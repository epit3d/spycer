import vtk

Lang = "ru"

colors = vtk.vtkNamedColors()
LastLayerColor = colors.GetColor3d("Red")
LayerColor = colors.GetColor3d("White")
BackgroundColor = colors.GetColor3d("SlateGray")
PlaneColor = colors.GetColor3d("Cyan")

PlaneXSize = 200
PlaneYSize = 200

SliceCommand = "./goosli --stl={stl} --gcode={gcode} --thickness={thickness} " \
               "--originx={originx} --originy={originy} --originz={originz}"
OutputGCode = "goosli_out.gcode"

SimplifyStlCommand = "./goosli_simplifier --stl={stl} --out={out} --triangles={triangles}"
OutputSimplifiedStl = "goosli_simplified.stl"
SimplifyTriangles = "800"
