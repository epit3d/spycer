from typing import List
from .delta import DeltaParams


class Point:
    def __init__(self, X: float, Y: float, Z: float):
        self.X = X
        self.Y = Y
        self.Z = Z


def Escher(dp: DeltaParams, points: List[Point], factorsNumber: int) -> DeltaParams:
    # do Escher calculation here
    return dp
