from .http import getObjectModel, execGcode


class DeltaParams:
    diagonals = {
        'X': 246.650,
        'Y': 246.650,
        'Z': 246.650,
    }
    deltaRadius = 100
    homedHeight = 240
    bedRadius = 100
    towerAngCorr = {
        'X': 0,
        'Y': 0,
        'Z': 0,
    }
    endstopCorr = {
        'X': 0,
        'Y': 0,
        'Z': 0,
    }
    bedTilt = {
        'X': 0,
        'Y': 0,
    }

    def generateM665(self):
        M665 = "M665"
        M665 += f" L{self.diagonals['X']}:{self.diagonals['Y']}:{self.diagonals['Z']}"
        M665 += f" R{self.deltaRadius}"
        M665 += f" H{self.homedHeight}"
        M665 += f" B{self.bedRadius}"
        M665 += f" X{self.towerAngCorr['X']}"
        M665 += f" Y{self.towerAngCorr['Y']}"
        M665 += f" Z{self.towerAngCorr['Z']}"
        return M665

    def generateM666(self):
        M666 = "M666"
        M666 += f" X{self.endstopCorr['X']}"
        M666 += f" Y{self.endstopCorr['Y']}"
        M666 += f" Z{self.endstopCorr['Z']}"
        return M666

    def readFromPrinter(self):
        self.diagonals['X'] = getObjectModel('move.kinematics.towers[0].diagonal')
        self.diagonals['Y'] = getObjectModel('move.kinematics.towers[1].diagonal')
        self.diagonals['Z'] = getObjectModel('move.kinematics.towers[2].diagonal')

        self.deltaRadius = getObjectModel('move.kinematics.deltaRadius')
        self.homedHeight = getObjectModel('move.kinematics.homedHeight')
        self.bedRadius = getObjectModel('move.kinematics.printRadius')

        self.towerAngCorr['X'] = getObjectModel('move.kinematics.towers[0].angleCorrection')
        self.towerAngCorr['Y'] = getObjectModel('move.kinematics.towers[1].angleCorrection')
        self.towerAngCorr['Z'] = getObjectModel('move.kinematics.towers[2].angleCorrection')

        self.endstopCorr['X'] = getObjectModel('move.kinematics.towers[0].endstopAdjustment')
        self.endstopCorr['Y'] = getObjectModel('move.kinematics.towers[1].endstopAdjustment')
        self.endstopCorr['Z'] = getObjectModel('move.kinematics.towers[2].endstopAdjustment')

        self.bedTilt['X'] = getObjectModel('move.kinematics.xTilt')
        self.bedTilt['Y'] = getObjectModel('move.kinematics.yTilt')

    def writeToPrinter(self):
        execGcode(self.deltaParams.generateM665())
        execGcode(self.deltaParams.generateM666())
        execGcode("M500")

    def toString(self):
        res = ""
        res += f"Diagonal X:{self.diagonals['X']}\n"
        res += f"Diagonal Y:{self.diagonals['Y']}\n"
        res += f"Diagonal Z:{self.diagonals['Z']}\n"
        res += f"Delta Radius:{self.deltaRadius}\n"
        res += f"Homed Height:{self.homedHeight}\n"
        res += f"Bed Radius:{self.bedRadius}\n"
        res += f"Tower X Angle Correction:{self.towerAngCorr['X']}\n"
        res += f"Tower Y Angle Correction:{self.towerAngCorr['Y']}\n"
        res += f"Tower Z Angle Correction:{self.towerAngCorr['Z']}\n"
        res += f"Tower X Endstop Correction:{self.endstopCorr['X']}\n"
        res += f"Tower Y Endstop Correction:{self.endstopCorr['Y']}\n"
        res += f"Tower Z Endstop Correction:{self.endstopCorr['Z']}\n"
        res += f"Bed Tilt X:{self.bedTilt['X']}\n"
        res += f"Bed Tilt Y:{self.bedTilt['Y']}\n"
        return res
