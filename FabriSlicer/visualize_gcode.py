import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import tkinter as tk
from tkinter import filedialog
import re
import os
import numpy as np
import math
from helpers.helpers import *

class GCodeInterpreter:
    def __init__(self, lines):
        self.lines = [re.sub(r"\(.*?\)", "", line).strip() for line in lines]
        self.vars = {}
        self.pc = 0
        self.pos = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        self.is_incremental = False

        self.subs = {}  
        self.active_if_blocks = set()
        self.head_extended = False
        self.path = [(0, 0, 0, "travel")]

        self.sub_pattern = re.compile(r"(?i)o(?P<name>\S+)\s+SUB")
        self.call_pattern = re.compile(r"(?i)o(?P<name>\S+)\s+CALL")
        self.endsub_pattern = re.compile(r"(?i)o(?P<name>\S+)\s+ENDSUB")
        self.ctrl_pattern = re.compile(r"(?i)o(?P<name>\S+)\s+(?P<cmd>IF|ELSEIF|ELSE|ENDIF|WHILE|ENDWHILE)(?:\s+(?P<expr>\[.*\]))?")

    def _get_okey(self, match):
        return match.group("name").lower().replace("<", "").replace(">", "")

    def run(self):
        self.pre_scan()
        self.execute()

    def pre_scan(self):
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            match = self.sub_pattern.match(line)
            if match:
                sub_key = self._get_okey(match)
                self.subs[sub_key] = i
                while i < len(self.lines):
                    end_match = self.endsub_pattern.match(self.lines[i])
                    if end_match and self._get_okey(end_match) == sub_key:
                        break
                    i += 1
            i += 1

    def evaluate(self, expr):
        expr = expr.strip()
        if not expr:
            return 0.0

        def var_repl(m):
            vname = m.group(1).upper()
            return str(self.vars.get(vname, 0.0))

        expr = re.sub(r"(?i)(#<_[a-z0-9_]+>)", var_repl, expr)
        expr = expr.replace(" EQ ", " == ").replace(" NE ", " != ")
        expr = expr.replace(" GT ", " > ").replace(" GE ", " >= ")
        expr = expr.replace(" LT ", " < ").replace(" LE ", " <= ")
        expr = expr.replace(" AND ", " and ").replace(" OR ", " or ")
        expr = re.sub(r"(?i)\bABS\b", "abs", expr)
        expr = expr.replace("[", "(").replace("]", ")")

        try:
            env = {"__builtins__": None, "abs": abs}
            for func in [
                "sin", "cos", "tan", "asin", "acos", "atan", "sqrt", "exp", "log"
            ]:
                env[func] = getattr(math, func)

            val = eval(expr, env)
            return 1.0 if isinstance(val, bool) and val else float(val)
        except Exception:
            return 0.0

    def find_next_o_word(self, start_pc, o_key, targets):
        targets_str = "|".join(targets)
        pattern = re.compile(rf"(?i)o(?P<name>\S+)\s+(?P<cmd>{targets_str})\b")
        pc = start_pc
        while pc < len(self.lines):
            match = pattern.match(self.lines[pc])
            if match:
                name = self._get_okey(match)
                if name == o_key:
                    return pc
            pc += 1
        return pc

    def execute(self):
        call_stack = []
        while_stack = []
        self.active_if_blocks = set()

        while self.pc < len(self.lines):
            line = self.lines[self.pc]
            self.pc += 1
            if not line:
                continue

            sub_match = self.sub_pattern.match(line)
            if sub_match:
                sub_key = self._get_okey(sub_match)
                while self.pc < len(self.lines):
                    end_match = self.endsub_pattern.match(self.lines[self.pc])
                    if end_match and self._get_okey(end_match) == sub_key:
                        self.pc += 1
                        break
                    self.pc += 1
                continue

            if self.endsub_pattern.match(line) and call_stack:
                self.pc = call_stack.pop()
                continue

            call_match = self.call_pattern.match(line)
            if call_match:
                sub_key = self._get_okey(call_match)
                if sub_key in self.subs:
                    call_stack.append(self.pc)
                    self.pc = self.subs[sub_key] + 1
                continue

            ctrl_match = self.ctrl_pattern.match(line)
            if ctrl_match:
                o_key = self._get_okey(ctrl_match)
                cmd = ctrl_match.group("cmd").upper()
                expr = ctrl_match.group("expr") or ""

                if cmd == "IF":
                    val = self.evaluate(expr)
                    if val != 0.0:
                        self.active_if_blocks.add(o_key)
                    else:
                        self.active_if_blocks.discard(o_key)
                        self.pc = self.find_next_o_word(self.pc, o_key, ["ELSEIF", "ELSE", "ENDIF"])
                elif cmd == "ELSEIF":
                    if o_key in self.active_if_blocks:
                        self.pc = self.find_next_o_word(self.pc, o_key, ["ENDIF"])
                    else:
                        val = self.evaluate(expr)
                        if val != 0.0:
                            self.active_if_blocks.add(o_key)
                        else:
                            self.pc = self.find_next_o_word(self.pc, o_key, ["ELSEIF", "ELSE", "ENDIF"])
                elif cmd == "ELSE":
                    if o_key in self.active_if_blocks:
                        self.pc = self.find_next_o_word(self.pc, o_key, ["ENDIF"])
                    else:
                        self.active_if_blocks.add(o_key)
                elif cmd == "ENDIF":
                    self.active_if_blocks.discard(o_key)
                elif cmd == "WHILE":
                    val = self.evaluate(expr)
                    if val != 0.0:
                        if not any(k == o_key for k, p in while_stack):
                            while_stack.append((o_key, self.pc - 1))
                    else:
                        self.pc = self.find_next_o_word(self.pc, o_key, ["ENDWHILE"]) + 1
                        while_stack = [(k, p) for k, p in while_stack if k != o_key]
                elif cmd == "ENDWHILE":
                    for i in range(len(while_stack)-1, -1, -1):
                        if while_stack[i][0] == o_key:
                            self.pc = while_stack[i][1]
                            break
                continue

            var_match = re.match(r"(?i)(#<_[a-z0-9_]+\s*>)\s*=\s*(.*)", line)
            if var_match:
                vname = var_match.group(1).replace(" ", "").upper()
                vexpr = var_match.group(2)
                self.vars[vname] = self.evaluate(vexpr)
                continue

            upper_line = line.upper()
            if "G90" in upper_line:
                self.is_incremental = False
            if "G91" in upper_line:
                self.is_incremental = True

            if "M64 P0" in upper_line:
                self.head_extended = True
            if "M65 P0" in upper_line:
                self.head_extended = False

            is_move = False
            if bool(re.search(r"\bG0*[01]\b", upper_line)) or any(
                a in upper_line for a in ["X", "Y", "Z"]
            ):
                new_pos = self.pos.copy()
                for axis in ["X", "Y", "Z"]:
                    match = re.search(
                        rf"\b{axis}(\[.+?\]|-?[\d\.]+)", upper_line
                    )
                    if match:
                        val = self.evaluate(match.group(1))
                        if self.is_incremental:
                            new_pos[axis] += val
                        else:
                            new_pos[axis] = val
                        is_move = True

                if is_move:
                    is_low_z = self.pos["Z"] < 2.0 and new_pos["Z"] < 2.0
                    tape_enabled = self.vars.get("#<_TAPEENABLE>", 1.0) > 0.0

                    if not is_low_z:
                        move_type = "travel"
                    elif not self.head_extended:
                        move_type = "tape_ext"
                    elif tape_enabled:
                        move_type = "weld"
                    else:
                        move_type = "texture"

                    self.pos = new_pos
                    self.path.append(
                        (self.pos["X"], self.pos["Y"], self.pos["Z"], move_type)
                    )
                    # print(f"Movement: X={self.pos['X']:.4f}, Y={self.pos['Y']:.4f}, Z={self.pos['Z']:.4f} | Type: {move_type}")

    def render_on_axes(self, ax):
        if len(self.path) <= 1:
            # print("Warning: No movement commands were found or executed.")
            return [], [], {}, 0

        # Subtract spindle offsets to plot the true printhead coordinates
        x_offset = self.vars.get('#<_WELDERXOFFSET>', -6.230)
        y_offset = self.vars.get('#<_WELDERYOFFSET>', 0.0)
        
        # We process a copy so we don't destructively modify self.path
        metric_path = [(imp_to_metric(x - x_offset), imp_to_metric(y - y_offset), imp_to_metric(z), m) for x, y, z, m in self.path]
        tape_width = imp_to_metric(self.vars.get('#<_TAPEWIDTH>', 0.5))
        
        weld_z_values = sorted(list(set(round(p[2], 4) for p in metric_path if p[3] in ['weld', 'texture', 'tape_ext'])))
        if not weld_z_values:
            weld_z_values = [0.0]

        lines_to_plot = []
        if len(metric_path) > 1:
            current_line = [metric_path[0][:3]]
            current_move_type = metric_path[1][3]
            for p in metric_path[1:]:
                x, y, z, move_type = p
                if move_type == current_move_type:
                    current_line.append((x, y, z))
                else:
                    lines_to_plot.append((current_line, current_move_type))
                    current_line = [current_line[-1], (x, y, z)]
                    current_move_type = move_type
            lines_to_plot.append((current_line, current_move_type))

        rendered_elements = []  
        global_move_idx = 0
        time_to_layer_map = {}

        for line_pts, move_type in lines_to_plot:
            if len(line_pts) < 2: continue
            
            group_idx = global_move_idx 
            
            move_z_val = max(p[2] for p in line_pts) if move_type != 'travel' else min(p[2] for p in line_pts)
            rounded_z = round(move_z_val, 4)
            z_layer_index = weld_z_values.index(rounded_z) + 1 if rounded_z in weld_z_values else 1
            time_to_layer_map[group_idx] = z_layer_index
            
            if move_type == 'weld':
                z_ref = max(p[2] for p in line_pts) 
                verts = []
                for i in range(len(line_pts)-1):
                    x1, y1, z1 = line_pts[i]
                    x2, y2, z2 = line_pts[i+1]
                    dx, dy = x2 - x1, y2 - y1
                    length = math.hypot(dx, dy)
                    if length < 1e-4: continue 
                    nx, ny = -dy / length, dx / length
                    w = tape_width / 2.0
                    p1L = (x1 + nx * w, y1 + ny * w, z1)
                    p2L = (x2 + nx * w, y2 + ny * w, z2)
                    p2R = (x2 - nx * w, y2 - ny * w, z2)
                    p1R = (x1 - nx * w, y1 - ny * w, z1)
                    verts.append([p1L, p2L, p2R, p1R])
                if verts:
                    poly = Poly3DCollection(verts, facecolors='blue', edgecolors='navy', alpha=0.6, linewidths=0.5)
                    ax.add_collection3d(poly)
                    rendered_elements.append((z_ref, group_idx, poly))
                    
            elif move_type == 'texture':
                z_ref = max(p[2] for p in line_pts) 
                verts = []
                for i in range(len(line_pts)-1):
                    x1, y1, z1 = line_pts[i]
                    x2, y2, z2 = line_pts[i+1]
                    dx, dy = x2 - x1, y2 - y1
                    length = math.hypot(dx, dy)
                    if length < 1e-4: continue 
                    nx, ny = -dy / length, dx / length
                    w = tape_width / 2.0
                    p1L = (x1 + nx * w, y1 + ny * w, z1)
                    p2L = (x2 + nx * w, y2 + ny * w, z2)
                    p2R = (x2 - nx * w, y2 - ny * w, z2)
                    p1R = (x1 - nx * w, y1 - ny * w, z1)
                    verts.append([p1L, p2L, p2R, p1R])
                if verts:
                    poly = Poly3DCollection(verts, facecolors='orange', edgecolors='darkorange', alpha=0.6, linewidths=0.5)
                    ax.add_collection3d(poly)
                    rendered_elements.append((z_ref, group_idx, poly))
                
            elif move_type == 'tape_ext':
                z_ref = max(p[2] for p in line_pts)
                xs, ys, zs = zip(*line_pts)
                line, = ax.plot(xs, ys, zs, color='magenta', linestyle='-.', linewidth=1.5)
                rendered_elements.append((z_ref, group_idx, line if not isinstance(line, list) else line[0]))
                
            else: # travel
                z_ref = min(p[2] for p in line_pts)
                xs, ys, zs = zip(*line_pts)
                line, = ax.plot(xs, ys, zs, color='grey', linestyle='--', linewidth=1.0, alpha=0.5)
                rendered_elements.append((z_ref, group_idx, line if not isinstance(line, list) else line[0]))

            global_move_idx += 1

        legend_elements = [
            Patch(facecolor='blue', edgecolor='navy', alpha=0.6, label='Tape Weld'),
            Patch(facecolor='orange', edgecolor='darkorange', alpha=0.6, label='Surface Texturing'),
            Line2D([0], [0], color='magenta', lw=1.5, linestyle='-.', label='Tape Clear'),
            Line2D([0], [0], color='grey', lw=1, linestyle='--', alpha=0.5, label='Travel')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # --- DRAW WELD BOUNDING BOX ---
        weld_pts = [p for p in metric_path if p[3] in ['weld', 'texture']]
        if weld_pts:
            min_wx = min(p[0] for p in weld_pts)
            max_wx = max(p[0] for p in weld_pts)
            min_wy = min(p[1] for p in weld_pts) - (tape_width / 2.0)
            max_wy = max(p[1] for p in weld_pts) + (tape_width / 2.0)
            min_wz = min(p[2] for p in weld_pts)
            max_wz = max(p[2] for p in weld_pts)

            box_color = 'red'
            box_alpha = 0.5
            box_lines = 'dotted'

            ax.plot([min_wx, max_wx, max_wx, min_wx, min_wx],
                    [min_wy, min_wy, max_wy, max_wy, min_wy],
                    [min_wz, min_wz, min_wz, min_wz, min_wz], color=box_color, linestyle=box_lines, alpha=box_alpha)
            ax.plot([min_wx, max_wx, max_wx, min_wx, min_wx],
                    [min_wy, min_wy, max_wy, max_wy, min_wy],
                    [max_wz, max_wz, max_wz, max_wz, max_wz], color=box_color, linestyle=box_lines, alpha=box_alpha)
            for bx in [min_wx, max_wx]:
                for by in [min_wy, max_wy]:
                    ax.plot([bx, bx], [by, by], [min_wz, max_wz], color=box_color, linestyle=box_lines, alpha=box_alpha)
            
            box_dx = max_wx - min_wx
            box_dy = max_wy - min_wy
            box_dz = max_wz - min_wz
            # info_text = f"Part Dimensions:\nX: {box_dx:.2f} mm\nY: {box_dy:.2f} mm\nZ: {box_dz:.2f} mm"
            # ax.text2D(0.02, 0.95, info_text, transform=ax.transAxes, 
            #           fontsize=11, verticalalignment='top',
            #           bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.5'))
                      
        try:
            ax.set_xlim(-127, 127)
            ax.set_ylim(-127, 127)
            ax.set_zlim(0, 254)
            try:
                ax.set_box_aspect((1, 1, 1))
            except AttributeError:
                pass
        except Exception:
            pass
            
        return rendered_elements, weld_z_values, time_to_layer_map, global_move_idx

def visualize_gcode_3d(filepath = None, data = None):
   
    if filepath != None and data == None:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    elif filepath == None and data != None:
        lines = data
    else:
        raise ValueError("No file or data found. wtf?")

    # print("Simulating...")
    sim = GCodeInterpreter(lines)
    sim.run()
    
    if len(sim.path) <= 1:
        # print("Warning: No movement commands were found or executed.")
        return
        
    fig = plt.figure(figsize=(12, 10))
    plt.subplots_adjust(bottom=0.25) 
    ax = fig.add_subplot(111, projection='3d')
    
    rendered_elements, weld_z_values, time_to_layer_map, global_move_idx = sim.render_on_axes(ax)
    # print(f"Simulation complete. Found {len(weld_z_values)} active layers.")
        
    def on_scroll(event):
        if event.inaxes != ax: return
        zoom_factor = 1.15
        scale = 1 / zoom_factor if event.button == 'up' else zoom_factor

        xlim, ylim, zlim = ax.get_xlim(), ax.get_ylim(), ax.get_zlim()
        xc = (xlim[0] + xlim[1]) * 0.5
        yc = (ylim[0] + ylim[1]) * 0.5
        zc = (zlim[0] + zlim[1]) * 0.5

        xr = (xlim[1] - xlim[0]) * 0.5 * scale
        yr = (ylim[1] - ylim[0]) * 0.5 * scale
        zr = (zlim[1] - zlim[0]) * 0.5 * scale

        ax.set_xlim([xc - xr, xc + xr])
        ax.set_ylim([yc - yr, yc + yr])
        ax.set_zlim([zc - zr, zc + zr])
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect('scroll_event', on_scroll)

    ax_layer_slider = plt.axes([0.15, 0.1, 0.7, 0.03])
    ax_move_slider = plt.axes([0.15, 0.05, 0.7, 0.03])

    layer_slider = Slider(ax_layer_slider, 'Z Layer', 1, max(1, len(weld_z_values)), valinit=max(1, len(weld_z_values)), valstep=1)
    move_slider = Slider(ax_move_slider, 'Time/Move', 0, global_move_idx, valinit=global_move_idx, valstep=1)
    
    is_updating = [False]

    def manual_visibility_draw():
        max_idx = int(layer_slider.val) - 1
        if max_idx >= len(weld_z_values): max_idx = len(weld_z_values)-1
        current_max_z = weld_z_values[max_idx]
        current_max_move = int(move_slider.val)
        
        for z, m_idx, element in rendered_elements:
            visible = (z <= current_max_z + 1e-4) and (m_idx <= current_max_move)
            if hasattr(element, 'set_visible'):
                element.set_visible(visible)
        fig.canvas.draw_idle()

    def update_from_layer(val):
        if is_updating[0]: return
        is_updating[0] = True
        move_slider.set_val(global_move_idx)
        manual_visibility_draw()
        is_updating[0] = False

    def update_from_move(val):
        if is_updating[0]: return
        is_updating[0] = True
        val_idx = int(val)
        if val_idx in time_to_layer_map:
            layer_slider.set_val(time_to_layer_map[val_idx])
        manual_visibility_draw()
        is_updating[0] = False

    layer_slider.on_changed(update_from_layer)
    move_slider.on_changed(update_from_move)

    plt.show()

def main():
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename(
        title="Select a G-code file",
        filetypes=(("NC files", "*.nc"), ("Text files", "*.txt"), ("All files", "*.*"))
    )
    if filepath:
        visualize_gcode_3d(filepath)

if __name__ == "__main__":
    main()
