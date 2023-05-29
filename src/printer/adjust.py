class AdjustParams:
    V = 0
    tempV = 0

    def getVfromRaw(self, raw):
        # we invert value due to G92+G0 logic
        self.V = -self.parseG92(raw.decode(), 'V')

    def parseG92(self, text: str, axis):
        lines = text.splitlines()
        res = None
        for line in lines:
            line = line.strip()
            if line.startswith(';'):
                continue
            if line.startswith('G92'):
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

    def genG92forV(self):
        # we invert value due to G92+G0 logic
        return f'G92 V{-(self.V + self.tempV)}'
