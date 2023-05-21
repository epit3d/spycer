class SkewParams:
    """
    M556: Axis skew compensation
    Compensates the orthogonality skew.
    Positive values indicate that the angle between the axis pair is obtuse,
    negative acute.
    """

    skew = {
        'X': 0,  # error between X and Y for 1mm lenght
        'Y': 0,  # error between Y and Z for 1mm lenght
        'Z': 0,  # error between X and Z for 1mm lenght
    }

    def generateM556(self):
        M556 = "M556 S1"
        M556 += f" X{self.skew['X']}"
        M556 += f" Y{self.skew['Y']}"
        M556 += f" Z{self.skew['Z']}"
        return M556