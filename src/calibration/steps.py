import math
from .data import CalibrationData
from .reprapfirmware_lsq import Tuner


class Container:
    initZ = 0
    rawDelta = b''
    rawScale = b''
    rawSkew = b''
    rawAdjustV = b''
    fixture2Height = 0.1


class StepsCollection:
    def __init__(self, printer):
        self.printer = printer
        self.printer.setOutputMethod(print)
        self.printer.setStatusMethod(print)

        self.calibrationData = CalibrationData()

        self.container = Container()

        stepClasses = (Step1, Step2, Step3, FinalStep)
        self._steps = [Step(num, parent=self)
                       for num, Step in enumerate(stepClasses)]

    def __getitem__(self, i):
        return self._steps[i]

    def __len__(self):
        return len(self._steps)


class Step:
    def __init__(self, num, stepType='text', parent=None):
        self.num = num
        self.type = stepType
        self.setLang('ru')
        self.parent = parent
        self.printer = self.parent.printer
        self.calibrationData = self.parent.calibrationData
        self.container = self.parent.container

    def setLang(self, lang):
        if lang == 'ru':
            self.labelText = self.textRu
        elif lang == 'en':
            self.labelText = self.textEn

    def printerMethod(self):
        print('Printer method', self.num)


class Step1(Step):
    textRu = (
        '<p>'
        'Шаг 1 из 3'
        '</p>'
        '<p>'
        'Это диалоговое окно предназначено для сбора'
        ' калибровочных данных 3Д принтера Epit.'
        '</p>'
        '<p>'
        '<b>!!!ВАЖНО!!!</b>'
        '<br>'
        'Не нажимайте кнопку <b>Далее</b> до того, как будут выполнены'
        ' полностью все нижеописанные действия. Иначе может произойти'
        ' неконтролируемое столкновение печатающей головки с рабочим столом,'
        ' и 3Д принтер может получить серьёзные повреждения.'
        '</p>'
        '<p>'
        'Демонтируйте печатающую головку и установите на её место'
        ' специальный калибровочный модуль, поставляемый в комплекте с'
        ' 3Д принтером.'
        '</p>'
        '<p>'
        'Установите на рабочий стол калибровочную оснастку №1,'
        ' поставляемую в комплекте с 3Д принтером.'
        '</p>'
        '<p>'
        'Подсоедините кабель калибровочной оснастки №1 к калибровочному'
        ' разъему 3Д принтера.'
        '</p>'
        '<p>'
        'После нажатия кнопки <b>Далее</b> 3Д принтер начнёт выполнять'
        ' последовательность движений для сбора калибровочных данных.'
        '</p>'
    )

    textEn = (
        '<p>'
        'Step 1 of 3'
        '</p>'
        '<p>'
        'This wizard is intended for collecting the'
        ' calibration data of the Epit 3D printer.'
        '</p>'
        '<p>'
        '<b>!!!IMPORTANT!!!</b>'
        '<br>'
        'Please do not press <b>Next</b> button until the following actions'
        ' are fully completed. Otherwise, the printing head may crash into the'
        ' bed and 3D printer may be damaged.'
        '</p>'
        '<p>'
        'Please unmount printing head and mount calibrating module.'
        '</p>'
        '<p>'
        'Please mount the fixture #1 to the bed.'
        '</p>'
        '<p>'
        'Please connect the calibration wire.'
        '</p>'
        '<p>'
        'Upon pressing  the <b>Next</b> button printer will'
        ' perform movements to collect the calibration data.'
        '</p>'
    )

    def touchFixture(self):
        # first we touch the fixture from a long distance for safety
        safeZ = 50
        res = self.printer.touchBed(posZ=safeZ)
        _, _, Z = res[0]

        # set initial Z some distance higher than fixture surface
        self.container.initZ = Z + 5

    def adjustBedIncline(self):
        tangent = self.printer.defBedIncline(posZ=self.container.initZ)
        angle = math.degrees(math.atan(tangent))
        self.printer.adjustParams.tempV = angle
        self.printer.applyAdjustV()

        raw = self.printer.fileRead("0:/sys/adjustv.g")
        self.printer.adjustParams.getVfromRaw(raw)

        cmd = self.printer.adjustParams.genG92forV()
        self.container.rawAdjustV = cmd.encode()

    def calibrateDelta(self):
        self.printer.deltaParams.readFromPrinter()
        print(self.printer.deltaParams.toString())

        tuner = Tuner(
            self.printer.deltaParams.diagonals['X'],
            self.printer.deltaParams.deltaRadius,
            self.printer.deltaParams.homedHeight,
            self.printer.deltaParams.endstopCorr['X'],
            self.printer.deltaParams.endstopCorr['Y'],
            self.printer.deltaParams.endstopCorr['Z'],
            self.printer.deltaParams.towerAngCorr['X'],
            self.printer.deltaParams.towerAngCorr['Y'],
            self.printer.deltaParams.towerAngCorr['Z'],
            probe_radius=100,
            num_probe_points=7,
            num_factors=7,
        )
        tuner.set_firmware("RRF")

        points = tuner.get_probe_points()

        # collect points for delta calibration
        res = self.printer.defDelta(posZ=self.container.initZ, points=points)
        for p in res:
            print(p)

        tuner.set_probe_errors(res)

        # calculate new delta parameters
        cmds, dev_before, dev_after = tuner.calc(recalc=False)
        print(dev_before, dev_after)
        for cmd in cmds:
            print(cmd)
            if cmd != "":
                self.printer.execGcode(cmd)

        self.container.rawDelta = '\n'.join(cmds).encode()

    def calibrateScale(self):
        nominalX = 105
        nominalY = 105
        nominalZ = 75

        realX = self.printer.measureScaleX()
        realY = self.printer.measureScaleY()
        realZ = self.printer.measureScaleZ()

        self.printer.scaleParams.scale['X'] = realX / nominalX
        self.printer.scaleParams.scale['Y'] = realY / nominalY
        self.printer.scaleParams.scale['Z'] = realZ / nominalZ

        cmd = self.printer.scaleParams.generateM579()
        self.printer.execGcode(cmd)
        self.container.rawScale = cmd.encode()

    def calibrateSkew(self):
        skewXY = self.printer.measureOrthoXY()
        skewYZ = self.printer.measureOrthoYZ()
        skewXZ = self.printer.measureOrthoXZ()

        self.printer.skewParams.skew['X'] = skewXY
        self.printer.skewParams.skew['Y'] = skewYZ
        self.printer.skewParams.skew['Z'] = skewXZ

        cmd = self.printer.skewParams.generateM556()
        self.printer.execGcode(cmd)
        self.container.rawSkew = cmd.encode()

    def collectPoints(self):
        res = self.printer.defAxisU()
        res += self.printer.defAxisV()
        res += self.printer.defOrigin()
        res += self.printer.touchBed()
        self.calibrationData.points.extend(res)

    def printerMethod(self):
        # zeroing temporary adjustments
        self.printer.adjustParams.tempV = 0

        # set default parameters for delta, scale and skew
        self.printer.execGcode(self.printer.deltaParams.generateM665())
        self.printer.execGcode(self.printer.deltaParams.generateM666())
        self.printer.execGcode(self.printer.scaleParams.generateM579())
        self.printer.execGcode(self.printer.skewParams.generateM556())

        self.touchFixture()
        self.adjustBedIncline()
        self.calibrateDelta()
        self.calibrateScale()
        self.calibrateSkew()
        self.collectPoints()


class Step2(Step):
    textRu = (
        '<p>'
        'Шаг 2 из 3'
        '</p>'
        '<p>'
        'Отсоедините кабель калибровочной оснастки №1 от калибровочного'
        ' разъема 3Д принтера.'
        '</p>'
        '<p>'
        'Демонтируйте с рабочего стола калибровочную оснастку №1.'
        '</p>'
        '<p>'
        'Установите на рабочий стол калибровочную оснастку №2,'
        ' поставляемую в комплекте с 3Д принтером.'
        '</p>'
        '<p>'
        'Подсоедините кабель калибровочной оснастки №2 к калибровочному'
        ' разъему 3Д принтера.'
        '</p>'
        '<p>'
        'После нажатия кнопки <b>Далее</b> 3Д принтер начнёт выполнять'
        ' последовательность движений для сбора калибровочных данных.'
        '</p>'
    )

    textEn = (
        '<p>'
        'Step 2 of 3'
        '</p>'
        '<p>'
        'Please disconnect the calibration wire.'
        '</p>'
        '<p>'
        'Please unmount the fixture #1 from the bed.'
        '</p>'
        '<p>'
        'Please mount the fixture #2 to the bed.'
        '</p>'
        '<p>'
        'Please connect the calibration wire.'
        '</p>'
        '<p>'
        'Upon pressing  the <b>Next</b> button printer will'
        ' perform movements to collect the calibration data.'
        '</p>'
    )

    def collectPoints(self):
        res = self.printer.touchBed()
        X, Y, Z = res[0]
        # udjust Z by fixture #2 height
        Z -= self.container.fixture2Height
        self.calibrationData.points.append((X, Y, Z))

    def printerMethod(self):
        self.collectPoints()


class Step3(Step):
    textRu = (
        '<p>'
        'Шаг 3 из 3'
        '</p>'
        '<p>'
        'Демонтируйте специальный калибровочный модуль и установите на место'
        ' печатающую головку.'
        '</p>'
        '<p>'
        'После нажатия кнопки <b>Далее</b> 3Д принтер начнёт выполнять'
        ' последовательность движений для сбора калибровочных данных.'
        '</p>'
    )

    textEn = (
        '<p>'
        'Step 3 of 3'
        '</p>'
        '<p>'
        'Please unmount calibrating module and mount printing head back.'
        '</p>'
        '<p>'
        'Upon pressing  the <b>Next</b> button printer will'
        ' perform movements to collect the calibration data.'
        '</p>'
    )

    def collectPoints(self):
        res = self.printer.touchBed()
        X, Y, Z = res[0]
        # udjust Z by fixture #2 height
        Z -= self.container.fixture2Height
        self.calibrationData.points.append((X, Y, Z))

        # adjust printer height
        self.printer.deltaParams.readFromPrinter()
        self.printer.deltaParams.homedHeight -= Z

        cmds = self.printer.deltaParams.generateM665() + "\n"
        cmds += self.printer.deltaParams.generateM666()
        self.container.rawDelta = cmds.encode()

    def printerMethod(self):
        self.collectPoints()


class FinalStep(Step):
    textRu = (
        '<p>'
        'Сбор калибровочных данных успешно завершён.'
        '</p>'
        '<p>'
        'Отсоедините кабель калибровочной оснастки №2 от калибровочного'
        ' разъема 3Д принтера.'
        '</p>'
        '<p>'
        'Демонтируйте с рабочего стола калибровочную оснастку №2.'
        '</p>'
        '<p>'
        'Установите на рабочий стол калибровочную оснастку №2,'
        ' поставляемую в комплекте с 3Д принтером.'
        '</p>'
        '<p>'
        'Подсоедините кабель калибровочной оснастки №2 к калибровочному'
        ' разъему 3Д принтера.'
        '</p>'
        '<p>'
        'После нажатия кнопки <b>Завершить</b> будет создан новый'
        ' калибровочный файл для этого 3Д принтера.'
        '</p>'
    )

    textEn = (
        '<p>'
        'Calibration data collection finished successfully.'
        '</p>'
        '<p>'
        'Please disconnect the calibration wire.'
        '</p>'
        '<p>'
        'Please unmount the fixture #2 from the bed.'
        '</p>'
        '<p>'
        'Upon pressing  the <b>Finish</b> button a new calibration'
        ' file will be created for this printer.'
        '</p>'
    )

    def printerMethod(self):
        header = ';This file automatically generated by calibration tool\n'
        header = header.encode()

        # write the required files to printer
        self.printer.fileUpload(
            "0:/sys/delta.g", header + self.container.rawDelta)
        self.printer.fileUpload(
            "0:/sys/scale.g", header + self.container.rawScale)
        self.printer.fileUpload(
            "0:/sys/skew.g", header + self.container.rawSkew)
        self.printer.fileUpload(
            "0:/sys/adjustv.g", header + self.container.rawAdjustV)

        # write the last string of calibration_data.csv
        res = (self.printer.calibBallRadius, 0, 0)
        self.calibrationData.points.append(res)

        self.calibrationData.writeToFile('data\calibration_data.csv')
        print('calibration_data.csv created')
