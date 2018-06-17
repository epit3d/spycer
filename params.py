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

CutStlCommand = "./goosli_cutter --stl={stl} --out1={out1} --out2={out2} " \
                "--pointx={pointx} --pointy={pointy} --pointz={pointz} " \
                "--normali={normali} --normalj={normalj} --normalk={normalk}"
OutputCutStl1 = "goosli_cut1.stl"
OutputCutStl2 = "goosli_cut2.stl"
CutPointX = 0
CutPointY = 0
CutPointZ = 30
CutNormalI = -1
CutNormalJ = 0
CutNormalK = 1
Cut2Move = (20, 0, 0)
