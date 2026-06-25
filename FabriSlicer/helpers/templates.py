class textureAndWeld():
	def __init__(self):
         #weld params/stats 
		self.total_foil_mm = 0
		self.total_weight_g = 0
		self.num_weldlines = 0
		self.est_time_min = 0
		self.weld_speed = 0
		self.print_start_x = 0
		self.print_end_x = 0
		self.dwelltime = 0
		self.rollback_imp = 0
		self.overlap_imp = 0
		self.foil_thickness_imp = 0
		self.offset = 0
		self.pause_l = 0
		self.pause_w = 0

        # size params
		self.print_x_mm = 0
		self.print_y_mm = 0
		self.print_start_y = 0

		self.tape_enable = False
	def set_speed(self, speed):
		#sets params that will change over time / params that need to be pushed multiple times
		gcode = f"""#<_WELDSPEED> = [{speed:.2f}]		(WELD SPEED IN IPM)
#<_WELDMIN1> = [#<_WELDSPEED> / #<_XINCWELDLG>]	(1/X MINUTES OF TOTAL WELD MOVEMENT; NEEDED FOR A/X AXIS SYNC MOTION)
#<_WELDMIN2> = [#<_WELDSPEED> / #<_ROLLBACK>]	(1/X MINUTES OF ROLLBACK WELD MOVEMENT; NEEDED FOR A/X AXIS SYNC MOTION)
#<_WELDMIN3> = [#<_WELDSPEED> / #<_TAPECUTLG>]  (1/X MINUTES OF WELD MOVEMENT BEFORE TAPE CUT)
#<_WELDMIN4> = [#<_WELDSPEED> / #<_TAPETAILLG>]	(1/X MINUTES OF WELD MOVEMENT AFTER TAPE CUT) """
		return gcode

	def layer_offsets(self):
		gcode = f"""#<_OffsetL1>=  0.000
#<_OffsetL1>=  0.000
#<_OffsetL2>=  0.030
#<_OffsetL3>= -0.030
#<_OffsetL4>= -0.015
#<_OffsetL5>=  0.015
#<_OffsetL6>= -0.035
#<_OffsetL7>= -0.050
#<_OffsetL8>= -0.020
#<_OffsetL9>=  0.005
#<_OffsetL10>= 0.050
#<_OffsetL11>=-0.015
#<_OffsetL12>= 0.035
#<_OffsetL13>= 0.050
#<_OffsetL14>= 0.000
#<_OffsetL15>=-0.020
#<_OffsetL16>=-0.050
#<_OffsetL17>= 0.000
#<_OffsetL18>= 0.025
#<_OffsetL19>= 0.050
#<_OffsetL20>=-0.005
#<_OffsetL21>=-0.025
#<_OffsetL22>=-0.040
#<_OffsetL23>= 0.015
#<_OffsetL24>= 0.035
#<_OffsetL25>=-0.010
#<_OffsetL26>= 0.030
#<_OffsetL27>= 0.045
#<_OffsetL28>= 0.020
#<_OffsetL29>=-0.005
#<_OffsetL30>=-0.025
"""
		return gcode

	def set_static_params(self,):
			
		gcode = f"""
(UTS FabriSlicer, Created by Lachlan torres 2026)
(SL1200-1022)
(Copyright © 2019 Fabrisonic® LLC All rights reserved)
#<_WELDHEIGHT> = [0]	(CURRENT WELD HEIGHT)
#<_TAPENUMBER> = [1]		(CURRENT TAPE NUMBER)
#<_LayerNumber> = [0]		(CURRENT LAYER NUMBER FOR STAGGER OFFSET CALCULATIONS)
#<_XSTART> = [{self.print_start_x:.4f}]		(START OF WELD X-POSITION; XMIN=-5.000)
#<_XEND> = [{self.print_end_x:.4f}]		    (END OF WELD X-POSITION; XMAX=5.000)
#<_DWELLTIME> = [{self.dwelltime}]		(DWELL LENGTH IN SECONDS)
#<_ROLLBACK> = [{self.rollback_imp}]		(X ROLLBACK LENGTH)
#<_OVERLAP> = [{self.overlap_imp}]		(TAPE OVERLAP VALUE)
#<_LayerThickness> = [0.006]	(ADJUSTED LAYER THICKNESS INCREMENT VALUE)
#<_TotalTapes> = [{self.num_weldlines}]		(TOTAL TAPES WIDE PER LAYER) 

#<_OptionLayerPause> = [{self.pause_l}]	(ENTER “1” TO STOP WELDER BETWEEN LAYERS FOR INSPECTION OR “0” TO NOT STOP)
#<_OptionWeldPause> = [{self.pause_w}]	(ENTER “1” TO STOP WELDER BETWEEN TAPES FOR INSPECTION OR “0” TO NOT STOP) 
#<_AFEEDLG> = [3.75]     			(LENGTH OF TAPE PRIMING FEED FOR 6" A-AXIS MOTOR)
#<_AFEEDVEL> = [200]     			(VELOCITY OF TAPE PRIMING FEED)
#<_XYZPOSVEL> = [200]    			(VELOCITY OF NON-CRITICAL MOVES)
#<_TAPEWIDTH> = [0.500]				(TAPE WIDTH)
#<_XEXTLG> = [2.250]      			(X EXTENSION LENGTH)
#<_ZABSSAFE> = [2.500]    			(WELDER LIFT HEIGHT)
#<_WELDERXOFFSET> = [-6.230]			(WELDER MEASURED X OFFSET FROM SPINDLE FOR T77)
#<_WELDERYOFFSET> = [0.000]			(WELDER MEASURED Y OFFSET FROM SPINDLE FOR T77)
#<_XINCWELDLG> = ABS[#<_XSTART> - #<_XEND>]	(CALCULATED X WELD LENGTH) (3+3 = 6)
#<_TAPETAILLG> = [0.25]			(AFFECTS TAIL LENGTH AFTER TAPE CUT) 
#<_TAPECUTLG> = [#<_XINCWELDLG> - #<_TAPETAILLG>]	(DISTANCE TRAVELED BEFORE TAPE CUT) (thf total distance travelled pre cut = 5.75)
#<_ODDEVENTEST> = [#<_TOTALTAPES>] 		(ASSIGN TOTAL TAPES VALUE TO SEPARATE VARIABLES FOR MANIPULATION)
#<_LayerNumberOffset> = [#<_LayerNumber>]	    (LAYER OFFSET TRACKER NUMBER)
#<_XABSWELDSTRT> = [#<_XSTART> + #<_ROLLBACK>]	(X POSITION OF START OF WELD WITH ROLLBACK)
#<_ARBLG> = [#<_ROLLBACK> * 0.5]		        (A MOTOR ROLLBACK LENGTH FOR 6" A-AXIS MOTOR)
#<_AWELDLG> = [#<_TAPECUTLG> * 0.5]     	(A WELD LENGTH FOR 6" A-AXIS MOTOR)
G54.1 P{self.offset}





"""
		return gcode

	def _return_offset_macro(self,macro_id):
		gcode = f"""

	(CALCULATE LAYER OFFSET FOR EACH LAYER AND TAPE)
	#<_Yoffset> = [#<_YWELDSTRT> + [[#<_TapeNumber> - 1] * #<_TAPEWIDTH>]]
	o<{macro_id}>32 IF [#<_LayerNumberOffset> EQ 1]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL1>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 2]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL2>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 3]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL3>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 4]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL4>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 5]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL5>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 6]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL6>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 7]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL7>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 8]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL8>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 9]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL9>]]
    o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 10]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL10>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 11]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL11>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 12]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL12>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 13]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL13>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 14]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL14>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 15]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL15>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 16]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL16>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 17]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL17>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 18]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL18>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 19]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL19>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 20]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL20>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 21]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL21>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 22]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL22>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 23]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL23>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 24]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL24>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 25]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL25>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 26]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL26>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 27]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL27>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 28]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL28>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 29]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL29>]]
	o<{macro_id}>32 ELSEIF [#<_LayerNumberOffset> EQ 30]
	#<_Yoffset> = [#<_Yoffset> + [#<_OffsetL30>]]
	o<{macro_id}>32 ENDIF"""

		return gcode


	def texturise_gcode(self,macro_id):
			set_variables = f"""
#<_YCENTER> = [{self.print_start_y:.4f}]\t\t(Y CENTER OF WELDS FOR Y POSITIONING)
#<_YABSCENTER> = [#<_WELDERYOFFSET> + #<_YCENTER>]	(ADJUSTED Y CENTER OF WELDS)
#<_TotalLayersToWeld> = [3]	(TOTAL NUMBER OF LAYERS TO WELD)
#<_TapeEnable> = [0]		(ENTER “1” TO ENABLE TAPE FEEDS AND “0” TO NOT)
#<_SonicsEnable> = [1]		(ENTER “1” TO ENABLE ULTRASONICS AND “0” TO NOT)

M0 (TEXTURE_WARNING.png)

o<{macro_id}>1 SUB
#<_YWELDSTRT> = [#<_YABSCENTER> - [[#<_TOTALTAPES> - 1] * [#<_TAPEWIDTH> / 2]]]
o<{macro_id}>1 ENDSUB

o<{macro_id}>01 SUB 

o<{macro_id}>02 WHILE [#<_LayerNumber> LE #<_TotalLayersToWeld> AND #<_TapeNumber> LE #<_TotalTapes>]
"""
			calc_layer_offset = self._return_offset_macro(macro_id)

			texturise =f"""
    (WELDER OPERATION FOR EACH TEXTURISE PASS)
	G90 G1 X[#<_XABSWELDSTRT> + #<_WELDERXOFFSET>] Y[#<_Yoffset>] F150.	(START OF WELD MOVE)
	M65 P0									(RETRACT HEAD TO MAKE SURE IT'S UP BEFORE FEEDING)
	M65 P1									(GUILLOTINE RETRACT TO MAKE SURE IT'S OPEN BEFORE FEEDING)
	G90 G1 Z[#<_WeldHeight>] F[#<_XYZPOSVEL>]				(WELD HEIGHT MOVE)
		M64 P0								(EXTEND HEAD)
		G04 P1								(DWELL TO ENSURE THE HEAD IS DOWN)

		M64 P3								(SONICS ON)

		G04 P[#<_DWELLTIME>]						(SPOT DWELL)

		G93 G91 G1 X[-[#<_ROLLBACK>]] F[#<_WELDMIN2>]		(ROLLBACK MOVE)
		G04 P[#<_DWELLTIME>]						(SPOT DWELL)
		G93 G91 G1 X[#<_XINCWELDLG>] F[#<_WELDMIN1>]		(WELD LENGTH WITH WELD 1/X_MINUTES)
		M65 P3								(SONICS OFF)
		M65 P0								(RETRACK HEAD)
        
	M66 P21									(CHECK IMAGINARY PIN BEFORE INCREMENTING)
	#<_TapeNumber> = [#<_TapeNumber> + 1]					(INCREMENT TAPE NUMBER)								
				

	(ITERATE LAYER# AND WELDHEIGHT IF CURRENT LAYER IS COMPLETE WHILE RESETTING TAPE# TO 1)
	o<{macro_id}>42 IF [#<_TapeNumber> GT #<_TotalTapes>]
	M66 P21 L0 						(CHECK IMAGINARY PIN BEFORE INCREMENTING)
	#<_LayerNumber> = [#<_LayerNumber> + 1]
	#<_LayerNumberOffset> = [#<_LayerNumber>]
	#<_WeldHeight> = [#<_WeldHeight> + #<_LayerThickness>]
	#<_TapeNumber> = 1
	(DEBUG, LAYER COMPLETE; READY TO WELD LAYER #<_LayerNumber>)
		o<{macro_id}>07 IF [#<_OptionLayerPause> EQ 1]		(CHECK FOR OPTIONAL INSPECTION BETWEEN LAYERS)
		G30						(UNLOAD HEIGHT)
		G90 G94 G0 X2 Y5				(INSPECTION POSITION)						(ADDITIONAL Z MOVE TO PREVENT MOTOR FROM FAULTING)
		M0
		o<{macro_id}>07 ENDIF
	o<{macro_id}>42 ENDIF

	(LIFT TO SAFE HEIGHT AND LOG VARIABLE VALUES)
	G94 G90 G1 Z[#<_ZABSSAFE>] F[#<_XYZPOSVEL>]		(SAFE Z POSITION MOVE)          
	(DEBUG, Weld height is #<_WeldHeight> Layer number is #<_LayerNumber> Tape number is #<_TapeNumber>)

o<{macro_id}>02 ENDWHILE 
o<{macro_id}>01 ENDSUB
o<{macro_id}>1  CALL			(EVEN OR ODD DETERMINATION)
o<{macro_id}>01 CALL			(EXECUTE THE SUBROUTINE GENERATED ABOVE)

"""
			return set_variables + calc_layer_offset + texturise 
    
	def welding_gcode(self,y_pos, macro_id, n_layers,n_weldlines,x_start, x_end, forced_layer_n=None):
		if forced_layer_n is not None:
			layer_tracker = forced_layer_n 
			n_layers = 1
			z_height = (forced_layer_n - 1) * 0.006
		else:
			layer_tracker = 1
			z_height = 0.000

		set_variables = f"""
#<_YCENTER> = [{y_pos:.4f}]\t\t(Y CENTER OF WELDS FOR Y POSITIONING)
#<_TotalLayersToWeld> = [{layer_tracker + n_layers - 1}]	(TOTAL NUMBER OF LAYERS TO WELD)
#<_TapeEnable> = [1]		(ENTER “1” TO ENABLE TAPE FEEDS AND “0” TO NOT)
#<_SonicsEnable> = [1]		(ENTER “1” TO ENABLE ULTRASONICS AND “0” TO NOT)
#<_XSTART> = [{x_start:.4f}]		(START OF WELD X-POSITION; XMIN=-5.000)
#<_XEND> = [{x_end:.4f}]		    (END OF WELD X-POSITION; XMAX=5.000)
#<_LayerNumber> = [{layer_tracker}]		(RESET LAYER NUMBER)
#<_LayerNumberOffset> = [{layer_tracker}]	(RESET LAYER OFFSET)
#<_TapeNumber> = [1]		(RESET TAPE NUMBER)

#<_TotalTapes> = [{n_weldlines}]		(TOTAL TAPES WIDE PER LAYER)
#<_WeldHeight> = [{z_height:.4f}]

#<_YABSCENTER> = [#<_YCENTER> + #<_WELDERYOFFSET>]
#<_XINCWELDLG> = ABS[#<_XSTART> - #<_XEND>]
#<_TAPECUTLG> = [#<_XINCWELDLG> - #<_TAPETAILLG>]
#<_XABSWELDSTRT> = [#<_XSTART> + #<_ROLLBACK>]
#<_AWELDLG> = [#<_TAPECUTLG> * 0.5]
#<_ODDEVENTEST> = [#<_TotalTapes>]

M0 (WELDING_WARNING.PNG)

o<{macro_id}>1 SUB
#<_YWELDSTRT> = [#<_YABSCENTER> - [[#<_TotalTapes> - 1] * [#<_TAPEWIDTH> / 2]]]
o<{macro_id}>1 ENDSUB

o<{macro_id}>01 SUB 
o<{macro_id}>02 WHILE [#<_LayerNumber> LE #<_TotalLayersToWeld> AND #<_TapeNumber> LE #<_TotalTapes>]
"""
		calc_layer_offsets = self._return_offset_macro(macro_id)
		weld = f"""
    (WELDER OPERATION FOR EACH WELD)
	G90 G1 X[#<_XABSWELDSTRT> + #<_WELDERXOFFSET>] Y[#<_Yoffset>] F150.	(START OF WELD MOVE)
	M65 P0									(RETRACT HEAD TO MAKE SURE IT'S UP BEFORE FEEDING)
	M65 P1									(GUILLOTINE RETRACT TO MAKE SURE IT'S OPEN BEFORE FEEDING)
	G90 G1 Z[#<_WeldHeight>] F[#<_XYZPOSVEL>]				(WELD HEIGHT MOVE)
		
		G94 G91 G1 A[#<_AFEEDLG>] F[#<_AFEEDVEL>]			(INCREMENTAL POSITIONING: ROTATION OF A-AXIS TO FEED TAPE)
		M64 P0								(EXTEND HEAD)
		G04 P1								(DWELL TO ENSURE THE HEAD IS DOWN)		
		M64 P3								(SONICS ON)
		G04 P[#<_DWELLTIME>]				(SPOT DWELL)
		G93 G91 G1 X[-[#<_ROLLBACK>]] F[#<_WELDMIN2>] A[-[#<_ARBLG>]]	(ROLLBACK MOVE)
		G04 P[#<_DWELLTIME>]						(SPOT DWELL)
		G93 G91 G1 X[#<_TAPECUTLG>] F[#<_WELDMIN3>] A[#<_AWELDLG>]	(WELD LENGTH WITH WELD 1/X_MINUTES)

		M64 P1								(GUILLOTINE CUT)
		G04 P0.02							(DWELL FOR P SECONDS)

		G93 G91 G1 X[#<_TAPETAILLG>] F[#<_WELDMIN4>]		(WELD LENGTH WITH WELD 1/X_MINUTES)

		M65 P3								(SONICS OFF)
		M65 P1								(GUILLOTINE RETRACT)
		M65 P0								(RETRACT HEAD)
		G04 P1								(DWELL TO ENSURE THE HEAD IS UP)
		G94 G91 G1 X[#<_XEXTLG>] F[#<_XYZPOSVEL>]			(INCREMENTAL MOVE TO GET TAPE OUT OF GUIDE)


	M66 P21									(CHECK IMAGINARY PIN BEFORE INCREMENTING)
	#<_TapeNumber> = [#<_TapeNumber> + 1]					(INCREMENT TAPE NUMBER)			
		o<{macro_id}>06 IF [#<_OptionWeldPause> EQ 1]			(CHECK OPTIONAL PAUSE BETWEEN WELDS)
			G90 G94 G0 X4.5 Y0 Z5
			M0
			o<{macro_id}>06 ENDIF
"""

		multiple_layer_macro = f"""(ITERATE LAYER# AND WELDHEIGHT IF CURRENT LAYER IS COMPLETE WHILE RESETTING TAPE# TO 1)
	o<{macro_id}>42 IF [#<_TapeNumber> GT #<_TotalTapes>]
	M66 P21 L0 						(CHECK IMAGINARY PIN BEFORE INCREMENTING)
	#<_LayerNumber> = [#<_LayerNumber> + 1]
	#<_LayerNumberOffset> = [#<_LayerNumber>]
	#<_WeldHeight> = [#<_WeldHeight> + #<_LayerThickness>]
	#<_TapeNumber> = 1
	(DEBUG, LAYER COMPLETE; READY TO WELD LAYER #<_LayerNumber>)
	
		o<{macro_id}>07 IF [#<_OptionLayerPause> EQ 1]		(CHECK FOR OPTIONAL INSPECTION BETWEEN LAYERS)
		G30						(UNLOAD HEIGHT)
		G90 G94 G0 X4.5 Y0 Z5				(INSPECTION POSITION)						(ADDITIONAL Z MOVE TO PREVENT MOTOR FROM FAULTING)
		M0
		o<{macro_id}>07 ENDIF
	o<{macro_id}>42 ENDIF

	(LIFT TO SAFE HEIGHT AND LOG VARIABLE VALUES)
	G94 G90 G1 Z[#<_ZABSSAFE>] F[#<_XYZPOSVEL>]		(SAFE Z POSITION MOVE)          
	(DEBUG, Weld height is #<_WeldHeight> Layer number is #<_LayerNumber> Tape number is #<_TapeNumber>)
"""	

		end_template = f"""o<{macro_id}>02 ENDWHILE 
o<{macro_id}>01 ENDSUB
o<{macro_id}>1 CALL				(EVEN OR ODD DETERMINATION)
o<{macro_id}>01 CALL			(EXECUTE THE SUBROUTINE GENERATED ABOVE)"""
		
		if n_layers == 1:
			weld_gcode = set_variables + calc_layer_offsets + weld + end_template
		else:
			weld_gcode = set_variables + calc_layer_offsets + weld + multiple_layer_macro + end_template

		return weld_gcode
    
	def operational_gcode(self,gcode_macros):
		gcode_pre_call = """(%%%%% BEGINNING OF OPERATIONAL CODE %%%%%)
G17 G90 G20 						(XY PLANE, ABSOLUTE DISTANCE MODE, UNITS IN INCHES)
T77 M6 G43 H77						(LOADS T77 PLUG AND WELDER Z-HEIGHT OFFSET)
G94 G90 G1 Z2.5 F150					(MOVE INTO SAFE Z POSITION)
G90 G1 X[#<_WELDERXOFFSET>] Y[#<_YABSCENTER>]  F150.	(MOVE INTO POSITION CENTERING WELDER)							(COOLANT NOZZLE ON FOR AIR ONLY)
M64 P2		(WELDER COOLING ON)
"""
		gcode_post_call = """G30		(MOVE Z TO UNLOAD HEIGHT)
M65 P2 		(COOLING OFF)
M9		(COOLANT NOZZLE OFF)
G94		(TURN OFF INVERSE TIME MOTION)
M30		(END PROGRAM)"""

		return gcode_pre_call + gcode_macros + gcode_post_call



        
	
	