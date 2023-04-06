class ScaleParams:
    """
    M579: Scale Cartesian axes
    If you print a part for which the Y length should be 100mm and measure it
    and find that it is 100.3mm long then you set Y0.997 (= 100/100.3).
    """

    scale = {
        'X': 1,
        'Y': 1,
        'Z': 1,
    }

    def generateM579(self):
        M579 = "M579"
        M579 += f" X{self.scale['X']}"
        M579 += f" Y{self.scale['Y']}"
        M579 += f" Z{self.scale['Z']}"
        return M579
