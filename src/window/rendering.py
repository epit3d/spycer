"""3D rendering utilities for :mod:`src.window`."""

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from src.InteractorAroundActivePlane import InteractionAroundActivePlane
from src import gui_utils
from src.settings import get_color


def init_3d_widget(window):
    """Create and initialize the VTK rendering widget for ``window``."""
    widget3d = QVTKRenderWindowInteractor(window)
    widget3d.installEventFilter(window)

    window.render = vtk.vtkRenderer()
    window.render.SetBackground(get_color("white"))

    widget3d.GetRenderWindow().AddRenderer(window.render)
    window.interactor = widget3d.GetRenderWindow().GetInteractor()
    window.interactor.SetInteractorStyle(None)

    window.interactor.Initialize()
    window.interactor.Start()

    # set position of camera to (5, 5, 5) and look at (0, 0, 0)
    window.render.GetActiveCamera().SetPosition(5, 5, 5)
    window.render.GetActiveCamera().SetFocalPoint(0, 0, 0)
    window.render.GetActiveCamera().SetViewUp(0, 0, 1)

    window.customInteractor = InteractionAroundActivePlane(
        window.interactor, window.render
    )
    window.interactor.AddObserver(
        "MouseWheelBackwardEvent", window.customInteractor.middleBtnPress
    )
    window.interactor.AddObserver(
        "MouseWheelForwardEvent", window.customInteractor.middleBtnPress
    )
    window.interactor.AddObserver(
        "RightButtonPressEvent", window.customInteractor.rightBtnPress
    )
    window.interactor.AddObserver(
        "RightButtonReleaseEvent", window.customInteractor.rightBtnPress
    )
    window.interactor.AddObserver(
        "LeftButtonPressEvent",
        lambda obj, event: window.customInteractor.leftBtnPress(obj, event, window),
    )
    window.interactor.AddObserver(
        "LeftButtonReleaseEvent", window.customInteractor.leftBtnPress
    )
    window.interactor.AddObserver(
        "MouseMoveEvent",
        lambda obj, event: window.customInteractor.mouseMove(obj, event, window),
    )

    window.axesWidget = gui_utils.createAxes(window.interactor)

    window.planeActor = gui_utils.createPlaneActorCircle()
    window.planeTransform = vtk.vtkTransform()
    window.render.AddActor(window.planeActor)

    window.add_legend()

    window.splanes_actors = []

    widget3d.Initialize()
    widget3d.Start()

    return widget3d
