from src import gui_utils, gcode


class MainModel:
    def __init__(self):
        self.current_slider_value = 0
        self.stl_translation = [0.0, 0.0, 0.0]
        self.opened_stl = ""
        self.gcode = None
        self.opened_gcode = ""
        self.splanes = []
        self.planesActors = []

    def load_gcode(self, filename):
        self.opened_gcode = filename
        self.gcode = gcode.readGCode(filename)
        return self.gcode

    def add_splane(self):
        if len(self.splanes) == 0:
            self.splanes.append(gui_utils.Plane(True, 0, [10, 10, 10]))
        else:
            path = [self.splanes[-1].x, self.splanes[-1].y, self.splanes[-1].z + 10]
            self.splanes.append(gui_utils.Plane(False, 0, path))
