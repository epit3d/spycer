import vtk

Lang = "ru"
Debug = True

colors = vtk.vtkNamedColors()
LastLayerColor = colors.GetColor3d("Red")
LayerColor = colors.GetColor3d("White")
BackgroundColor = colors.GetColor3d("SlateGray")
PlaneColor = colors.GetColor3d("Cyan")

InclineXValue = 60

PlaneCenter = (0, 0, 0)
RotationCenter = (0, 0, 50)
PlaneXSize = 200
PlaneYSize = 200
PlaneDiameter = 250

SliceCommand = "./goosli --stl={stl} --gcode={gcode} --thickness={thickness} " \
               "--originx={originx} --originy={originy} --originz={originz} " \
               "--rotcx={rotcx} --rotcy={rotcy} --rotcz={rotcz} " \
               "--wall_thickness={wall_thickness} --fill_density={fill_density} --bed_temperature={bed_temperature} " \
               "--extruder_temperature={extruder_temperature} --print_speed={print_speed} --nozzle={nozzle} " \
               "--slicing_type={slicing_type} --planes_file={planes_file} " \
               "--print_speed_layer1={print_speed_layer1} --print_speed_wall={print_speed_wall} " \
               "--filling_type={filling_type} --angle={angle} " \
               "--retraction_speed={retraction_speed} --retraction_distance={retraction_distance}"

OutputGCode = "goosli_out.gcode"
PlanesFile = "planes_file.txt"

ColorizeStlCommand = "./goosli_colorizer --stl={stl} --out={out} --angle={angle}"
ColorizeResult = "colorize_triangles.bin"
ColorizeColor = colors.GetColor3d("Red")

AnalyzeStlCommand = "./goosli_analyzer --stl={stl} --angle={angle} --out={out} " \
                    "--originx={originx} --originy={originy} --originz={originz} " \
                    "--rotcx={rotcx} --rotcy={rotcy} --rotcz={rotcz} "
AnalyzeResult = "analyze_triangles.txt"


