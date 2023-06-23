class AdjustParams:
    V = 0
    tempV = 0

    def getVfromRaw(self, raw):
        self.V = self.parseAdjust(raw.decode(), "V")

    def parseAdjust(self, text: str, axis):
        lines = text.splitlines()
        res = None
        for line in lines:
            line = line.strip()
            if line.startswith(';'):
                continue
            if line.startswith("G0"):
                args = line.split(' ')[1:]
                for arg in args:
                    if arg.startswith(';'):
                        break
                    if arg.startswith(axis):
                        res = float(arg[1:])
                        break
                break

        if res is None:
            raise Exception(f'Unable to read adjustment for axis {axis}')

        return res

    def genAdjustV(self):
        return self.genAdjust("V", self.V + self.tempV)

    def genAdjustTempV(self):
        return self.genAdjust("V", self.tempV)

    def genAdjust(self, axis, val):
        return [
            "G91",
            f"G0 H2 {axis}{val}",
            "G90",
            f"G92 {axis}0",
        ]
