from .steps import StepsCollection


class CalibrationModel():
    def __init__(self, printer):
        self.steps = StepsCollection(printer)
