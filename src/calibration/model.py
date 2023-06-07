from .steps import StepsCollection


class CalibrationModel():
    mainLocales = dict(
        en=dict(
            window='Calibration',
            btnNext='Next',
            btnCancel='Cancel',
            btnFinish='Finish',
        ),
        ru=dict(
            window='Калибровка',
            btnNext='Далее',
            btnCancel='Отмена',
            btnFinish='Завершить',
        ),
    )

    def __init__(self, printer):
        self.steps = StepsCollection(printer)

        self.setLang('ru')

    def setLang(self, lang):
        if lang not in self.mainLocales.keys():
            lang = 'en'
        self.mainLocale = self.mainLocales[lang]

        self.steps.setLang(lang)

