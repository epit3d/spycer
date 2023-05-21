import math
import printer
from .data import CalibrationData
from .reprapfirmware_lsq import Tuner


class Container:
    rawDelta = b''
    rawScale = b''
    rawSkew = b''
    rawAdjustV = b''


class StepsCollection:
    def __init__(self):
        self.printer = printer.EpitPrinter()
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

    def adjustBedIncline(self):
        tangent = self.printer.defBedIncline()
        angle = math.degrees(math.atan(tangent))
        cmds = [
            "G91",
            f"G0 V{angle}",
            "G92 V0",
            "G90",
        ]
        for cmd in cmds:
            self.printer.execGcode(cmd)
        self.container.rawAdjustV = "\n".join(cmds)

    def calibrateDelta(self):
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
        res = self.printer.defDelta(points=points)
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

        self.container.rawDelta = '/n'.join(cmds).encode()

    def calibrateScale(self):
        nominalX = 105
        nominalY = 105
        nominalZ = 63

        realX = self.printer.measureScaleX()
        realY = self.printer.measureScaleY()
        realZ = self.printer.measureScaleZ()

        self.printer.scaleParams.scale['X'] = nominalX / realX
        self.printer.scaleParams.scale['Y'] = nominalY / realY
        self.printer.scaleParams.scale['Z'] = nominalZ / realZ

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

        cmd = self.printer.scaleParams.generateM556()
        self.printer.execGcode(cmd)
        self.container.rawSkew = cmd.encode()

    def collectPoints(self):
        res = self.printer.defAxisU()
        res += self.printer.defAxisV()
        res += self.printer.defOrigin()
        res += self.printer.touchBed()
        self.calibrationData.points.extend(res)

    def printerMethod(self):
        # set default parameters for delta, scale and skew
        self.printer.runGcode(self.printer.deltaParams.generateM665())
        self.printer.runGcode(self.printer.deltaParams.generateM666())
        self.printer.runGcode(self.printer.scaleParams.generateM579())
        self.printer.runGcode(self.printer.skewParams.generateM556())

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
        self.calibrationData.points.extend(res)

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
        self.calibrationData.points.extend(res)

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
        # write the required files to printer
        self.printer.fileUpload("0:/sys/delta.g", self.container.rawDelta)
        self.printer.fileUpload("0:/sys/scale.g", self.container.rawScale)
        self.printer.fileUpload("0:/sys/skew.g", self.container.rawSkew)
        self.printer.fileUpload("0:/sys/adjustV.g", self.container.rawAdjustV)

        # write the last string of calibration_data.csv
        res = (self.printer.calibBallRadius, 0, 0)
        self.calibrationData.points.append(res)

        self.calibrationData.writeToFile('data\calibration_data.csv')
        print('calibration_data.csv created')
