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

    def printerMethod(self):
        print('Printer method', self.num)


class Step1(Step):
    labelText = (
        '<p>'
        'Step 1 of 4'
        '</p>'
        '<p>'
        'This wizard is intended for collecting the'
        ' calibaration data of the Epit 3D printer.'
        '</p>'
        '<p>'
        '<b>!!!IMPORTANT!!!</b>'
        '<br>'
        'Please unmout the glass'
        ' from the bed. If this is not done at this'
        ' step, the nozzle may crash into the bed.'
        '</p>'
        '<p>'
        'Please mount the calibration ball instead'
        ' of the nozzle.'
        '</p>'
        '<p>'
        'Please connect the calibtation wire to the bed.'
        '</p>'
        '<p>'
        'Upon pressing  the <b>Next</b> button printer will'
        ' perform movements to collect the calibration data.'
        '<br>'
        '(Delta calibration)'
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


class Step2(Step):
    labelText = (
        '<p>'
        'Step 2 of 4'
        '</p>'
        '<p>'
        'Please mount the fixture #1 to the bed.'
        '</p>'
        '<p>'
        'Upon pressing  the <b>Next</b> button printer will'
        ' perform movements to collect the calibration data.'
        '<br>'
        '(Scale factor check, orthogonality check)'
        '</p>'
    )


class Step3(Step):
    labelText = (
        '<p>'
        'Step 3 of 4'
        '</p>'
        '<p>'
        'Please unmount the fixture #1 from the bed.'
        '</p>'
        '<p>'
        'Upon pressing  the <b>Next</b> button printer will'
        ' perform movements to collect the calibration data.'
        '<br>'
        '(U axis definition, V axis definition)'
        '</p>'
    )

    def action_template(self):
        res = printer.defAxisU()
        res += printer.defAxisV()
        calibrationData.points.extend(res)


class Step4(Step):
    labelText = (
        '<p>'
        'Step 4 of 4'
        '</p>'
        '<p>'
        'Please mount the fixture #2 to the bed.'
        '</p>'
        '<p>'
        'Upon pressing  the <b>Next</b> button printer will'
        ' perform movements to collect the calibration data.'
        '<br>'
        '(Origin definition)'
        '</p>'
    )

    def action_template(self):
        res = printer.defOrigin()
        calibrationData.points.extend(res)


class Step5(Step):
    labelText = (
        '<p>'
        'Calibration point collection finished successfully.'
        '</p>'
        '<p>'
        'Please unmount the fixture #2 from the bed.'
        '</p>'
        '<p>'
        'Please disconnect the calibtation wire from the bed.'
        '</p>'
        '<p>'
        'Please mount back the glass to the bed and'
        ' replace the calibration ball by nozzle.'
        '</p>'
        'Upon pressing  the <b>Finish</b> button a new calibration'
        ' file will be created for this printer.'
        '</p>'
    )

    def printerMethod(self):
        calibrationData.writeToFile('test.csv')
        print('test.csv created')


steps = [Step1, Step2, Step3, Step4, Step5]
