from src.settings import sett


class Locale:
    LayerHeight = "Layer height, mm:"
    PrintSpeed = "Print speed, mm/s:"
    PrintSpeedLayer1 = "Print speed, Layer1, mm/s:"
    PrintSpeedWall = "Print speed, walls, mm/s:"
    ExtruderTemp = "Extruder temperature, °C:"
    BedTemp = "Bed temperature, °C:"
    FillDensity = "Fill density, %:"
    WallThickness = "Wall thickness:"
    NumberWallLines='Number of wall lines:'
    BottomThickness='Bottom thickness:'
    NumberOfBottomLayers='Number of bottom layers:'
    LidsThickness='Lid thickness:'
    NumberOfLidsLayers='Number of lid layers:'
    LineWidth = 'Extruder diameter, mm:'
    FillingType = 'Filling type:'
    FillingTypeValues = ["Lines", "Squares", "Triangles"]
    ShowStl = "Show stl"
    LayersCount = "Layers count:"
    OpenModel = "Open model"
    ColorModel = "Highlight critical overhangs"
    MoveModel = "Move model"
    Slice3Axes = "3D slicing"
    SliceVip = "5D slicing"
    Settings = "Settings"
    # SliceCone = "Slice cone"
    SaveGCode = "Save GCode"
    FanOffLayer1 = "Turn off airflow on the first layer"
    Tilted = "Tilted"
    Hide = "Hide"
    Retraction = "Retraction"
    RetractionDistance = "Retraction distance"
    RetractionSpeed = "Retraction speed"
    SupportsOn = "Add supports"
    # EditPlanes = "Edit"
    # Analyze = "Analyze"
    AddPlane = "Add Plane"
    AddCone = "Add Cone"
    DeletePlane = "Delete"
    EditFigure = "Edit"
    Rotated = "Rotated"
    SupportOffset = "Support offset, mm:"
    FloatParsingError = "Error in float number"
    SkirtLineCount = "Skirt lines count:"
    FanSpeed = "Airflow amount, %:"
    Plane = "Plane"
    AddOnePlaneError = "Add at least one plane"
    AddOneConeError = "Add at least one cone (it should be first in the list)"
    # SmoothSlice = "Non planar 5d (Beta)"
    # SmoothFlatSlice = "Non planar (Beta)"
    StlMoveTranslate = "Translate"
    StlMoveRotate = "Rotate"
    StlMoveScale = "Scale"
    ModelCentering = "Center model"
    AlignModelHeight = "Align model height"
    SavePlanes = "Save planes"
    DownloadPlanes = "Download planes"
    NamePlanes = "Name"
    PrintTime = "Print time:"
    ConsumptionMaterial = "Consumption of material:"
    WarningNozzleAndTableCollision = "Attention! Threatening of the print head nozzle colliding with the table surface. Change the print settings. Critical planes: "
    Hour = "hr."
    Minute = "min."
    Second = "sec."
    Gram = "g."
    Meter = "m."
    Millimeter = "mm."
    OverlappingInfillPercentage = "Fill-wall overlay, %:"
    CriticalWallOverhangAngle = "Critical wall overhang angle:"
    ModelCoordinates = "Model coordinates"
    FigureSettings = "Figure settings"
    RetractCompensationAmount = "Retract compensation amount, mm:"
    SupportDensity = "Support density, %:"
    FileName = "File name: "
    File = "File"
    Open = "Open"
    SaveSettings = "Save settings"
    LoadSettings = "Load settings"
    SlicingTitle = "Slicing"
    SlicingProgress = "Slicing is in progress..."
    GCodeLoadingTitle = "GCode loading"
    GCodeLoadingProgress = "GCode loading is in progress..."

    def __init__(self, **entries):
        self.__dict__.update(entries)


dicts = {
    "en": Locale(),
    "ru": Locale(
        LayerHeight='Высота слоя, мм:',
        PrintSpeed='Скорость печати, мм/с:',
        PrintSpeedLayer1='Скорость печати первого слоя, мм/с:',
        PrintSpeedWall='Скорость печати стенок, мм/с:',
        ExtruderTemp='Температура сопла, °C:',
        BedTemp='Температура стола, °C:',
        FillDensity='Плотность заполнения, %:',
        WallThickness='Толщина стенки:',
        NumberWallLines='Количество проходов стенки:',
        BottomThickness='Толщина дна:',
        NumberOfBottomLayers='Количество слоев дна:',
        LidThickness='Толщина крышки:',
        NumberOfLidLayers='Количество слоев крышки:',
        LineWidth='Диаметр сопла, мм:',
        ShowStl='Отображение STL модели',
        LayersCount='Отображаемые слои:',
        FillingType='Тип заполнения:',
        FillingTypeValues=["Линии", "Квадраты", "Треугольники"],
        OpenModel='Открыть модель',
        ColorModel='Выделить критические свесы',
        MoveModel='Передвинуть модель',
        Slice='Нарезать на слои',
        Slice3Axes="3D слайсинг",
        SliceVip="5D слайсинг",
        Settings = "Настройки",
        # SliceCone="Конический слайсинг",
        SaveGCode='Сохранить GCode',
        FanOffLayer1="Выключить обдув на первом слое",
        Retraction="Ретракция",
        RetractionDistance="Величина ретракта, мм:",
        RetractionSpeed="Скорость ретракта, мм/с:",
        Tilted='Наклонена',
        Hide='Скрыть',
        SupportsOn='Добавить поддержки',
        # EditPlanes='Редактировать',
        # Analyze='Анализировать',
        AddPlane="Добавить плоскость",
        AddCone="Добавить конус",
        DeletePlane="Удалить",
        EditFigure="Редактировать",
        Rotated="Повёрнута",
        SupportOffset="Отступ поддержки от детали, мм:",
        FloatParsingError="Ошибка в написании дробного числа",
        SkirtLineCount="Количество линий юбки:",
        FanSpeed="Величина обдува детали, %:",
        Plane="Плоскость",
        AddOnePlaneError="Добавьте хотя бы одну плоскость",
        AddOneConeError="Первой фигурой должен быть конус",
        # SmoothSlice="Непланарная 5d (Beta)",
        # SmoothFlatSlice="Непланарная (Beta)",
        StlMoveTranslate="Перемещение",
        StlMoveRotate="Вращение",
        StlMoveScale="Масштабирование",
        ModelCentering = "Поместить модель в центр",
        AlignModelHeight = "Выровнять модель по высоте",
        SavePlanes = "Сохранить плоскости",
        DownloadPlanes = "Загрузить плоскости",
        NamePlanes = "Название",
        PrintTime = "Время печати:",
        ConsumptionMaterial = "Расход материала:",
        WarningNozzleAndTableCollision = "Внимание! Угроза столкновения сопла печатающей головки с поверхностью стола. Измените настройки печати. Критические плоскости: ",
        Hour = "час.",
        Minute = "мин.",
        Second = "сек.",
        Gram = "г.",
        Meter = "м.",
        Millimeter = "мм.",
        OverlappingInfillPercentage = "Наложение заполнение-стенка, %:",
        CriticalWallOverhangAngle = "Критический угол свеса стенки:",
        ModelCoordinates = "Координаты модели",
        FigureSettings = "Настройки фигуры",
        RetractCompensationAmount = "Величина компенсации ретракта, мм:",
        SupportDensity = "Плотность поддержек, %:",
        FileName = "Имя файла: ",
        File = "Файл",
        Open = "Открыть",
        SaveSettings = "Сохранить настройки",
        LoadSettings = "Загрузить настройки",
        SlicingTitle = "Слайсинг",
        SlicingProgress = "Слайсинг в прогрессе...",
        GCodeLoadingTitle = "Загрузка GCode",
        GCodeLoadingProgress = "Загрузка GCode в прогрессе...",
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
