import vtk


class ActorInteractorStyle(vtk.vtkInteractorStyleTrackballActor):

    def __init__(self, onChange, parent=None):
        self.WorkingActor = None
        self.onChange = onChange
        self.AddObserver("LeftButtonPressEvent", self.onPressEvent)
        self.AddObserver('MiddleButtonPressEvent', self.onPressEvent)
        self.AddObserver('RightButtonPressEvent', self.onPressEvent)
        self.AddObserver('LeftButtonReleaseEvent', self.onReleaseEvent)
        self.AddObserver('MiddleButtonReleaseEvent', self.onReleaseEvent)
        self.AddObserver('RightButtonReleaseEvent', self.onReleaseEvent)
        # self.AddObserver('MouseWheelForwardEvent', self.bimodal_mouse_handler)
        # self.AddObserver('MouseWheelBackwardEvent', self.bimodal_mouse_handler)

    def onPressEvent(self, obj, event):
        print("INSIDE!")
        # pos2d = obj.GetEventPosition()
        clickPos = self.GetInteractor().GetEventPosition()
        print(clickPos)

        picker = vtk.vtkPropPicker()
        picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())

        # get the new
        self.NewPickedActor = picker.GetActor()

        if self.NewPickedActor != self.WorkingActor:
            return

        print("BEFORE ON LEFT")

        if event == 'LeftButtonPressEvent':
            self.OnLeftButtonDown()
        elif event == 'MiddleButtonPressEvent':
            self.OnMiddleButtonDown()
        elif event == 'RightButtonPressEvent':
            self.OnRightButtonDown()
        return

    def onReleaseEvent(self, obj, event):
        if event == 'LeftButtonReleaseEvent':
            self.OnLeftButtonUp()
        elif event == 'MiddleButtonReleaseEvent':
            self.OnMiddleButtonUp()
        elif event == 'RightButtonReleaseEvent':
            self.OnRightButtonUp()
        self.onChange()
        return

    def setStlActor(self, stlActor):
        self.WorkingActor = stlActor


class CameraInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, parent=None):
        # self.__init__()
        pass
        # self.AddObserver("LeftButtonPressEvent" ,self.leftButtonPressEvent)
        #
        # self.LastPickedActor = None
        # self.LastPickedProperty = vtk.vtkProperty()

    # def leftButtonPressEvent(self ,obj ,event):
    #     print("INSIDE!")
    #     clickPos = self.GetInteractor().GetEventPosition()
    #     print(clickPos)
    #
    #     picker = vtk.vtkPropPicker()
    #     picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())
    #
    #
    #     # get the new
    #     self.NewPickedActor = picker.GetActor()
    #
    #     if self.NewPickedActor != self.LastPickedActor:
    #         print("not equal")
    #         # restore previous
    #         if self.LastPickedActor:
    #             self.LastPickedActor.GetProperty().DeepCopy(self.LastPickedProperty)
    #
    #         # If something was selected
    #         if self.NewPickedActor:
    #             # Save the property of the picked actor so that we can restore it next time
    #             self.LastPickedProperty.DeepCopy(self.NewPickedActor.GetProperty())
    #             # Highlight the picked actor by changing its properties
    #             self.NewPickedActor.GetProperty().SetColor(1.0, 0.0, 0.0)
    #             self.NewPickedActor.GetProperty().SetDiffuse(1.0)
    #             self.NewPickedActor.GetProperty().SetSpecular(0.0)
    #
    #         # save the last picked actor even if it is None
    #         self.LastPickedActor = self.NewPickedActor
    #
    #     print("BEFORE ON LEFT")
    #
    #     self.OnLeftButtonDown()
    #     return
