#!/usr/bin/env python

# Demonstrate how to use the vtkBoxWidget to translate, scale, and
# rotate actors.  The basic idea is that the box widget controls an
# actor's transform. A callback which modifies the transform is
# invoked as the box widget is manipulated.

import vtk

# Start by creating some simple geometry; in this case a mace.
import gui_utils

sphere = vtk.vtkSphereSource()
cone = vtk.vtkConeSource()
glyph = vtk.vtkGlyph3D()
glyph.SetInputConnection(sphere.GetOutputPort())
glyph.SetSourceConnection(cone.GetOutputPort())
glyph.SetVectorModeToUseNormal()
glyph.SetScaleModeToScaleByVector()
glyph.SetScaleFactor(0.25)
appendData = vtk.vtkAppendPolyData()
appendData.AddInputConnection(glyph.GetOutputPort())
appendData.AddInputConnection(sphere.GetOutputPort())
maceMapper = vtk.vtkPolyDataMapper()
maceMapper.SetInputConnection(appendData.GetOutputPort())
maceActor = vtk.vtkLODActor()
maceActor.SetMapper(maceMapper)
maceActor.VisibilityOn()

# Create the RenderWindow, Renderer and both Actors
ren = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

# The box widget observes the events invoked by the render window
# interactor.  These events come from user interaction in the render
# window.
boxWidget = vtk.vtkBoxWidget()
boxWidget.SetInteractor(iren)
boxWidget.SetPlaceFactor(1.25)
boxWidget.HandlesOn()

# Add the actors to the renderer, set the background and window size.
ren.AddActor(maceActor)
ren.SetBackground(0.1, 0.2, 0.4)
renWin.SetSize(300, 300)

# As the box widget is interacted with, it produces a transformation
# matrix that is set on the actor.
t = vtk.vtkTransform()


def TransformActor(obj, event):
    global t, maceActor
    obj.GetTransform(t)
    # print(t.GetScale())
    print(t.GetPosition())

    maceActor.SetUserTransform(t)


# Place the interactor initially. The actor is used to place and scale
# the interactor. An observer is added to the box widget to watch for
# interaction events. This event is captured and used to set the
# transformation matrix of the actor.
boxWidget.SetProp3D(maceActor)
boxWidget.PlaceWidget()
boxWidget.AddObserver("InteractionEvent", TransformActor)

cylinder = vtk.vtkCylinderSource()
cylinder.SetResolution(50)
cylinder.SetRadius(2)
cylinder.SetHeight(0.1)
cylinder.SetCenter(0, 0, 0)  # WHAT? vtk :(
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(cylinder.GetOutputPort())
actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.RotateX(90)

ren.AddActor(actor)

axesWidget = gui_utils.createAxes(iren)

iren.Initialize()
renWin.Render()
iren.Start()
