import params


class Locale:
    Thickness = "Layer thickness, mm:"
    PrintSpeed = "Print speed, mm/s:"
    ExtruderTemp = "Print temperature, °C:"
    BedTemp = "Bed temperature, °C:"
    FillDensity = "Fill density, %:"
    WallThickness = "Wall thickness, mm:"
    Nozzle = 'Nozzle diameter, mm:'
    ShowStl = "Show stl"
    LayersCount = "Layers count:"
    OpenModel = "Open model"
    ColorModel = "Color triangles"
    MoveModel = "Move model"
    Slice3Axes = "Standard 3a slicing"
    Slice5AxesByProfile = "5Axes slicing by profile"
    Slice5Axes = "5Axes slicing"
    SliceVip = "Vip slicing"
    SaveGCode = "Save GCode"
    SimplifyStl = "Simplify Stl"
    CutStl = "Cut Stl"
    ChangePlane = "Change plane"

    Tilted = "Tilted"

    def __init__(self, **entries):
        self.__dict__.update(entries)


dicts = {
    "en": Locale(),
    "ru": Locale(
        Thickness='Толщина слоя, мм:',
        PrintSpeed='Скорость печати, мм/с:',
        ExtruderTemp='Температура печати, °C:',
        BedTemp='Температура стола, °C:',
        FillDensity='Плотность заполнения, %:',
        WallThickness='Толщина стенок, мм:',
        Nozzle='Диаметр сопла, мм:',
        ShowStl='Отображение STL модели',
        LayersCount='Отображаемые слои:',
        OpenModel='Открыть модель',
        ColorModel='Подкрасить треугольники',
        MoveModel='Подвинуть модель',
        Slice='Нарезать на слои',
        Slice3Axes="Стандартная нарезка(3о)",
        Slice5AxesByProfile="Нарезать по профилю(5о)",
        Slice5Axes="Нарезка 5осевая",
        SliceVip="Нарезка vip",
        SaveGCode='Сохранить GCode',
        SimplifyStl='Упростить модель',
        CutStl='Разрезать модель',
        ChangePlane='Сменить плоскость',

        Tilted='Наклонена',
    ),
}


def getLocale():
    if params.Lang in dicts:
        return dicts[params.Lang]
    return dicts["en"]
