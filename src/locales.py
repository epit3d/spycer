import params


class Locale:
    Thickness = "Layer thickness, mm:"
    PrintSpeed = "Print speed, mm/s:"
    PrintSpeedLayer1 = "Print speed, Layer1, mm/s"
    PrintSpeedWall = "Print speed, walls, mm/s"
    ExtruderTemp = "Print temperature, °C:"
    BedTemp = "Bed temperature, °C:"
    FillDensity = "Fill density, %:"
    WallThickness = "Wall thickness, mm:"
    Nozzle = 'Nozzle diameter, mm:'
    FillingType = 'Filling type:'
    FillingTypeValues = ["Lines", "Squares", "Triangles"]
    ShowStl = "Show stl"
    LayersCount = "Layers count:"
    OpenModel = "Open model"
    ColorModel = "Color triangles"
    MoveModel = "Move model"
    Slice3Axes = "Standard 3a slicing"
    SliceVip = "Vip slicing"
    SaveGCode = "Save GCode"
    FanOffLayer1="Fan Off, Layer 1"
    Tilted = "Tilted"
    Retraction = "Retraction"
    RetractionDistance = "Retraction Distance"
    RetractionSpeed = "Retraction Speed"

    def __init__(self, **entries):
        self.__dict__.update(entries)


dicts = {
    "en": Locale(),
    "ru": Locale(
        Thickness='Толщина слоя, мм:',
        PrintSpeed='Скорость печати, мм/с:',
        PrintSpeedLayer1='Скорость печати первого слоя, мм/с',
        PrintSpeedWall='Скорость печати стенок, мм/с',
        ExtruderTemp='Температура печати, °C:',
        BedTemp='Температура стола, °C:',
        FillDensity='Плотность заполнения, %:',
        WallThickness='Толщина стенок, мм:',
        Nozzle='Диаметр сопла, мм:',
        ShowStl='Отображение STL модели',
        LayersCount='Отображаемые слои:',
        FillingType='Тип заполнения:',
        FillingTypeValues = ["Линии", "Квадраты", "Треугольники"],
        OpenModel='Открыть модель',
        ColorModel='Подкрасить треугольники',
        MoveModel='Подвинуть модель',
        Slice='Нарезать на слои',
        Slice3Axes="Стандартная нарезка(3о)",
        SliceVip="Нарезка vip",
        SaveGCode='Сохранить GCode',
        FanOffLayer1="Выключить вентилятор на первом слое",
        Retraction="Ретракция",
        RetractionDistance="Ретракция, Дистанция, мм",
        RetractionSpeed="Ретракция, Скорость, мм/с",
        Tilted='Наклонена',
    ),
}


def getLocale():
    if params.Lang in dicts:
        return dicts[params.Lang]
    return dicts["en"]


def getLocaleByLang(lang):
    if lang in dicts:
        return dicts[lang]
    return dicts["en"]