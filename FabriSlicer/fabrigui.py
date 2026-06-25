import os
import numpy as np
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
from tkinter import *
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import MultipleLocator, NullFormatter, NullLocator
from mpl_toolkits.mplot3d import art3d
from stl import mesh
from fabrislicer import FabriSlicer
from visualize_gcode import GCodeInterpreter 

class AutoScrollbar(ttk.Scrollbar):
    # scrollbar with auto-hide functionality
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_place_geometry = None

    def place(self, **kwargs):
        # geometry arguments on line 1 and save them
        self._saved_place_geometry = kwargs
        super().place(**kwargs)
    
    place_configure = place #restore overwritten configure alias

    def set(self, low, high):
        if float(low) <= 0.0 and float(high) >= 1.0:
            self.place_forget()
        else:
            if self._saved_place_geometry:
                super().place(**self._saved_place_geometry)
        super().set(low, high)


class FabriGui(tk.Tk):

    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title("UTS FabriSlicer")
        self.geometry('900x600') #600*400
        self.resizable(True,True)
        self._window_width = 900
        self._window_height = 600
        self.minsize(900,600)
        self._last_geom = (self._window_width, self._window_width)
        self._resize_job = None
        
        self.update()
        

        # stl/viewport stuff
        self.meshes = [] 
        self._ui_block = False
        self.fig = plt.figure()
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        self.fig.set_facecolor("lightblue")
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.bed_size = 254
        self.setup_build_volume()

        # setup gui frames, widgets and menubar
        self.set_widths_and_heights()
        self.create_frames()
        self.create_widgets()
        self.create_menubar()
        # self.state('zoomed') 
        self.configure(bg="#F0F0F0")
        self.update_idletasks()
        self.deiconify()

        # safe shutdown procedure kills matplot and tkinter together
        self.protocol("WM_DELETE_WINDOW", self.safe_shutdown)
        
        # gcode generation variables
        self.compile_gcode_flag = False
        self.x_start = None
        self.gcode = " "
        self.gcode_stats = []


        
    
    
    def create_menubar(self):
        self.menu = tk.Menu(self)

        # file
        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Create GCODE Using Dimensions...", command=self.custom_model)
        file_menu.add_command(label="Import Stl..", command=self.load_stl)
        file_menu.add_command(label="Preview Gcode File..", command=self.preview_gcode)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.safe_shutdown)

        edit_menu = tk.Menu(self.menu, tearoff=0)
        edit_menu.add_command(label="Default View", command=lambda: self.set_view("default"))
        edit_menu.add_command(label="Top View", command=lambda: self.set_view("top"))
        edit_menu.add_command(label="Front View", command=lambda: self.set_view("front"))
        edit_menu.add_command(label="Side View", command=lambda: self.set_view("side"))


        # attach to menubar, and add menubar to config
        self.menu.add_cascade(label="File", menu=file_menu)
        self.menu.add_cascade(label="View", menu=edit_menu)
        self.config(menu=self.menu)
    
    
    def set_widths_and_heights(self):

        # self._window_width = 750 now 900
        # self._window_height = 500 now 600
        # left frames
        self._left_frame_w = 280
        self._left_frame_h = self._window_height #600
        self._model_frame_w = self._left_frame_w - 20
        self._model_frame_h = self._left_frame_h - 385  # 215 
        self._settings_frame_w = self._model_frame_w
        self._settings_frame_h = self._left_frame_h - self._model_frame_h -20 #270

        # right frames
        self._right_frame_w = self._window_width - self._left_frame_w #350
        self._right_frame_h = self._window_height #500
        self._viewport_frame_w = self._right_frame_w - 20 #330
        self._viewport_frame_h = self._right_frame_h - 20#480



        # left widgets
        self._model_list_fh = self._model_frame_h - 160 #55
        self._model_list_fw = self._model_frame_w - 15 #215
        self._imp_stl_bw = self._model_list_fw - 125
        self._further_set_bw = self._model_list_fw
        self._create_model_bw = self._model_list_fw - self._imp_stl_bw - 10


    def create_frames(self):
        # 1. Master Left Frame
        self.left_frame = Frame(self, width=self._left_frame_w, height=self._left_frame_h, bg="#F0F0F0")
        self.left_frame.place(y=0)

        # ==========================================
        # BOX A: MODEL PREP MODE 
        # ==========================================
        self.prep_container = Frame(self.left_frame, bg="#F0F0F0")
        self.prep_container.place(x=0, y=0, relwidth=1, relheight=1)

        self.model_labelframe = ttk.LabelFrame(self.prep_container, width=self._model_frame_w, height=self._model_frame_h, text="Model", relief="groove")
        self.settings_labelframe = ttk.LabelFrame(self.prep_container, width=self._settings_frame_w, height=self._settings_frame_h, text='GCODE Settings')

        self.prep_container.place(x=10, y=0)
        self.settings_labelframe.place(x=10, y=120)
        
         #right
        self.right_frame = Frame(self, bg="#F0F0F0",width=self._right_frame_w, height=self._right_frame_h)
        self.right_frame.place(x=self._left_frame_w,y=0)
        
        self.viewport_frame = Frame(self.right_frame,width=self._viewport_frame_w,height=self._viewport_frame_h, bg="lightblue",borderwidth=1,relief="sunken")
        self.viewport_frame.place(x=10,y=10)

        # ==========================================
        # BOX B: GCODE PREVIEW MODE (Hidden at start)
        # ==========================================
        self.preview_container = Frame(self.left_frame, bg="#F0F0F0")
        
        self.preview_actions_frame = ttk.LabelFrame(self.preview_container, text="Preview Mode", relief="groove")
        self.preview_actions_frame.place(x=10, y=10, width=self._model_frame_w, height=220)

        self.save_gcode_btn = ttk.Button(self.preview_actions_frame, text="Save GCODE to Disk...", command=self.save_gcode_to_disk)
        self.exit_preview_btn = ttk.Button(self.preview_actions_frame, text="← Exit Preview Mode", command=self.exit_preview_mode)

        self.save_gcode_btn.place(x=10, y=15, width=self._model_frame_w - 25, height=35)
        self.exit_preview_btn.place(x=10, y=60, width=self._model_frame_w - 25, height=35)

        self.layer_var = tk.IntVar(value=1)
        self.move_var = tk.IntVar(value=0)

        
        
        self.is_updating_scrubbers = False

        self.stats_frame = ttk.LabelFrame(self.preview_container, text="Total Print Stats", relief="groove")
        self.stats_frame.place(x=10, y=240, width=self._model_frame_w, height=160)
        self.layer_lbl = ttk.Label(self.preview_actions_frame, text="Z Layer:")
        

       

    
    def create_widgets(self):
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viewport_frame)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        
        # Override mplot3d default buttons to map Right-Click to Pan (btn 3) and Middle-Click to Zoom (btn 2)
        try:
            self.ax.mouse_init(rotate_btn=1, zoom_btn=2, pan_btn=3)
        except TypeError:
            pass # older matplotlib versions might not support button overrides
            
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.view_tools_frame = Frame(self.viewport_frame, bg="#F0F0F0")
        self.view_lbl = ttk.Label(self.view_tools_frame,text="Change\nView:",justify="center")
        self.btn_view_def = ttk.Button(self.view_tools_frame, text="Default", width=8, command=lambda: self.set_view("default"))
        self.btn_view_top = ttk.Button(self.view_tools_frame, text="Top", width=8, command=lambda: self.set_view("top"))
        self.btn_view_front = ttk.Button(self.view_tools_frame, text="Front", width=8, command=lambda: self.set_view("front"))
        self.btn_view_side = ttk.Button(self.view_tools_frame, text="Side", width=8, command=lambda: self.set_view("side"))

        # lhs
        
        self.model_list = tk.Listbox(self.prep_container, bg="white",font=('Arial',9),exportselection=False)
        self.model_scroll = AutoScrollbar(self.prep_container, orient="vertical", command=self.model_list.yview)
        self.model_list.config(yscrollcommand=self.model_scroll.set)
        self.model_list.bind("<Delete>", self._delete_selected_item)
        self.model_list.bind("<<ListboxSelect>>", self.on_mesh_select)

        self.import_stl_button = ttk.Button(self.prep_container, text= "Import STL", command=self.load_stl)
        self.create_stl_button = ttk.Button(self.prep_container, text= "  Create Model\nUsing Dimensions", command=self.custom_model)
        self.model_dims_label = ttk.Label(self.prep_container, text="Dimensions: ", font=('Arial',9,'bold'))
        
        #make all spinbar widgets at once because im sick of scrolling for 30s every time i need to make a change
        self.default_work_offset = 12
        self.default_print_speed = 60.0

        base_opts = {'increment': 0.05, 'wrap': True, 'format': "%.3f", 'width': 8}
        
        spinbox_widget_data = {
            "x_width":     (self.prep_container,    tk.DoubleVar(value=0.0),                     "X (mm): ",                      {'from_': 0.0,    'to': 254.0}),
            "y_width":     (self.prep_container,    tk.DoubleVar(value=0.0),                     "Y (mm): ",                      {'from_': 0.0,    'to': 254.0}),
            "z_width":     (self.prep_container,    tk.DoubleVar(value=0.0),                     "Z (mm): ",                      {'from_': 0.0,    'to': 254.0}),
            
            "x_scale":     (self.prep_container,    tk.DoubleVar(value=100),                     "Scale %: ",                     {'from_': -1000.0,'to': 1000.0, 'increment':1, 'format':"%.2f"}), 
            "y_scale":     (self.prep_container,    tk.DoubleVar(value=100),                     "Scale %: ",                     {'from_': -1000.0,'to': 1000.0, 'increment':1, 'format':"%.2f"}), 
            "z_scale":     (self.prep_container,    tk.DoubleVar(value=100),                     "Scale %: ",                     {'from_': -1000.0,'to': 1000.0, 'increment':1, 'format':"%.2f"}), 
            
            "x_pos":     (self.prep_container, tk.DoubleVar(value=0.0),                       "X Offset (mm): ",      {'from_': -127.0, 'to': 127.0}),
            "y_pos":     (self.prep_container, tk.DoubleVar(value=0.0),                       "Y Offset (mm): ",      {'from_': -127.0, 'to': 127.0}),
            "z_pos":     (self.prep_container, tk.DoubleVar(value=0.0),                       "Z Offset (mm): ",      {'from_': -1.0,    'to': 254.0}),
            
            "work_offset": (self.prep_container, tk.IntVar(value=self.default_work_offset),   "Work offset: ",                 {'from_': 0,      'to': 999,   'increment': 1, 'format': "%.0f"}),
            "print_speed": (self.prep_container, tk.DoubleVar(value=self.default_print_speed),"Print speed (mm/s): ",          {'from_': 0.0,    'to': 150.0})
        }

        for name, (frame, var, label_text, custom_opts) in spinbox_widget_data.items():
            merged_opts = {**base_opts, **custom_opts} 

            lbl = ttk.Label(frame, text=label_text, font=('Arial', 9))
            spn = ttk.Spinbox(frame, textvariable=var, **merged_opts)

            setattr(self, f"{name}_var", var)
            setattr(self, f"{name}_label", lbl)
            setattr(self, f"{name}_spinval", spn)


        self.x_width_var.trace_add("write", lambda *a: self.reconcile_dimensions('width', 'x'))
        self.y_width_var.trace_add("write", lambda *a: self.reconcile_dimensions('width', 'y'))
        self.z_width_var.trace_add("write", lambda *a: self.reconcile_dimensions('width', 'z'))
        self.x_scale_var.trace_add("write", lambda *a: self.reconcile_dimensions('scale', 'x'))
        self.y_scale_var.trace_add("write", lambda *a: self.reconcile_dimensions('scale', 'y'))
        self.z_scale_var.trace_add("write", lambda *a: self.reconcile_dimensions('scale', 'z'))
        self.x_pos_var.trace_add("write", self.transform_mesh)
        self.y_pos_var.trace_add("write", self.transform_mesh)
        self.z_pos_var.trace_add("write", self.transform_mesh)
        

        self.centre_print_button = ttk.Button(self.prep_container, text="Centre Selected Model", command=self.centre_print)
        self.auto_arrange_button = ttk.Button(self.prep_container, text="Auto-Arrange Models", command=self.auto_arrange)

        self.pause_after_layer_var = tk.BooleanVar(value=False)
        self.pause_after_weld_var = tk.BooleanVar(value=False)

        self.layer_pause = ttk.Checkbutton(self.prep_container, text= "Pause after each layer?", variable=self.pause_after_layer_var)
        self.weld_pause = ttk.Checkbutton(self.prep_container, text= "Pause after each weld?", variable=self.pause_after_weld_var)

        self.further_settings_button = ttk.Button(self.prep_container, text="Further Settings..")
        self.gen_code_button = ttk.Button(self.prep_container, text="Generate GCODE", command=self.preview_gcode)
        

        # gcode viz scrubbers
        self.layer_spin = ttk.Spinbox(self.preview_actions_frame, from_=1, to=1, textvariable=self.layer_var, width=5, command=lambda: self.on_layer_scrub(self.layer_var.get()))
        self.layer_spin.bind('<Return>', lambda e: self.on_layer_scrub(self.layer_var.get()))
        self.layer_scale = tk.Scale(self.preview_actions_frame, from_=1, to=1, orient=tk.HORIZONTAL, command=self.on_layer_scrub, showvalue=0, sliderlength=15, resolution=1, variable=self.layer_var)
        
        
        self.move_lbl = ttk.Label(self.preview_actions_frame, text="Time/Move:")
        self.move_spin = ttk.Spinbox(self.preview_actions_frame, from_=0, to=0, textvariable=self.move_var, width=7, command=lambda: self.on_move_scrub(self.move_var.get()))
        self.move_spin.bind('<Return>', lambda e: self.on_move_scrub(self.move_var.get()))
        self.move_scale = tk.Scale(self.preview_actions_frame, from_=0, to=0, orient=tk.HORIZONTAL, command=self.on_move_scrub, showvalue=0, sliderlength=15, resolution=1, variable=self.move_var)
        
        # stats
        self.foil_stat_lbl = ttk.Label(self.stats_frame, text="Total Foil: 0.00 m")
        self.weight_stat_lbl = ttk.Label(self.stats_frame, text="Total Tape Weight: 0.00 g")
        self.net_weight_lbl = ttk.Label(self.stats_frame, text="Net Part Weight: 0.00 g")
        self.waste_weight_lbl = ttk.Label(self.stats_frame, text="Waste: 0.00 g (0.00%)")
        self.time_stat_lbl = ttk.Label(self.stats_frame, text="Estimated Time: 0 min")
        

        self.set_widget_coords()

    def set_widget_coords(self):
        
        self.right_frame.place_configure(width= self._right_frame_w, height=self._right_frame_h)
        self.viewport_frame.place_configure(width=self._viewport_frame_w, height=self._viewport_frame_h)
        
        self.view_tools_frame.place_configure(relx=1.0, rely=0.0, anchor="ne", x=1, y=-1, width=64, height=self._viewport_frame_h+2)
        self.btn_view_ycoord = 45
        self.view_lbl.place_configure(x=10,y=self.btn_view_ycoord-40)
        self.btn_view_def.place_configure(x=4, y=self.btn_view_ycoord, width=60, height=24)
        self.btn_view_top.place_configure(x=4, y=self.btn_view_ycoord+26, width=60, height=24)
        self.btn_view_front.place_configure(x=4, y=self.btn_view_ycoord+52, width=60, height=24)
        self.btn_view_side.place_configure(x=4, y=self.btn_view_ycoord+78, width=60, height=24)

        self.left_frame.place_configure(height=self._left_frame_h)
        self.prep_container.place_configure(height=self._model_frame_h)
        self.settings_labelframe.place_configure(height=self._settings_frame_h, y=self._model_frame_h+10)

        self.model_list.place_configure(in_=self.prep_container, width=self._model_list_fw,height=self._model_list_fh,x=5,y=5)
        self.model_scroll.place_configure(in_=self.model_list, x=self._model_list_fw - 25,y=0, height=self._model_list_fh-4)
        self.import_stl_button.place_configure(in_=self.prep_container,x=5, y=self._model_list_fh+10, width=self._imp_stl_bw)
        self.create_stl_button.place_configure(in_=self.prep_container,x=self._model_frame_w-self._create_model_bw-10, y=self._model_list_fh+10, width=self._create_model_bw)

        self.model_dims_label.place_configure(in_=self.prep_container, x=5,y=self._model_list_fh+40)
        self.x_scale_label.place(in_=self.prep_container, x=5, y=self._model_list_fh+60, height=23)
        self.y_scale_label.place(in_=self.prep_container, x=5, y=self._model_list_fh+85,height=23)
        self.z_scale_label.place(in_=self.prep_container, x=5, y=self._model_list_fh+110,height=23)
        self.x_scale_spinval.place(in_=self.prep_container, x=60,width=60, y=self._model_list_fh+60)
        self.y_scale_spinval.place(in_=self.prep_container, x=60,width=60, y=self._model_list_fh+85)
        self.z_scale_spinval.place(in_=self.prep_container, x=60,width=60, y=self._model_list_fh+110)

        self.x_width_label.place_configure(in_=self.prep_container, x=130, y=self._model_list_fh+60)
        self.y_width_label.place_configure(in_=self.prep_container, x=130, y=self._model_list_fh+85)
        self.z_width_label.place_configure(in_=self.prep_container, x=130, y=self._model_list_fh+110)
        self.x_width_spinval.place_configure(in_=self.prep_container, x=184, y=self._model_list_fh+60)
        self.y_width_spinval.place_configure(in_=self.prep_container, x=184, y=self._model_list_fh+85)
        self.z_width_spinval.place_configure(in_=self.prep_container, x=184, y=self._model_list_fh+110)
        
        # bottom-left
        self.x_pos_label.place_configure(in_=self.settings_labelframe, x=50, y=15)
        self.y_pos_label.place_configure(in_=self.settings_labelframe, x=50, y=40)
        self.z_pos_label.place_configure(in_=self.settings_labelframe, x=50, y=65)
        self.x_pos_spinval.place_configure(in_=self.settings_labelframe, x=140, y=15)
        self.y_pos_spinval.place_configure(in_=self.settings_labelframe, x=140, y=40)
        self.z_pos_spinval.place_configure(in_=self.settings_labelframe, x=140, y=65)
        self.centre_print_button.place_configure(in_=self.settings_labelframe, x=5, y=100, width = self._further_set_bw, height = 30 )
        self.auto_arrange_button.place_configure(in_=self.settings_labelframe, x=5, y=135, width = self._further_set_bw, height = 30 )

        self.work_offset_label.place_configure(in_=self.settings_labelframe, x=64, y=175)
        self.print_speed_label.place_configure(in_=self.settings_labelframe, x=18, y=200, height= 23)
        self.work_offset_spinval.place_configure(in_=self.settings_labelframe, x=140, y=175)
        self.print_speed_spinval.place_configure(in_=self.settings_labelframe, x=140, y=200)
        
        self.weld_pause.place_configure(in_=self.settings_labelframe,x=41,y=230)
        self.layer_pause.place_configure(in_=self.settings_labelframe,x=41,y=253)

        self.further_settings_button.place_configure(in_=self.settings_labelframe, x=5, y=285, width = self._further_set_bw )
        self.gen_code_button.place_configure(in_=self.settings_labelframe, x=5, y=310, width = self._further_set_bw, height=30)
        
        self.layer_lbl.place(x=10, y=105)
        self.layer_spin.place(x=70, y=103)
        self.layer_scale.place(x=10, y=125, width=self._model_frame_w - 25)
        self.move_lbl.place(x=10, y=155)
        self.move_scale.place(x=10, y=175, width=self._model_frame_w - 25)
        self.move_spin.place(x=80, y=153)
        self.foil_stat_lbl.place(x=10, y=10)
        self.weight_stat_lbl.place(x=10, y=35)
        self.net_weight_lbl.place(x=10, y=60)
        self.waste_weight_lbl.place(x=10, y=85)
        self.time_stat_lbl.place(x=10, y=110)


    def setup_build_volume(self):
        self.ax.clear()
        self.ax.set_facecolor('none')
        self.ax.set_xlim([-127, 127])
        self.ax.set_ylim([-127, 127])
        self.ax.set_zlim([0, 254])        
        self.ax.set_axis_off()
        self.ax.set_box_aspect((1, 1, 1))
        

        # tick params
        self.minorspacing = 5.08
        self.majorspacing = 25.4
        #create grid on base of buildvolume
        ruler_xy = np.arange(-127, 128, self.minorspacing)
       
        major_segments = []
        minor_segments = []


        for coord in ruler_xy:

            if coord % self.majorspacing > 25:
                # Major tick
                major_segments.append([(coord, -127.0, 0.0), (coord, 127.0, 0.0)]) # x
                major_segments.append([(-127.0, coord, 0.0), (127.0, coord,  0.0)]) # y
            else:
                # Minor tick
                minor_segments.append([(coord, -127.0, 0.0), (coord, 127, 0.0)]) # x 
                minor_segments.append([(-127.0, coord,  0.0), (127, coord,  0.0)]) # y
            
        major_collection = art3d.Line3DCollection(
            major_segments, 
            colors="#3A3A3A", 
            linewidths=1,
            alpha=0.85
        )
        minor_collection = art3d.Line3DCollection(
            minor_segments, 
            colors="#313131", 
            linewidths=0.5,
            alpha=0.7
        )

        # colored base of bv
        bv_baseverts = np.array([
            [-127,  -127,   0],
            [-127,  127,    0],
            [127,   127,    0],
            [127,   -127,   0]
        ])
        bv_base = art3d.Poly3DCollection([bv_baseverts], facecolors="#6b6b6b50")

        # add bv box        
        bv_topverts = np.array(
            [
            [-127,  -127,   254],
            [-127,  127,    254],
            [127,   127,    254],
            [127,   -127,   254],
            [-127,  -127,   254],
            ])
        
        bv_segs = []
        # top
        top_poss = bv_topverts[:-1]
        top_ends = bv_topverts[1:]
        for segstart,segend in zip(top_poss,top_ends):
            segment = ([tuple(int(x) for x in segstart),tuple(int(x) for x in segend)])
            bv_segs.append(segment)

        # sides
        for segstart, segend in zip(bv_topverts,bv_baseverts):
            segment = ([tuple(int(x) for x in segstart),tuple(int(x) for x in segend)])
            bv_segs.append(segment)

        bv_edges= art3d.Line3DCollection(
            bv_segs, 
            colors="#716F6FB7", 
            linewidths=0.5,
        )

        #origin
        n = 3
        length_vec = np.array([0,35])
        zero_vec = np.array([0,0])
        originvecs = np.full((n, n), fill_value=None, dtype=object)
        for i in range(n):
            for j in range(n):
                originvecs[i, j] = length_vec if i == j else zero_vec
       
        colours = [
            "#ff0000",
            "#00ff00",
            "#0000ff",
        ]

        origins = np.column_stack((originvecs,colours))

        for r,row, in enumerate(origins):
            # print(row[0],row[1],row[2],row[3])
            self.ax.plot(row[0],row[1],row[2],color=row[3],linewidth=2)

        # self.origin = np.array([0,35])
        # self.otherplane = np.array([0,0])
        # self.ax.plot(self.otherplane,  self.origin,        self.otherplane,    color="red",        linewidth=2)
        # self.ax.plot(self.origin,       self.otherplane,   self.otherplane,    color="#00ff0d", linewidth=2)
        # self.ax.plot(self.otherplane,  self.otherplane,   self.origin/2,         color="blue",       linewidth=2)

        self.ax.add_collection3d(major_collection)
        self.ax.add_collection3d(minor_collection)
        self.ax.add_collection3d(bv_edges)
        self.ax.add_collection3d(bv_base)

    def on_scroll(self, event):
        if event.inaxes != self.ax: return
        base_scale = 1.1
        scale = base_scale if event.button == 'up' else 1 / base_scale
        
        self.ax.set_xlim([self.ax.get_xlim()[0]*scale, self.ax.get_xlim()[1]*scale])
        self.ax.set_ylim([self.ax.get_ylim()[0]*scale, self.ax.get_ylim()[1]*scale])
        self.ax.set_zlim([self.ax.get_zlim()[0]*scale, self.ax.get_zlim()[1]*scale])
        self.canvas.draw_idle()

    def set_view(self, view_type):
        if view_type == "default":
            self.ax.view_init(elev=30, azim=-60)
        elif view_type == "top":
            self.ax.view_init(elev=90, azim=-90)
        elif view_type == "front":
            self.ax.view_init(elev=0, azim=-90)
        elif view_type == "side":
            self.ax.view_init(elev=0, azim=0)
        self.canvas.draw_idle()

    def load_stl(self):
        file_path = filedialog.askopenfilename(filetypes=[("STL Files", "*.stl")])
        if not file_path:
            return

        clean_filename = os.path.basename(file_path)
        imported_mesh = mesh.Mesh.from_file(file_path)

        # Bounding box & centring math
        minx, maxx = imported_mesh.x.min(), imported_mesh.x.max()
        miny, maxy = imported_mesh.y.min(), imported_mesh.y.max()
        minz, maxz = imported_mesh.z.min(), imported_mesh.z.max()
    
        totalx, totaly, totalz = abs(maxx-minx), abs(maxy-miny), abs(maxz-minz)

        shift_x = - ((minx + maxx) / 2.0)
        shift_y = - ((miny + maxy) / 2.0)
        shift_z = - minz 
        
        imported_mesh.x += shift_x
        imported_mesh.y += shift_y
        imported_mesh.z += shift_z

        poly_collection = art3d.Poly3DCollection(
            imported_mesh.vectors, facecolor="#9152C5", edgecolor="#00000016"
        ) 
        self.ax.add_collection3d(poly_collection)

        # Create the unique state dictionary for this specific part
        mesh_state = {
            "name": clean_filename,
            "collection": poly_collection,
            "base_vectors": imported_mesh.vectors.copy(),
            "native_limits": {
                "min_x": imported_mesh.x.min(), "max_x": imported_mesh.x.max(),
                "min_y": imported_mesh.y.min(), "max_y": imported_mesh.y.max(),
                "min_z": imported_mesh.z.min(), "max_z": imported_mesh.z.max()
            },
            "live_bounds": {
                "min_x": imported_mesh.x.min(), "max_x": imported_mesh.x.max(),
                "min_y": imported_mesh.y.min(), "max_y": imported_mesh.y.max(),
                "min_z": imported_mesh.z.min(), "max_z": imported_mesh.z.max()
            },

            "pos": {"x": 0.0, "y": 0.0, "z": 0.0},
            "scale": {"x": 100.0, "y": 100.0, "z": 100.0},
            "width": {"x": totalx, "y": totaly, "z": totalz},
        }

        self.meshes.append(mesh_state)
        self.model_list.insert(tk.END, clean_filename)

        # Programmatically highlight the newly added part
        self.model_list.selection_clear(0, tk.END)
        self.model_list.selection_set(tk.END)
        self.on_mesh_select()

        self._evaluate_scene_collisions()
        self.canvas.draw_idle()

    def custom_model(self):
        modelname = simpledialog.askstring("Input", "Please enter file name: ")
        if modelname == '':
            return
        
        self.model_list.insert(tk.END, modelname)

        simple_cube_verts = np.array([
            [ -5, -5, 0],
            [  5, -5, 0],
            [  5,  5, 0],
            [ -5,  5, 0],
            [ -5, -5, 10],
            [  5, -5, 10],
            [  5,  5, 10],
            [ -5,  5, 10]
        ])

        simple_cube_faces = np.array([
                [simple_cube_verts[0], simple_cube_verts[1], simple_cube_verts[2], simple_cube_verts[3]], # Bottom
                [simple_cube_verts[4], simple_cube_verts[5], simple_cube_verts[6], simple_cube_verts[7]], # Top
                [simple_cube_verts[0], simple_cube_verts[1], simple_cube_verts[5], simple_cube_verts[4]], # Front
                [simple_cube_verts[2], simple_cube_verts[3], simple_cube_verts[7], simple_cube_verts[6]], # Back
                [simple_cube_verts[1], simple_cube_verts[2], simple_cube_verts[6], simple_cube_verts[5]], # Right
                [simple_cube_verts[0], simple_cube_verts[3], simple_cube_verts[7], simple_cube_verts[4]]  # Left
            ])

        simple_cube = art3d.Poly3DCollection(simple_cube_faces,
                                            facecolor= "#9152C5",
                                            edgecolor="#00000016"
                                            ) 
       


        self.base_min_x, self.base_max_x = -5.0,  5.0
        self.base_min_y, self.base_max_y = -5.0,  5.0
        self.base_min_z, self.base_max_z =  0.0, 10.0

        mesh_state = {
            "name": modelname,
            "collection": simple_cube,
            "base_vectors": simple_cube_faces.copy(),
            "native_limits": {
                "min_x": -5, "max_x": 5,
                "min_y": -5, "max_y": 5,
                "min_z": 0, "max_z": 10
            },
            "live_bounds": {
                "min_x": -5, "max_x": 5,
                "min_y": -5, "max_y": 5,
                "min_z": 0, "max_z": 10
            },

            "pos": {"x": 0.0, "y": 0.0, "z": 0.0},
            "scale": {"x": 100.0, "y": 100.0, "z": 100.0},
            "width": {"x": 10, "y": 10, "z": 10},
        }
        self.meshes.append(mesh_state)

        self.ax.add_collection3d(simple_cube)
        self._evaluate_scene_collisions()
        self.canvas.draw()
        self.model_list.selection_clear(0, tk.END)
        self.model_list.selection_set(tk.END)
        self.on_mesh_select()


    def preview_gcode(self):
        for mesh in self.meshes:
            if mesh.get("is_colliding"):
                messagebox.showwarning("Error", "Please resolve model collisions first.")
                return

        if len(self.meshes) > 1:
            too_close = False
            num_meshes = len(self.meshes)
            for i in range(num_meshes):
                for j in range(i + 1, num_meshes):
                    box_A = self.meshes[i]["live_bounds"]
                    box_B = self.meshes[j]["live_bounds"]
                    
                    overlap_y = box_A["min_y"] < box_B["max_y"] and box_A["max_y"] > box_B["min_y"]
                    
                    if overlap_y:
                        if box_A["max_x"] <= box_B["min_x"]:
                            gap = box_B["min_x"] - box_A["max_x"]
                        elif box_B["max_x"] <= box_A["min_x"]:
                            gap = box_A["min_x"] - box_B["max_x"]
                        else:
                            gap = 0
                            
                        if gap < 57.14:
                            too_close = True
                            break
                if too_close:
                    break

            if too_close:
                ans = messagebox.askyesno(
                    "Models Too Close",
                    "The x-gap between models sharing the same Y-axis is less than 2.25 inches (57.15mm), which may cause foil binding.\n\nWould you like to auto-arrange them?"
                )
                if ans:
                    self.auto_arrange()
                return

        if not self.meshes:
            return

        # compile gcode
        compiler = FabriSlicer(self)
        self.gcode, self.gcode_stats = compiler.generate_master_gcode()
        
        if self.gcode_stats:
            foil_m = self.gcode_stats.get('total_foil_print', 0) / 1000.0
            weight_g = self.gcode_stats.get('total_weight_print', 0)
            net_weight_g = self.gcode_stats.get('total_net_weight', 0)
            waste_g = self.gcode_stats.get('total_waste_weight', 0)
            time_m = self.gcode_stats.get('total_time_min', 0)
            
            waste_pct = (waste_g / weight_g * 100.0) if weight_g > 0 else 0.0
            
            self.foil_stat_lbl.config(text=f"Total Foil: {foil_m:.2f} m")
            self.weight_stat_lbl.config(text=f"Total Tape Weight: {weight_g:.2f} g")
            self.net_weight_lbl.config(text=f"Net Part Weight: {net_weight_g:.2f} g")
            self.waste_weight_lbl.config(text=f"Waste: {waste_g:.2f} g ({waste_pct:.1f}%)")
            
            hours = int(time_m // 60)
            mins = int(time_m % 60)
            if hours > 0:
                self.time_stat_lbl.config(text=f"Est. Time: {hours} hr {mins} min")
            else:
                self.time_stat_lbl.config(text=f"Est. Time: {mins} min")
        else:
            self.foil_stat_lbl.config(text="Total Foil: N/A")
            self.weight_stat_lbl.config(text="Total Tape Weight: N/A")
            self.net_weight_lbl.config(text="Net Part Weight: N/A")
            self.waste_weight_lbl.config(text="Waste: N/A")
            self.time_stat_lbl.config(text="Est. Time: N/A")

        # interpret gcode
        lines = self.gcode.split('\n')
        sim = GCodeInterpreter(lines)
        sim.run()

        #swap ui frame
        self.prep_container.place_forget()
        self.preview_container.place(x=0, y=0, relwidth=1, relheight=1)

       
        self.ax.clear()
        self.setup_build_volume()

        # Render the toolpath directly via the interpreter
        res = sim.render_on_axes(self.ax)
        if isinstance(res, tuple) and len(res) == 4:
            self.rendered_elements, self.weld_z_values, self.time_to_layer_map, self.global_move_idx = res
            
            max_layer = max(1, len(self.weld_z_values))
            
            self.is_updating_scrubbers = True
            self.layer_scale.config(from_=1, to=max_layer)
            self.layer_spin.config(from_=1, to=max_layer)
            self.layer_var.set(max_layer)
            
            self.move_scale.config(from_=0, to=self.global_move_idx)
            self.move_spin.config(from_=0, to=self.global_move_idx)
            self.move_var.set(self.global_move_idx)
            self.is_updating_scrubbers = False
            self.manual_visibility_draw()

        self.canvas.draw_idle()


    def exit_preview_mode(self):
        # 1. Swap UI back
        self.preview_container.place_forget()
        self.prep_container.place(x=0, y=0, relwidth=1, relheight=1)

        # 2. Reset the 3D stage
        self.ax.clear()
        self.setup_build_volume()

        # 3. Resurrect the 3D meshes from your Python memory registry
        for mesh_obj in self.meshes:
            self.ax.add_collection3d(mesh_obj["collection"])

        self._evaluate_scene_collisions()
        self.canvas.draw_idle()


    def save_gcode_to_disk(self):
        if not self.gcode or self.gcode.strip() == "":
            messagebox.showinfo("Empty", "No GCODE generated yet.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".nc",
            filetypes=[("CNC (.nc) Files", "*.nc"), ("All Files", "*.*")],
            title="Save GCODE"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.gcode)

    

    def on_layer_scrub(self, val):
        if getattr(self, 'is_updating_scrubbers', False): return
        self.is_updating_scrubbers = True
        
        if hasattr(self, 'global_move_idx'):
            self.move_var.set(self.global_move_idx)
        
        self.manual_visibility_draw()
        self.is_updating_scrubbers = False

    def on_move_scrub(self, val):
        if getattr(self, 'is_updating_scrubbers', False): return
        self.is_updating_scrubbers = True
        
        try:
            move_idx = int(float(val))
        except ValueError:
            move_idx = 0
            
        if hasattr(self, 'time_to_layer_map') and move_idx in self.time_to_layer_map:
            self.layer_var.set(self.time_to_layer_map[move_idx])
            
        self.manual_visibility_draw()
        self.is_updating_scrubbers = False

    def manual_visibility_draw(self):
        if not hasattr(self, 'rendered_elements'): return
        
        try:
            max_idx = int(self.layer_var.get()) - 1
        except tk.TclError:
            max_idx = 0
            
        if max_idx >= len(self.weld_z_values): max_idx = len(self.weld_z_values) - 1
        if max_idx < 0: max_idx = 0
        
        current_max_z = self.weld_z_values[max_idx] if self.weld_z_values else 0
        
        try:
            current_max_move = int(self.move_var.get())
        except tk.TclError:
            current_max_move = 0
        
        for z, m_idx, element in self.rendered_elements:
            visible = (z <= current_max_z + 1e-4) and (m_idx <= current_max_move)
            if hasattr(element, 'set_visible'):
                element.set_visible(visible)
        self.canvas.draw_idle()

    def centre_print(self):
        if not self.model_list.curselection():
            return
        
        # Setting these to 0 automatically triggers transform_mesh() via your traces!
        self.x_pos_var.set(0.0)
        self.y_pos_var.set(0.0)
        self.z_pos_var.set(0.0)       

    def auto_arrange(self):
        if len(self.meshes) <= 1:
            return
            
        def push_mesh(mesh, dx, dy):
            mesh["pos"]["x"] += dx
            mesh["pos"]["y"] += dy
            mesh["live_bounds"]["min_x"] += dx
            mesh["live_bounds"]["max_x"] += dx
            mesh["live_bounds"]["min_y"] += dy
            mesh["live_bounds"]["max_y"] += dy

        X_CLEARANCE = 57.15
        Y_CLEARANCE = 3.0 # Minimum edgewise gap (calculated from your 10x10 trial yielding 3mm edge distance)
        
        # Max valid physical boundaries
        MAX_X = 127.0 - 58.0
        MIN_X = -127.0
        MAX_Y = 127.0 - 3.0
        MIN_Y = -127.0 + 3.0

        # Iterative physics-style overlap resolution
        for _ in range(100):
            resolved_any = False
            for i in range(len(self.meshes)):
                for j in range(i + 1, len(self.meshes)):
                    A = self.meshes[i]
                    B = self.meshes[j]
                    
                    boundsA = A["live_bounds"]
                    boundsB = B["live_bounds"]
                    
                    # Compute overlaps
                    if boundsA["min_x"] < boundsB["min_x"]:
                        dx = (boundsA["max_x"] + X_CLEARANCE) - boundsB["min_x"]
                    else:
                        dx = (boundsB["max_x"] + X_CLEARANCE) - boundsA["min_x"]
                        
                    if boundsA["min_y"] < boundsB["min_y"]:
                        dy = (boundsA["max_y"] + Y_CLEARANCE) - boundsB["min_y"]
                    else:
                        dy = (boundsB["max_y"] + Y_CLEARANCE) - boundsA["min_y"]
                        
                    if dx > 0 and dy > 0:
                        resolved_any = True
                        # Resolve along axis of minimum penetration
                        if dx < dy:
                            shift = (dx / 2.0) + 0.01 # Tiny buffer to ensure resolution
                            if boundsA["min_x"] < boundsB["min_x"]:
                                push_mesh(A, -shift, 0)
                                push_mesh(B, shift, 0)
                            else:
                                push_mesh(A, shift, 0)
                                push_mesh(B, -shift, 0)
                        else:
                            shift = (dy / 2.0) + 0.01
                            if boundsA["min_y"] < boundsB["min_y"]:
                                push_mesh(A, 0, -shift)
                                push_mesh(B, 0, shift)
                            else:
                                push_mesh(A, 0, shift)
                                push_mesh(B, 0, -shift)
            
            # Constrain to valid bed area
            for mesh in self.meshes:
                bounds = mesh["live_bounds"]
                if bounds["max_x"] > MAX_X:
                    push_mesh(mesh, MAX_X - bounds["max_x"], 0)
                if bounds["min_x"] < MIN_X:
                    push_mesh(mesh, MIN_X - bounds["min_x"], 0)
                if bounds["max_y"] > MAX_Y:
                    push_mesh(mesh, 0, MAX_Y - bounds["max_y"])
                if bounds["min_y"] < MIN_Y:
                    push_mesh(mesh, 0, MIN_Y - bounds["min_y"])
                    
            if not resolved_any:
                break
                
        # Recompute final geometric transforms for display
        for mesh in self.meshes:
            scale_x = mesh["scale"]["x"] / 100.0
            scale_y = mesh["scale"]["y"] / 100.0
            scale_z = mesh["scale"]["z"] / 100.0
            
            limits = mesh["native_limits"]
            centre_x = (limits["min_x"] + limits["max_x"]) / 2.0
            centre_y = (limits["min_y"] + limits["max_y"]) / 2.0
            
            transformed = mesh["base_vectors"].astype(float)
            transformed[:, :, 0] = centre_x + (transformed[:, :, 0] - centre_x) * scale_x + mesh["pos"]["x"]
            transformed[:, :, 1] = centre_y + (transformed[:, :, 1] - centre_y) * scale_y + mesh["pos"]["y"]
            transformed[:, :, 2] = limits["min_z"] + (transformed[:, :, 2] - limits["min_z"]) * scale_z + mesh["pos"]["z"]
            
            mesh["collection"].set_verts(transformed)

        # Update UI sliders to reflect the new position of the currently selected model
        selected = self.model_list.curselection()
        if selected:
            self._ui_block = True
            active_mesh = self.meshes[selected[0]]
            self.x_pos_var.set(active_mesh["pos"]["x"])
            self.y_pos_var.set(active_mesh["pos"]["y"])
            self._ui_block = False

        self._evaluate_scene_collisions()
        self.canvas.draw_idle()

    def reconcile_dimensions(self, trigger_source, axis):
        if getattr(self, '_ui_block', False) or getattr(self, '_dim_sync_lock', False):
            return

        selected = self.model_list.curselection()
        if not selected:
            return

        active_mesh = self.meshes[selected[0]]
        limits = active_mesh["native_limits"] 
        base_span = limits[f"max_{axis}"] - limits[f"min_{axis}"]

        if base_span <= 0.0001:
            return

        self._dim_sync_lock = True
        try:
            width_var = getattr(self, f"{axis}_width_var")
            scale_var = getattr(self, f"{axis}_scale_var")
            max_machine_span = 252.0 if axis in ('x', 'y') else 254.0

            if trigger_source == 'width':
                req_width = width_var.get()
                clamped_width = max(0.001, min(max_machine_span, req_width))
                derived_scale_pct = (clamped_width / base_span) * 100.0

                if req_width != clamped_width:
                    width_var.set(clamped_width)
                scale_var.set(derived_scale_pct)

            elif trigger_source == 'scale':
                req_scale_pct = scale_var.get()
                req_width = base_span * (req_scale_pct / 100.0)
                clamped_width = max(0.001, min(max_machine_span, req_width))
                clamped_scale_pct = (clamped_width / base_span) * 100.0

                if req_scale_pct != clamped_scale_pct:
                    scale_var.set(clamped_scale_pct)
                width_var.set(clamped_width)

        except tk.TclError:
            pass
        finally:
            self._dim_sync_lock = False

        self.transform_mesh()



    def transform_mesh(self, *args):
        if getattr(self, '_ui_block', False) or getattr(self, '_trace_lock', False):
            return

        selected = self.model_list.curselection()
        if not selected:
            return

        active_mesh = self.meshes[selected[0]]
        limits = active_mesh["native_limits"]

        centre_x = (limits["min_x"] + limits["max_x"]) / 2.0
        centre_y = (limits["min_y"] + limits["max_y"]) / 2.0

        try:
            x_pos, y_pos, z_pos = self.x_pos_var.get(), self.y_pos_var.get(), self.z_pos_var.get()
            scale_x = self.x_scale_var.get() / 100.0
            scale_y = self.y_scale_var.get() / 100.0
            scale_z = self.z_scale_var.get() / 100.0

            x_width = self.x_width_var.get()
            y_width = self.y_width_var.get()
            z_width = self.z_width_var.get()
        except tk.TclError:
            return

        # Centroid scaling for X/Y; Bedrock Floor scaling for Z
        centre_x = (limits["min_x"] + limits["max_x"]) / 2.0
        centre_y = (limits["min_y"] + limits["max_y"]) / 2.0

        scaled_min_x = (limits["min_x"] - centre_x) * scale_x
        scaled_max_x = (limits["max_x"] - centre_x) * scale_x

        scaled_min_y = (limits["min_y"] - centre_y) * scale_y
        scaled_max_y = (limits["max_y"] - centre_y) * scale_y

        live_z_height = (limits["max_z"] - limits["min_z"]) * scale_z
        
        

        # Dynamic Boundary Clamping 
        clamped_x = max(-126.0 - scaled_min_x, min(126.0 - scaled_max_x, x_pos))
        clamped_y = max(-126.0 - scaled_min_y, min(126.0 - scaled_max_y, y_pos))
        clamped_z = max(-limits["min_z"], min(254.0 - live_z_height - limits["min_z"], z_pos))
        

        if (x_pos != clamped_x or y_pos != clamped_y or z_pos != clamped_z):
            self._trace_lock = True
            self.x_pos_var.set(clamped_x)
            self.y_pos_var.set(clamped_y)
            self.z_pos_var.set(clamped_z)
            self._trace_lock = False
            x_pos, y_pos, z_pos = clamped_x, clamped_y, clamped_z

        # Save active transformations back into the part's state dictionary
        active_mesh["pos"] = {"x": x_pos, "y": y_pos, "z": z_pos}
        active_mesh["width"] = {"x": x_width, "y": y_width, "z": z_width}
        active_mesh["scale"] = {"x": scale_x * 100.0, "y": scale_y * 100.0, "z": scale_z * 100.0}

        # Execute Matrix SRT on the individual part
        transformed = active_mesh["base_vectors"].astype(float)
        
        transformed[:, :, 0] = centre_x + (transformed[:, :, 0] - centre_x) * scale_x + x_pos
        transformed[:, :, 1] = centre_y + (transformed[:, :, 1] - centre_y) * scale_y + y_pos
        transformed[:, :, 2] = limits["min_z"] + (transformed[:, :, 2] - limits["min_z"]) * scale_z + z_pos
       

        active_mesh["live_bounds"] = {
            "min_x": float(transformed[:, :, 0].min()),
            "max_x": float(transformed[:, :, 0].max()),
            
            "min_y": float(transformed[:, :, 1].min()),
            "max_y": float(transformed[:, :, 1].max()),
            
            "min_z": float(transformed[:, :, 2].min()),
            "max_z": float(transformed[:, :, 2].max())
        }
        active_mesh["collection"].set_verts(transformed)
        
        # Check the scene and paint overlapping models red before drawing!
        self._evaluate_scene_collisions() 

        self.canvas.draw_idle()


    def _evaluate_scene_collisions(self):
        """Scans all living meshes for 3D AABB intersections and updates their colors."""
        # 1. Reset everyone's status to safe
        for mesh_obj in self.meshes:
            mesh_obj["is_colliding"] = False

        num_meshes = len(self.meshes)
        
        # 2. Check every unique pair of meshes once (e.g. A vs B, A vs C, B vs C)
        for i in range(num_meshes):
            for j in range(i + 1, num_meshes):
                box_A = self.meshes[i]["live_bounds"]
                box_B = self.meshes[j]["live_bounds"]

                # True solid intersection test. 
                # (Using strictly '<' instead of '<=' ensures that two cubes sitting 
                # perfectly flush side-by-side touching faces don't trigger a false alarm).
                overlap_x = box_A["min_x"] < box_B["max_x"] and box_A["max_x"] > box_B["min_x"]
                overlap_y = box_A["min_y"] < box_B["max_y"] and box_A["max_y"] > box_B["min_y"]
                overlap_z = box_A["min_z"] < box_B["max_z"] and box_A["max_z"] > box_B["min_z"]

                if overlap_x and overlap_y and overlap_z:
                    self.meshes[i]["is_colliding"] = True
                    self.meshes[j]["is_colliding"] = True

        # 3. Apply the paint to Matplotlib
        for mesh_obj in self.meshes:
            # Normal = Purple; Colliding = Warning Red
            target_color = "#D9383A" if mesh_obj.get("is_colliding") else "#9152C5"
            mesh_obj["collection"].set_facecolor(target_color)
    
        

    def on_resize(self, event):
        if event.widget != self:
            return
        
        current_geom = (event.width, event.height)
        if current_geom == self._last_geom:
            return
        self._last_geom = current_geom

        self._window_width = event.width
        self._window_height = event.height
       
        
        # update widget dimensions and coordinates
        self.set_widths_and_heights()
        self.set_widget_coords()         


        if self._resize_job is not None:
            self.after_cancel(self._resize_job)

        self._resize_job = self.after(100, self._redraw_viewport)

    def on_mesh_select(self, event=None):
        """Fired when the user clicks a different model in the Listbox."""
        if getattr(self, '_ui_block', False):
            return

        selected = self.model_list.curselection()
        if not selected:
            return

        mesh_data = self.meshes[selected[0]]

        # ENGAGE SILENCE LOCK: We are programmatically altering spinbox values.
        # This stops the attached traces from accidentally triggering transform_mesh().
        self._ui_block = True
        try:
            self.x_pos_var.set(mesh_data["pos"]["x"])
            self.y_pos_var.set(mesh_data["pos"]["y"])
            self.z_pos_var.set(mesh_data["pos"]["z"])

            self.x_width_var.set(mesh_data["width"]["x"])
            self.y_width_var.set(mesh_data["width"]["y"])
            self.z_width_var.set(mesh_data["width"]["z"])

            self.x_scale_var.set(mesh_data["scale"]["x"])
            self.y_scale_var.set(mesh_data["scale"]["y"])
            self.z_scale_var.set(mesh_data["scale"]["z"])
        finally:
            self._ui_block = False

    

    def _redraw_viewport(self):
        self._resize_job = None
        
        # Explicitly push the new pixel dimensions to the underlying Matplotlib Figure
        dpi = self.fig.get_dpi()
        w = self._viewport_frame_w - 2
        h = self._viewport_frame_h - 2
        self.fig.set_size_inches(w / dpi, h / dpi, forward=True)
        
        self.canvas.draw_idle()

    def safe_shutdown(self):
        #Kill any pending asynchronous debouncing loops
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
            self._resize_job = None

        #Purge the 3D figure from Matplotlib's global memory registry 
        plt.close(self.fig)
        plt.close('all')

        #Terminate the Tkinter mainloop and destroy the Tcl interpreter
        self.quit()
        self.destroy()

    def _delete_selected_item(self, event=None):
        selected = self.model_list.curselection()
        if not selected:
            return  

        # Iterate in reverse so index shifts don't throw off the loop
        for idx in reversed(selected):
            # 1. Erase the polygon from Matplotlib's 3D space
            self.meshes[idx]["collection"].remove()
            # 2. Pop the dictionary out of the internal registry
            self.meshes.pop(idx)
            # 3. Delete the text label from the UI
            self.model_list.delete(idx)

        self._evaluate_scene_collisions()
        self.canvas.draw_idle()

        # If any other models survived the purge, select the last one automatically
        if self.meshes:
            self.model_list.selection_set(tk.END)
            self.on_mesh_select()
            




if __name__ == "__main__":
    gui = FabriGui()
    gui.bind("<Configure>", gui.on_resize)
    gui.mainloop()
