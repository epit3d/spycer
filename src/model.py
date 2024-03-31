from src import gui_utils, gcode
from src.settings import Settings


class MainModel:
    def __init__(self):
        self.current_slider_value = None
        self.opened_stl = ""
        self.gcode = None
        self.opened_gcode = ""
        self.splanes = []
        self.planesActors = []

        self.figures_setts = []

    def load_gcode(self, filename):
        self.current_slider_value = None
        self.opened_gcode = filename
        self.gcode = gcode.readGCode(filename)
        return self.gcode

    def add_splane(self):
        if len(self.splanes) == 0:
            self.splanes.append(gui_utils.Plane(-60, 0, [10, 10, 10]))
        else:
            rot = 0.0
            if isinstance(self.splanes[-1], gui_utils.Plane):
                rot = self.splanes[-1].rot
            path = [self.splanes[-1].x, self.splanes[-1].y, self.splanes[-1].z + 10]
            self.splanes.append(gui_utils.Plane(0, rot, path))

        self.figures_setts.append(Settings())

    def add_cone(self):
        self.splanes.append(gui_utils.Cone(60, (0, 0, 10), 0, 100))

        self.figures_setts.append(Settings())
