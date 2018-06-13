import vtk

colors = vtk.vtkNamedColors()

LastLayerColor = colors.GetColor3d("Red")
LayerColor = colors.GetColor3d("White")
BackgroundColor = colors.GetColor3d("SlateGray")
PlaneColor = colors.GetColor3d("Cyan")

PlaneXSize = 200
PlaneYSize = 200

SliceCommand = "./goosli --stl={stl} --gcode={gcode} --thickness={thickness}"
OutputGCode = "out.gcode"

#TODO: make from txt file?