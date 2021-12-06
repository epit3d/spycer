from src import gui_utils, gcode


class MainModel:
    def __init__(self):
        self.current_slider_value = None
        self.opened_stl = ""
        self.gcode = None
        self.opened_gcode = ""
        self.splanes = []
        self.planesActors = []

    def load_gcode(self, filename):
        self.current_slider_value = None
        self.opened_gcode = filename
        self.gcode = gcode.readGCode(filename)
        return self.gcode

    def add_splane(self):
        if len(self.splanes) == 0:
            self.splanes.append(gui_utils.Plane(-60, 0, [10, 10, 10]))
        else:
            path = [self.splanes[-1].x, self.splanes[-1].y, self.splanes[-1].z + 10]
            self.splanes.append(gui_utils.Plane(0, 0, path))

    def add_cone(self):
        self.splanes.append(gui_utils.Cone(60, (0, 0, 10), 15))
