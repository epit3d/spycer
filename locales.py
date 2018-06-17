import params


class Locale:
    Thickness = "Layer thickness, mm:"
    TravelSpeed = "Travel speed, mm/s:"
    ExtruderTemp = "Print temperature, °C:"
    BedTemp = "Bed temperature, °C:"
    FillDensity = "Fill density, %:"
    WallThickness = "Wall thickness, mm:"
    ShowStl = "Show stl"
    LayersCount = "Layers count:"
    OpenModel = "Open model"
    Slice = "Slice!"
    SaveGCode = "Save GCode"
    SimplifyStl = "Simplify Stl"
    CutStl = "Cut Stl"

    def __init__(self, **entries):
        self.__dict__.update(entries)


dicts = {
    "en": Locale(),
    "ru": Locale(
        Thickness='Толщина слоя, мм:',
        TravelSpeed='Скорость движения, мм/с:',
        ExtruderTemp='Температура печати, °C:',
        BedTemp='Температура стола, °C:',
        FillDensity='Плотность заполнения, %:',
        WallThickness='Толщина стенок, мм:',
        ShowStl='Отображение STL модели',
        LayersCount='Отображаемые слои:',
        OpenModel='Открыть модель',
        Slice='Нарезать',
        SaveGCode='Сохранить GCode',
        SimplifyStl='Упростить модель',
        CutStl='Разрезать модель',
    ),
}


def getLocale():
    if params.Lang in dicts:
        return dicts[params.Lang]
    return dicts["en"]
