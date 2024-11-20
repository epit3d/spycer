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
    NumberWallLines = "Number of wall lines:"
    BottomThickness = "Bottom thickness:"
    NumberOfBottomLayers = "Number of bottom layers:"
    LidsThickness = "Lids thickness:"
    NumberOfLidLayers = "Number of lid layers:"
    LineWidth = "Extruder diameter, mm:"
    FillingType = "Filling type:"
    FillingTypeValues = ["Lines", "Squares", "Triangles", "Cross", "ZigZag"]
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
    SupportXYOffset = "Support XY offset, mm:"
    SupportZOffsetLayers = "Support Z offset, layers:"
    SupportPriorityZOffset = "Priority Z offset"
    FloatParsingError = "Error in float number"
    SkirtLineCount = "Skirt lines count:"
    FanSpeed = "Airflow amount, %:"
    Plane = "Plane"
    AddOnePlaneError = "Add at least one figure"
    AddOneConeError = "Add at least one cone (it should be first in the list)"
    # SmoothSlice = "Non planar 5d (Beta)"
    # SmoothFlatSlice = "Non planar (Beta)"
    StlMoveTranslate = "Translate"
    StlMoveRotate = "Rotate"
    StlMoveScale = "Scale"
    ModelCentering = "Center model"
    AlignModelHeight = "Attachment to the table"
    SavePlanes = "Save figures"
    DownloadPlanes = "Download figures"
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
    SaveProject = "Save project"
    SaveProjectAs = "Save project as..."
    SlicerInfo = "Slicer info"
    SlicerVersion = "Slicer version: "
    SlicingTitle = "Slicing"
    SlicingProgress = "Slicing is in progress..."
    GCodeLoadingTitle = "GCode loading"
    GCodeLoadingProgress = "GCode loading is in progress..."
    SupportsSettings = "Supports settings"
    MaterialShrinkage = "Material shrinkage, %:"
    FlowRate = "Flow rate, %:"
    PressureAdvance = "Pressure advance"
    PressureAdvanceValue = "Pressure advance value"
    ValueInBetween = "Value should be in range from {} to {}"
    ProjectManager = "FASP project manager"
    NewProject = "New project"
    ProjectDirectory = "Project directory:"
    ChooseProjectDirectory = "Choose project directory"
    ChooseFolder = "Choose folder"
    ProjectName = "Project name:"
    OpenProject = "Open project"
    RecentProjects = "Recent projects"
    ProjectNameCannotBeEmpty = "Project name cannot be empty"
    ProjectDirectoryCannotBeEmpty = "Project directory cannot be empty"
    ProjectAlreadyExists = "Project already exists"
    NoProjectSelected = "No project selected"
    Tools = "Tools"
    Calibration = "Calibration"
    SubmitBugReport = "Submit a bug report"
    SubmittingBugReport = "Submitting a bug report"
    ErrorDescription = "Error description:"
    AddImage = "Add image"
    Send = "Send"
    Cancel = "Cancel"
    Save = "Save"
    DontSave = "Don't save"
    Continue = "Continue"
    AddingImage = "Adding an image"
    ReportSubmitSuccessfully = "Report submit successfully. \nYou will be notified as soon as the problem is resolved. If necessary, our specialists will contact you for additional information. Thank you for helping us make the product better!"
    ErrorReport = "An error occurred while submitting the report"
    PlaceModelOnEdge = "Place the model on the edge"
    SavingProject = "Saving the project"
    ProjectSaved = "The project was successfully saved"
    ProjectChange = "The project has been changed. Save changes?"

    ErrorHardwareModule = "Hardware module is unavailable in public"
    ErrorBugModule = "Bug reporting is unavailable in public"

    PrinterName = "Printer name:"
    ChoosePrinterDirectory = "Choose printer name"
    AddNewPrinter = "Add new printer"
    DefaultPrinterWarn = "Be aware that you are using default printer. New data might be removed after update. We recommend to create new printer and calibrate it."
    CheckUpdates = "Check for updates"
    ProjectUpdate = "Project update"
    SettingsUpdate = "We want to update the project settings. Please check the values of the new fields. They will be set to default values."
    Update = "Update"
    EmptyDescription = "The error description cannot be empty"
    CalibrationDataWarning = (
        "You have not selected printer calibration data. Continue with default data?"
    )
    SelectingCalibrationData = "Selecting calibration data"

    UninterruptedPrint = "Uninterrupted print"
    M10CutDistance = "Filament cut distance, mm:"
    WarningPathNotClosed = "When cutting the model, not closed areas were found! Check that the shapes are positioned correctly"

    RemoveFirstPlaneError = "First figure cannot be removed"
    CannotDropHere = "Figure cannot be dropped here"

    ShouldCreateWalls = "Create wall in support"

    def __init__(self, **entries):
        self.__dict__.update(entries)


dicts = {
    "en": Locale(),
    "ru": Locale(
        LayerHeight="Высота слоя, мм:",
        PrintSpeed="Скорость печати, мм/с:",
        PrintSpeedLayer1="Скорость печати первого слоя, мм/с:",
        PrintSpeedWall="Скорость печати стенок, мм/с:",
        ExtruderTemp="Температура сопла, °C:",
        BedTemp="Температура стола, °C:",
        FillDensity="Плотность заполнения, %:",
        WallThickness="Толщина стенки:",
        NumberWallLines="Количество проходов стенки:",
        BottomThickness="Толщина дна:",
        NumberOfBottomLayers="Количество слоев дна:",
        LidsThickness="Толщина крышки:",
        NumberOfLidLayers="Количество слоев крышки:",
        LineWidth="Диаметр сопла, мм:",
        ShowStl="Отображение STL модели",
        LayersCount="Отображаемые слои:",
        FillingType="Тип заполнения:",
        FillingTypeValues=[
            "Линии",
            "Квадраты",
            "Треугольники",
            "Перекрёстное",
            "Зигзаг",
        ],
        OpenModel="Открыть модель",
        ColorModel="Выделить критические свесы",
        MoveModel="Передвинуть модель",
        Slice="Нарезать на слои",
        Slice3Axes="3D слайсинг",
        SliceVip="5D слайсинг",
        Settings="Настройки",
        # SliceCone="Конический слайсинг",
        SaveGCode="Сохранить GCode",
        FanOffLayer1="Выключить обдув на первом слое",
        Retraction="Ретракция",
        RetractionDistance="Величина ретракта, мм:",
        RetractionSpeed="Скорость ретракта, мм/с:",
        Tilted="Наклонена",
        Hide="Скрыть",
        SupportsOn="Добавить поддержки",
        # EditPlanes='Редактировать',
        # Analyze='Анализировать',
        AddPlane="Добавить плоскость",
        AddCone="Добавить конус",
        DeletePlane="Удалить",
        EditFigure="Редактировать",
        Rotated="Повёрнута",
        SupportXYOffset="Поддержки XY отступ, мм:",
        SupportZOffsetLayers="Поддержки Z отступ, слои:",
        SupportPriorityZOffset="Приоритет отступа по Z",
        FloatParsingError="Ошибка в написании дробного числа",
        SkirtLineCount="Количество линий юбки:",
        FanSpeed="Величина обдува детали, %:",
        Plane="Плоскость",
        AddOnePlaneError="Добавьте хотя бы одну фигуру",
        AddOneConeError="Первой фигурой должен быть конус",
        # SmoothSlice="Непланарная 5d (Beta)",
        # SmoothFlatSlice="Непланарная (Beta)",
        StlMoveTranslate="Перемещение",
        StlMoveRotate="Вращение",
        StlMoveScale="Масштабирование",
        ModelCentering="Поместить модель в центр",
        AlignModelHeight="Привязка к столу",
        SavePlanes="Сохранить фигуры",
        DownloadPlanes="Загрузить фигуры",
        NamePlanes="Название",
        PrintTime="Время печати:",
        ConsumptionMaterial="Расход материала:",
        WarningNozzleAndTableCollision="Внимание! Угроза столкновения сопла печатающей головки с поверхностью стола. Измените настройки печати. Критические плоскости: ",
        Hour="час.",
        Minute="мин.",
        Second="сек.",
        Gram="г.",
        Meter="м.",
        Millimeter="мм.",
        OverlappingInfillPercentage="Наложение заполнение-стенка, %:",
        CriticalWallOverhangAngle="Критический угол свеса стенки:",
        ModelCoordinates="Координаты модели",
        FigureSettings="Настройки фигуры",
        RetractCompensationAmount="Величина компенсации ретракта, мм:",
        SupportDensity="Плотность поддержек, %:",
        FileName="Имя файла: ",
        File="Файл",
        Open="Открыть",
        SaveSettings="Сохранить настройки",
        LoadSettings="Загрузить настройки",
        SaveProject="Сохранить проект",
        SaveProjectAs="Сохранить проект как...",
        SlicerInfo="Информация о слайсере",
        SlicerVersion="Версия слайсера: ",
        SlicingTitle="Слайсинг",
        SlicingProgress="Слайсинг в прогрессе...",
        GCodeLoadingTitle="Загрузка GCode",
        GCodeLoadingProgress="Загрузка GCode в прогрессе...",
        SupportsSettings="Настройки поддержек",
        MaterialShrinkage="Величина усадки материала, %:",
        FlowRate="Коэффициент потока расплава, %:",
        PressureAdvance="Управление давлением расплава",
        PressureAdvanceValue="Коэффициент управления давлением",
        ValueInBetween="Значение должно быть в диапазоне от {} до {}",
        ProjectManager="FASP менеджер проектов",
        NewProject="Новый проект",
        ProjectDirectory="Директория проекта:",
        ChooseProjectDirectory="Выберите директорию проекта",
        ChooseFolder="Выберите папку",
        ProjectName="Имя проекта:",
        OpenProject="Открыть проект",
        RecentProjects="Последние проекты",
        ProjectNameCannotBeEmpty="Имя проекта не может быть пустым",
        ProjectDirectoryCannotBeEmpty="Директория проекта не может быть пустой",
        ProjectAlreadyExists="Проект с таким именем уже существует",
        NoProjectSelected="Проект не выбран",
        Tools="Инструменты",
        Calibration="Калибровка",
        SubmitBugReport="Отправить сообщение об ошибке",
        SubmittingBugReport="Отправка сообщения об ошибке",
        ErrorDescription="Описание ошибки:",
        AddImage="Добавить изображение",
        Send="Отправить",
        Cancel="Отмена",
        Save="Сохранить",
        DontSave="Не сохранять",
        Continue="Продолжить",
        AddingImage="Выбрать изображение",
        ReportSubmitSuccessfully="Отчет успешно отправлен. \nВы будете уведомлены, как только проблема будет устранена. При необходимости, наши специалисты свяжутся с вами для получения дополнительной информации. Благодарим Вас, что помогаете нам сделать продукт лучше!",
        ErrorReport="Произошла ошибка при отправке отчета",
        PlaceModelOnEdge="Положить модель на грань",
        SavingProject="Сохранение проекта",
        ProjectSaved="Проект успешно сохранен",
        ProjectChange="Проект был изменен. Сохранить изменения?",
        ErrorHardwareModule="Модуль калибровки недоступен публично",
        ErrorBugModule="Модуль отправки багов недоступен публично",
        PrinterName="Конфигурация принтера:",
        ChoosePrinterDirectory="Выберите название принтера",
        AddNewPrinter="Добавить новый принтер",
        DefaultPrinterWarn="Будьте внимательны, Вы используете принтер по умолчанию. Данные этого принтера будут перезаписываться при обновлениях. Мы рекомендуем создать и использовать свою конфигурацию принтера.",
        CheckUpdates="Проверить наличие обновлений",
        ProjectUpdate="Обновление проекта",
        SettingsUpdate="Мы хотим обновить настройки проекта. Пожалуйста, проверьте значения новых полей. Они будут выставлены в значения по умолчанию.",
        Update="Обновить",
        EmptyDescription="Описание ошибки не может быть пустым",
        CalibrationDataWarning="Вы не выбрали калибровочные данные принтера. Продолжить с данными по умолчанию?",
        SelectingCalibrationData="Выбор калибровочных данных",
        UninterruptedPrint="Печать непрерывным волокном",
        M10CutDistance="Дистанция отреза филамента, мм:",
        RemoveFirstPlaneError="Первая фигура не может быть убрана",
        WarningPathNotClosed="При разрезании модели были обнаружены незамкнутые участки! Проверьте корректность расположения фигур",
        CannotDropHere="Фигура не может быть перенесена сюда",
        ShouldCreateWalls="Создавать стенки в поддержках",
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
