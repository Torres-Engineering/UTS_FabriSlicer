from gcode_formats import texture_and_weld
import math
import re
from helpers.templates import *


class FabriSlicer:

    def __init__(self, fabrigui_instance):
        self.gui = fabrigui_instance
        self.template = textureAndWeld()

        self.foil_density = 2.7 #g/cm - default is alu
        self.tape_width_imp = 0.5
        self.rollback_imp = 0.01                       # x rollback 
        self.overlap_imp = 0.003                        # y overlap (on each weldline)
        self.foil_thickness_imp = 0.006
        self.dwelltime = 0.2                            #dwelltime at the beginning of each weld
        self.rollback = self._imp_to_mm(self.rollback_imp)
        self.tape_width = self._imp_to_mm(self.tape_width_imp)
        self.foil_thickness = self._imp_to_mm(self.foil_thickness_imp)

        self.A_feed_imp = 3.5
        self.x_extension_imp = 2.25
        self.tail_length_imp = 0.25
        self.A_feed = self._imp_to_mm(self.A_feed_imp)
        self.x_extension = self._imp_to_mm(self.x_extension_imp)
        self.tail_length = self._imp_to_mm(self.tail_length_imp)

        self.weld_speed_ipm = 0
        

    def _mm_to_imp(self, mm):
        return float(mm) / 25.4
    
    def _imp_to_mm(self,imp):
        return float(imp) * 25.4

    def _extract_mesh_geometry(self, mesh_dict):
        b = mesh_dict["live_bounds"]
        span_x_mm = abs(b["max_x"] - b["min_x"])
        span_y_mm = abs(b["max_y"] - b["min_y"])
        span_z_mm = abs(b["max_z"] - b["min_z"])
        print(b["max_z"], b["min_z"])
        print(span_z_mm)

        pitch_mm = 12.7 - (self.overlap_imp * 25.4)
        weldlines = (
            1
            if span_y_mm <= 12.7
            else math.ceil(1 + ((span_y_mm - 12.7) / pitch_mm))
        )
        layers = math.ceil(span_z_mm / (self.foil_thickness_imp * 25.4))
        
        vol_mm3 = span_x_mm * span_y_mm * span_z_mm
        net_weight_g = (vol_mm3 / 1000.0) * self.foil_density

        return {
            "name": mesh_dict["name"],
            "start_x": self._mm_to_imp(b["min_x"]),
            "end_x": self._mm_to_imp(b["max_x"]),
            "center_y": self._mm_to_imp((b["min_y"] + b["max_y"]) / 2.0),
            "print_x_mm": span_x_mm,
            "print_y_mm": span_y_mm,
            "weldlines": weldlines,
            "layers": layers,
            "net_weight_g": net_weight_g,
        }

    def _populate_init_template(
        self,
        tpl,
        geom,
        speed_ipm,
        work_offset,
        pause_l,
        pause_w,
    ):
        
        tpl.print_start_x = geom["start_x"]
        tpl.print_end_x = geom["end_x"]
        tpl.print_start_y = geom["center_y"]
        tpl.print_x_mm = geom["print_x_mm"]
        tpl.print_y_mm = geom["print_y_mm"]
        tpl.weld_speed = speed_ipm
        tpl.dwelltime = self.dwelltime
        tpl.rollback_imp = self.rollback_imp
        tpl.overlap_imp = self.overlap_imp
        tpl.foil_thickness_imp = self.foil_thickness_imp
        tpl.num_weldlines = geom["weldlines"]
        tpl.total_foil_mm =geom["total_foil_print"]
        tpl.total_weight_g =geom["total_weight_print"]
        tpl.est_time_min =geom["total_time_min"]    
        tpl.offset       =work_offset    
        tpl.pause_l = pause_l
        tpl.pause_w = pause_w   
        
        init = tpl.set_static_params()
        
        return init
    def gen_welding_gcode(self,print_geoms):
        gcode = self.template.set_speed(self.weld_speed_ipm)
       
        # Sort models from highest start_x to lowest, preserving original index for macro naming
        sorted_geoms = sorted(enumerate(print_geoms), key=lambda x: x[1]["start_x"])

        if len(print_geoms)>1:
            # sequential, layer-by-layer
            max_scene_layers = max(g["layers"] for g in print_geoms)
            current_layer_n = 0
            while current_layer_n < max_scene_layers:
                for p_idx, geom in sorted_geoms:
                    if current_layer_n < geom["layers"]:
                        gcode += (
                            f"\n\n( >>> Welding layer {current_layer_n+1} for: {geom['name']} <<< )\n"
                        )
                        macro = self._return_subroutine_names(p_idx, current_layer_n, "WELD")  
                        gcode += self.template.welding_gcode(
                            y_pos=geom["center_y"],
                            macro_id=macro,
                            n_layers=current_layer_n + 1,
                            n_weldlines=geom["weldlines"],
                            x_start=geom["start_x"],
                            x_end=geom["end_x"],
                            forced_layer_n=current_layer_n + 1
                        )
                current_layer_n += 1

        else:
            geom = print_geoms[0]
            gcode += (
                f"( >>> Welding: {geom['name']} <<< )\n"
            )
            macro = self._return_subroutine_names(0, "0", "WELD")
            gcode += self.template.welding_gcode(
                y_pos=geom["center_y"],
                macro_id=macro,
                n_layers=geom["layers"],
                n_weldlines=geom["weldlines"],
                x_start=geom["start_x"],
                x_end=geom["end_x"]
            )
        
        return gcode
            

    def _return_subroutine_names(
        self, part_idx, layer_idx, pass_type
    ):
        """creates dynamic macro denominations. from o1001 to 0<P1_L1_TEX_>01"""

        return f"P{part_idx}_L{layer_idx}_{pass_type}"


    def _calc_stats(self, geoms):
        model_stats = []
        for g in geoms:
            # foil/model
            total_foil_mm_per_weld = g["print_x_mm"]  + self.x_extension
            total_foil = total_foil_mm_per_weld * g["layers"] * g["weldlines"]

            # mass/model
            total_volume_per_print_mm3  = total_foil * self.foil_thickness * self.tape_width
            total_volume_per_print_cm3 = total_volume_per_print_mm3/1000
            total_weight = total_volume_per_print_cm3 * self.foil_density

            # print time/model
            total_weld_inches = self._mm_to_imp(g["print_x_mm"]) * g["weldlines"] * g["layers"]
            weld_motion_minutes = total_weld_inches / self.weld_speed_ipm
            weld_dwell_minutes = (self.dwelltime * 2.0 * g["weldlines"] * g["layers"]) / 60.0

            total_texture_inches = self._mm_to_imp(g["print_x_mm"]) * g["weldlines"] * 3
            texture_motion_minutes = total_texture_inches/self.texture_speed_ipm
            texture_dwell_minutes = (self.dwelltime * 2.0 * g["weldlines"] * 3) / 60.0

            total_motion_minutes = weld_motion_minutes + texture_motion_minutes
            total_dwell_minutes = weld_dwell_minutes + texture_dwell_minutes
            overhead_minutes = (5.0 * g["weldlines"] * g["layers"]) / 60.0 # ~5 sec indexing overhead per weld
            
            est_time_min = total_motion_minutes + total_dwell_minutes + overhead_minutes

            stats = {
                "name": g["name"],
                "total_foil_model": total_foil,
                "total_weight_model": total_weight,
                "est_time_min_model": est_time_min
            }

            model_stats.append(stats)
        # print(*(d for d in model_stats))
        total_foil_print = sum(m["total_foil_model"] for m in model_stats)
        total_weight_print = sum(m["total_weight_model"] for m in model_stats)
        total_time_min = sum(m["est_time_min_model"] for m in model_stats)
        total_net_weight = sum(g["net_weight_g"] for g in geoms)

        print_stats = {
                "total_foil_print": total_foil_print,
                "total_weight_print": total_weight_print,
                "total_time_min": total_time_min,
                "total_net_weight": total_net_weight,
                "total_waste_weight": total_weight_print - total_net_weight,
                "model_stats": model_stats
        }
        # print(*(val for val in print_stats.values()))
        return print_stats


        

    def generate_master_gcode(self):
        if not self.gui.meshes:
            return "(No models in build volume)", {}

        # 1. Pre-calculate all part bounding boxes once so we don't spam the CPU inside the loop
        part_geoms = [
            self._extract_mesh_geometry(m) for m in self.gui.meshes
        ]
        
        [print(g["name"],", ",g["layers"]) for g in part_geoms]

        work_offset = self.gui.work_offset_var.get()
        pause_l = 1 if self.gui.pause_after_layer_var.get() else 0
        pause_w = 1 if self.gui.pause_after_weld_var.get() else 0

        self.weld_speed_ipm = self.gui.print_speed_var.get()
        self.texture_speed_ipm = 70.0

        print_stats = self._calc_stats(part_geoms)
        
        for g in part_geoms:
            g|=print_stats 
            print(g)
            
        gcode_out = ""

        # -------------------------------------------------------------
        # STAGE 1: GLOBAL BED TEXTURING (Baseplate footprint pass)
        # -------------------------------------------------------------
        
        for p_idx, geom in enumerate(part_geoms):
            gcode_out += (
                f"( >>> Texturing footprint for: {geom['name']} <<< )\n"
            )
            
            gcode_out += self._populate_init_template(self.template,geom,self.weld_speed_ipm,work_offset,pause_l,pause_w)

            macro_id = self._return_subroutine_names(p_idx,0,"TEX")
            gcode_out += self.template.texturise_gcode(macro_id)
        
        
        

        

        # -------------------------------------------------------------
        # STAGE 2: TRUE CONTINUOUS LAYER-BY-LAYER WELDING
        # -------------------------------------------------------------
        # layer-by-layer printing
        # similar to above but figure out layer by layer lmao

        gcode_out+= self.gen_welding_gcode(part_geoms)

        
        # -------------------------------------------------------------
        # MASTER TEARDOWN
        # -------------------------------------------------------------
#         gcode_out += """(===================================================)
# (MASTER SCENE TEARDOWN)
# (===================================================)
# G30\t\t\t(RETRACT Z TO UNLOAD HEIGHT)
# M65 P2\t\t(COOLING OFF)
# M9\t\t\t(COOLANT NOZZLE OFF)
# G94\t\t\t(TURN OFF INVERSE TIME MOTION)
# M30\t\t\t(END PROGRAM)
# """
        return gcode_out, print_stats