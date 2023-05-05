import printer
from .data import CalibrationData

printer = printer.EpitPrinter()
printer.setOutputMethod(print)
printer.setStatusMethod(print)
calibrationData = CalibrationData()


class Step:
    def __init__(self, num, stepType='text'):
        self.num = num
        self.type = stepType
        self.setLang('ru')

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

    def action_template(self):
        points = printer.deltaCalibrator.collectPoints()
        pointsText = ""
        for num, point in points:
            x, y, z = point
            pointsText += f"Point {num}: X:{x:.3f} Y:{y:.3f} Z{z:.3f}\n"

        dialogText = ""
        "Please use the following data to ajust printer parameters at:\n"
        "https://escher3d.com/pages/wizards/wizarddelta.php\n"
        "\n"

        dialogText += pointsText
        dialogText += "\n"

        dialogText += printer.deltaCalibrator.deltaParams.toString()
        dialogText += "\n"

    def collectPoints(self):
        res = printer.defAxisU()
        res += printer.defAxisV()
        res += printer.defOrigin()
        calibrationData.points.extend(res)


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
        calibrationData.writeToFile('test.csv')
        print('test.csv created')


steps = [Step1, Step2, Step3, FinalStep]
