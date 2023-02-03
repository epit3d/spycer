from src.settings import sett


class Locale:
    LayerHeight = "Layer height, mm:"
    PrintSpeed = "Print speed, mm/s:"
    PrintSpeedLayer1 = "Print speed, Layer1, mm/s"
    PrintSpeedWall = "Print speed, walls, mm/s"
    ExtruderTemp = "Print temperature, °C:"
    BedTemp = "Bed temperature, °C:"
    FillDensity = "Fill density, %:"
    WallThickness = "Wall thickness, mm:"
    LineWidth = 'Line width, mm:'
    FillingType = 'Filling type:'
    FillingTypeValues = ["Lines", "Squares", "Triangles"]
    ShowStl = "Show stl"
    LayersCount = "Layers count:"
    OpenModel = "Open model"
    ColorModel = "Color triangles"
    MoveModel = "Move model"
    Slice3Axes = "Standard 3a slicing"
    SliceVip = "Vip slicing"
    SliceCone = "Slice cone"
    SaveGCode = "Save GCode"
    FanOffLayer1 = "Fan Off, Layer 1"
    Tilted = "Tilted"
    Hide = "Hide"
    Retraction = "Retraction"
    RetractionDistance = "Retraction Distance"
    RetractionSpeed = "Retraction Speed"
    SupportsOn = "Add supports"
    EditPlanes = "Edit"
    Analyze = "Analyze"
    AddPlane = "Add Plane"
    AddCone = "Add Cone"
    DeletePlane = "Delete"
    EditFigure = "Edit"
    Rotated = "Rotated"
    SupportOffset = "Support offset"
    FloatParsingError = "Error in float number"
    SkirtLineCount = "Skirt lines count"
    FanSpeed = "Fan Speed, %:"
    Plane = "Plane"
    AddOnePlaneError = "Add at least one plane"
    AddOneConeError = "Add at least one cone (it should be first in the list)"
    SmoothSlice = "Non planar 5d (Beta)"
    SmoothFlatSlice = "Non planar (Beta)"
    StlMoveTranslate = "Translate"
    StlMoveRotate = "Rotate"
    StlMoveScale = "Scale"
    ModelCentering = "Center model"
    SavePlanes = "Save planes"
    DownloadPlanes = "Download planes"
    NamePlanes = "Name"
    PrintTime = "Approximate print time: "
    ConsumptionMaterial = "Approximate consumption of material: "
    WarningNozzleAndTableCollision = "Attention! Threatening of the print head nozzle colliding with the table surface. Change the print settings. Critical planes: "
    Hour = "hr."
    Minute = "min."
    Second = "sec."
    Gram = "g."
    Meter = "m."

    def __init__(self, **entries):
        self.__dict__.update(entries)


dicts = {
    "en": Locale(),
    "ru": Locale(
        LayerHeight='Высота слоя, мм:',
        PrintSpeed='Скорость печати, мм/с:',
        PrintSpeedLayer1='Скорость печати первого слоя, мм/с',
        PrintSpeedWall='Скорость печати стенок, мм/с',
        ExtruderTemp='Температура печати, °C:',
        BedTemp='Температура стола, °C:',
        FillDensity='Плотность заполнения, %:',
        WallThickness='Толщина стенок, мм:',
        LineWidth='Ширина линии, мм:',
        ShowStl='Отображение STL модели',
        LayersCount='Отображаемые слои:',
        FillingType='Тип заполнения:',
        FillingTypeValues=["Линии", "Квадраты", "Треугольники"],
        OpenModel='Открыть модель',
        ColorModel='Подкрасить треугольники',
        MoveModel='Подвинуть модель',
        Slice='Нарезать на слои',
        Slice3Axes="Стандартная нарезка(3d)",
        SliceVip="Нарезка vip",
        SliceCone="Нарезка конусом",
        SaveGCode='Сохранить GCode',
        FanOffLayer1="Выключить вентилятор на первом слое",
        Retraction="Ретракция",
        RetractionDistance="Ретракция, Дистанция, мм",
        RetractionSpeed="Ретракция, Скорость, мм/с",
        Tilted='Наклонена',
        Hide='Скрыть',
        SupportsOn='Добавить поддержки',
        EditPlanes='Редактировать',
        Analyze='Анализировать',
        AddPlane="Добавить плоскость",
        AddCone="Добавить конус",
        DeletePlane="Удалить",
        EditFigure="Редактировать",
        Rotated="Повёрнута",
        SupportOffset="Отступ поддержки от детали",
        FloatParsingError="Ошибка в написании дробного числа",
        SkirtLineCount="Количество слоёв юбки",
        FanSpeed="Скорость вентилятора, %",
        Plane="Плоскость",
        AddOnePlaneError="Добавьте хотя бы одну плоскость",
        AddOneConeError="Первой фигурой должен быть конус",
        SmoothSlice="Непланарная 5d (Beta)",
        SmoothFlatSlice="Непланарная (Beta)",
        StlMoveTranslate="Перемещение",
        StlMoveRotate="Вращение",
        StlMoveScale="Масштабирование",
        ModelCentering = "Поместить модель в центр",
        SavePlanes = "Сохранить плоскости",
        DownloadPlanes = "Загрузить плоскости",
        NamePlanes = "Название",
        PrintTime = "Примерное время печати: ",
        ConsumptionMaterial = "Примерный расход материала: ",
        WarningNozzleAndTableCollision = "Внимание! Угроза столкновения сопла печатающей головки с поверхностью стола. Измените настройки печати. Критические плоскости: ",
        Hour = "час.",
        Minute = "мин.",
        Second = "сек.",
        Gram = "г.",
        Meter = "м.",
    ),
}


def getLocale():
    lang = sett().common.lang
    if lang in dicts:
        return dicts[lang]
    return dicts["en"]


def getLocaleByLang(lang):
    if lang in dicts:
        return dicts[lang]
    return dicts["en"]
