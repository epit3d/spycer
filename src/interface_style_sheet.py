import qdarkstyle

def getStyleSheet():
    # Loading the style so that can get pictures from the link
    darkstyle = qdarkstyle.load_stylesheet()

    border_color = "#455364"
    text_color = "#E0E1E3"
    disabled_text_color = "#9DA9B5"
    hover_string_color = "#37414F"
    hover_color = "#54687A"
    main_background_color = "#0e1621"
    pressed_button_color = "#5fbdce"
    menu_color = "#242f3d"
    button_color = "#04859d"
    button_disabled_color = "#455364"
    button_text_color = "#E0E1E3"
    button_disabled_text_color = "#9DA9B5"
    button_hover_color = "#17adbf"
    background_color = button_hover_color
    selected_line_color = button_color
    selected_element_color = button_color

    border_radius = "3"
    check_box_height = "16"
    button_height = "25"
    button_padding = "2px 5px 2px 5px"

    font_size = "13px"
    font_type = "ROBOTO"
    font = font_size + " " + font_type
    header_view_font = "14px " + font_type
    button_font = "bold 15px " + font_type
    menu_font = "14px " + font_type

    style_sheet = f"""
    * {{
        padding: 0px;
        margin: 0px;
        border: 0px;
        border-style: none;
        border-image: none;
        outline: 0;
        font: {font};
    }}

    /* specific reset for elements inside QToolBar */
    QToolBar * {{
        margin: 0px;
        padding: 0px;
    }}

    /* QWidget ---------------------------------------------------------------- */

    QWidget {{
        background-color: {main_background_color};
        border: 0px solid {border_color};
        padding: 0px;
        color: {text_color};
        selection-background-color: {selected_line_color};
        selection-color: {text_color};
    }}

    QWidget:disabled {{
        background-color: {main_background_color};
        color: {disabled_text_color};
        selection-background-color: {background_color};
        selection-color: {disabled_text_color};
    }}

    QWidget::item:selected {{
        background-color: {selected_line_color};
    }}

    QWidget::item:hover:!selected {{
        background-color: {selected_element_color};
    }}

    /* QMainWindow ------------------------------------------------------------ */
    QMainWindow::separator {{
        background-color: {border_color};
        border: 0px solid {main_background_color};
        spacing: 0px;
        padding: 2px;
    }}

    QMainWindow::separator:hover {{
        background-color: {pressed_button_color};
        border: 0px solid {selected_element_color};
    }}

    QMainWindow::separator:horizontal {{
        width: 5px;
        margin-top: 2px;
        margin-bottom: 2px;
        image: url(":/qss_icons/dark/rc/toolbar_separator_vertical.png");
    }}

    QMainWindow::separator:vertical {{
        height: 5px;
        margin-left: 2px;
        margin-right: 2px;
        image: url(":/qss_icons/dark/rc/toolbar_separator_horizontal.png");
    }}

    /* QToolTip --------------------------------------------------------------- */
    QToolTip {{
        background-color: {selected_line_color};
        color: {text_color};
        border: none;
        padding: 0px;
    }}

    /* QStatusBar ------------------------------------------------------------- */
    QStatusBar {{
        border: 1px solid {border_color};
        background: {border_color};
    }}

    QStatusBar::item {{
        border: none;
    }}

    QStatusBar QToolTip {{
        background-color: {selected_element_color};
        border: 1px solid {main_background_color};
        color: {main_background_color};
        padding: 0px;
        opacity: 230;
    }}

    QStatusBar QLabel {{
        background: transparent;
    }}

    /* QCheckBox -------------------------------------------------------------- */
    QCheckBox {{
        background-color: {main_background_color};
        color: {text_color};
        spacing: 4px;
        outline: none;
        padding-top: 4px;
        padding-bottom: 4px;
    }}

    QCheckBox:focus {{
        border: none;
    }}

    QCheckBox QWidget:disabled {{
        background-color: {main_background_color};
        color: {disabled_text_color};
    }}

    QCheckBox::indicator {{
        margin-left: 2px;
        height: {check_box_height}px;
        width: {check_box_height}px;
    }}

    QCheckBox::indicator:unchecked {{
        image: url(":/qss_icons/dark/rc/checkbox_unchecked.png");
    }}

    QCheckBox::indicator:unchecked:hover, QCheckBox::indicator:unchecked:focus, QCheckBox::indicator:unchecked:pressed {{
        border: none;
        image: url(":/qss_icons/dark/rc/checkbox_unchecked_focus.png");
    }}

    QCheckBox::indicator:unchecked:disabled {{
        image: url(":/qss_icons/dark/rc/checkbox_unchecked_disabled.png");
    }}

    QCheckBox::indicator:checked {{
        image: url(":/qss_icons/dark/rc/checkbox_checked.png");
    }}

    QCheckBox::indicator:checked:hover, QCheckBox::indicator:checked:focus, QCheckBox::indicator:checked:pressed {{
        border: none;
        image: url(":/qss_icons/dark/rc/checkbox_checked_focus.png");
    }}

    QCheckBox::indicator:checked:disabled {{
        image: url(":/qss_icons/dark/rc/checkbox_checked_disabled.png");
    }}

    QCheckBox::indicator:indeterminate {{
        image: url(":/qss_icons/dark/rc/checkbox_indeterminate.png");
    }}

    QCheckBox::indicator:indeterminate:disabled {{
        image: url(":/qss_icons/dark/rc/checkbox_indeterminate_disabled.png");
    }}

    QCheckBox::indicator:indeterminate:focus, QCheckBox::indicator:indeterminate:hover, QCheckBox::indicator:indeterminate:pressed {{
        image: url(":/qss_icons/dark/rc/checkbox_indeterminate_focus.png");
    }}

    /* QGroupBox -------------------------------------------------------------- */
    QGroupBox {{
        font-weight: bold;
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
        padding: 2px;
        margin-top: 6px;
        margin-bottom: 4px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 4px;
        padding-left: 2px;
        padding-right: 4px;
        padding-top: -4px;
    }}

    QGroupBox::indicator {{
        margin-left: 2px;
        margin-top: 2px;
        padding: 0;
        height: 14px;
        width: 14px;
    }}

    QGroupBox::indicator:unchecked {{
        border: none;
        image: url(":/qss_icons/dark/rc/checkbox_unchecked.png");
    }}

    QGroupBox::indicator:unchecked:hover, QGroupBox::indicator:unchecked:focus, QGroupBox::indicator:unchecked:pressed {{
        border: none;
        image: url(":/qss_icons/dark/rc/checkbox_unchecked_focus.png");
    }}

    QGroupBox::indicator:unchecked:disabled {{
        image: url(":/qss_icons/dark/rc/checkbox_unchecked_disabled.png");
    }}

    QGroupBox::indicator:checked {{
        border: none;
        image: url(":/qss_icons/dark/rc/checkbox_checked.png");
    }}

    QGroupBox::indicator:checked:hover, QGroupBox::indicator:checked:focus, QGroupBox::indicator:checked:pressed {{
        border: none;
        image: url(":/qss_icons/dark/rc/checkbox_checked_focus.png");
    }}

    QGroupBox::indicator:checked:disabled {{
        image: url(":/qss_icons/dark/rc/checkbox_checked_disabled.png");
    }}

    /* QRadioButton ----------------------------------------------------------- */
    QRadioButton {{
        background-color: {main_background_color};
        color: {text_color};
        spacing: 4px;
        padding-top: 4px;
        padding-bottom: 4px;
        border: none;
        outline: none;
    }}

    QRadioButton:focus {{
        border: none;
    }}

    QRadioButton:disabled {{
        background-color: {main_background_color};
        color: {disabled_text_color};
        border: none;
        outline: none;
    }}

    QRadioButton QWidget {{
        background-color: {main_background_color};
        color: {text_color};
        spacing: 0px;
        padding: 0px;
        outline: none;
        border: none;
    }}

    QRadioButton::indicator {{
        border: none;
        outline: none;
        margin-left: 2px;
        height: 14px;
        width: 14px;
    }}

    QRadioButton::indicator:unchecked {{
        image: url(":/qss_icons/dark/rc/radio_unchecked.png");
    }}

    QRadioButton::indicator:unchecked:hover, QRadioButton::indicator:unchecked:focus, QRadioButton::indicator:unchecked:pressed {{
        border: none;
        outline: none;
        image: url(":/qss_icons/dark/rc/radio_unchecked_focus.png");
    }}

    QRadioButton::indicator:unchecked:disabled {{
        image: url(":/qss_icons/dark/rc/radio_unchecked_disabled.png");
    }}

    QRadioButton::indicator:checked {{
        border: none;
        outline: none;
        image: url(":/qss_icons/dark/rc/radio_checked.png");
    }}

    QRadioButton::indicator:checked:hover, QRadioButton::indicator:checked:focus, QRadioButton::indicator:checked:pressed {{
        border: none;
        outline: none;
        image: url(":/qss_icons/dark/rc/radio_checked_focus.png");
    }}

    QRadioButton::indicator:checked:disabled {{
        outline: none;
        image: url(":/qss_icons/dark/rc/radio_checked_disabled.png");
    }}

    /* QMenuBar --------------------------------------------------------------- */
    QMenuBar {{
        background-color: {menu_color};
        padding: 2px;
        border: 1px solid {main_background_color};
        color: {text_color};
        selection-background-color: {selected_element_color};
        font: {menu_font};
    }}

    QMenuBar:focus {{
        border: 1px solid {selected_line_color};
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 4px;
    }}

    QMenuBar::item:selected {{
        padding: 4px;
        background: transparent;
        border: 0px solid {border_color};
        background-color: {selected_element_color};
    }}

    QMenuBar::item:pressed {{
        padding: 4px;
        border: 0px solid {border_color};
        background-color: {selected_element_color};
        color: {text_color};
        margin-bottom: 0px;
        padding-bottom: 0px;
    }}

    /* QMenu ------------------------------------------------------------------ */
    QMenu {{
        border: 0px solid {menu_color};
        color: {text_color};
        margin: 0px;
        background-color: {hover_string_color};
        selection-background-color: {selected_element_color};
        font: {menu_font};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {pressed_button_color};
        color: {text_color};
    }}

    QMenu::item {{
        background-color: {hover_string_color};
        padding: 4px 24px 4px 28px;
        border: 1px transparent {border_color};
    }}

    QMenu::item:selected {{
        color: {text_color};
        background-color: {selected_element_color};
    }}

    QMenu::item:pressed {{
        background-color: {selected_element_color};
    }}

    QMenu::icon {{
        padding-left: 10px;
        width: 14px;
        height: 14px;
    }}

    QMenu::indicator {{
        padding-left: 8px;
        width: 12px;
        height: 12px;
    }}

    QMenu::indicator:non-exclusive:unchecked {{
        image: url(":/qss_icons/dark/rc/checkbox_unchecked.png");
    }}

    QMenu::indicator:non-exclusive:unchecked:hover, QMenu::indicator:non-exclusive:unchecked:focus, QMenu::indicator:non-exclusive:unchecked:pressed {{
        border: none;
        image: url(":/qss_icons/dark/rc/checkbox_unchecked_focus.png");
    }}

    QMenu::indicator:non-exclusive:unchecked:disabled {{
        image: url(":/qss_icons/dark/rc/checkbox_unchecked_disabled.png");
    }}

    QMenu::indicator:non-exclusive:checked {{
        image: url(":/qss_icons/dark/rc/checkbox_checked.png");
    }}

    QMenu::indicator:non-exclusive:checked:hover, QMenu::indicator:non-exclusive:checked:focus, QMenu::indicator:non-exclusive:checked:pressed {{
        border: none;
        image: url(":/qss_icons/dark/rc/checkbox_checked_focus.png");
    }}

    QMenu::indicator:non-exclusive:checked:disabled {{
        image: url(":/qss_icons/dark/rc/checkbox_checked_disabled.png");
    }}

    QMenu::indicator:non-exclusive:indeterminate {{
        image: url(":/qss_icons/dark/rc/checkbox_indeterminate.png");
    }}

    QMenu::indicator:non-exclusive:indeterminate:disabled {{
        image: url(":/qss_icons/dark/rc/checkbox_indeterminate_disabled.png");
    }}

    QMenu::indicator:non-exclusive:indeterminate:focus, QMenu::indicator:non-exclusive:indeterminate:hover, QMenu::indicator:non-exclusive:indeterminate:pressed {{
        image: url(":/qss_icons/dark/rc/checkbox_indeterminate_focus.png");
    }}

    QMenu::indicator:exclusive:unchecked {{
        image: url(":/qss_icons/dark/rc/radio_unchecked.png");
    }}

    QMenu::indicator:exclusive:unchecked:hover, QMenu::indicator:exclusive:unchecked:focus, QMenu::indicator:exclusive:unchecked:pressed {{
        border: none;
        outline: none;
        image: url(":/qss_icons/dark/rc/radio_unchecked_focus.png");
    }}

    QMenu::indicator:exclusive:unchecked:disabled {{
        image: url(":/qss_icons/dark/rc/radio_unchecked_disabled.png");
    }}

    QMenu::indicator:exclusive:checked {{
        border: none;
        outline: none;
        image: url(":/qss_icons/dark/rc/radio_checked.png");
    }}

    QMenu::indicator:exclusive:checked:hover, QMenu::indicator:exclusive:checked:focus, QMenu::indicator:exclusive:checked:pressed {{
        border: none;
        outline: none;
        image: url(":/qss_icons/dark/rc/radio_checked_focus.png");
    }}

    QMenu::indicator:exclusive:checked:disabled {{
        outline: none;
        image: url(":/qss_icons/dark/rc/radio_checked_disabled.png");
    }}

    QMenu::right-arrow {{
        margin: 5px;
        padding-left: 12px;
        image: url(":/qss_icons/dark/rc/arrow_right.png");
        height: 12px;
        width: 12px;
    }}

    /* QAbstractItemView ------------------------------------------------------ */
    QAbstractItemView {{
        alternate-background-color: {main_background_color};
        color: {text_color};
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
    }}

    QAbstractItemView QLineEdit {{
        padding: 2px;
    }}

    /* QAbstractScrollArea ---------------------------------------------------- */
    QAbstractScrollArea {{
        background-color: {main_background_color};
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
        padding: 2px;
        color: {text_color};
    }}

    QAbstractScrollArea:disabled {{
        color: {disabled_text_color};
    }}

    /* QScrollArea ------------------------------------------------------------ */
    QScrollArea QWidget QWidget:disabled {{
        background-color: {main_background_color};
    }}

    /* QScrollBar ------------------------------------------------------------- */
    QScrollBar:horizontal {{
        height: 16px;
        margin: 2px 16px 2px 16px;
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
        background-color: {main_background_color};
    }}

    QScrollBar:vertical {{
        background-color: {main_background_color};
        width: 16px;
        margin: 16px 2px 16px 2px;
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {pressed_button_color};
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
        min-width: 8px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {selected_line_color};
        border: {selected_line_color};
        border-radius: {border_radius}px;
        min-width: 8px;
    }}

    QScrollBar::handle:horizontal:focus {{
        border: 1px solid {selected_element_color};
    }}

    QScrollBar::handle:vertical {{
        background-color: {pressed_button_color};
        border: 1px solid {border_color};
        min-height: 8px;
        border-radius: {border_radius}px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {selected_line_color};
        border: {selected_line_color};
        border-radius: {border_radius}px;
        min-height: 8px;
    }}

    QScrollBar::handle:vertical:focus {{
        border: 1px solid {selected_element_color};
    }}

    QScrollBar::add-line:horizontal {{
        margin: 0px 0px 0px 0px;
        border-image: url(":/qss_icons/dark/rc/arrow_right_disabled.png");
        height: 12px;
        width: 12px;
        subcontrol-position: right;
        subcontrol-origin: margin;
    }}

    QScrollBar::add-line:horizontal:hover, QScrollBar::add-line:horizontal:on {{
        border-image: url(":/qss_icons/dark/rc/arrow_right.png");
        height: 12px;
        width: 12px;
        subcontrol-position: right;
        subcontrol-origin: margin;
    }}

    QScrollBar::add-line:vertical {{
        margin: 3px 0px 3px 0px;
        border-image: url(":/qss_icons/dark/rc/arrow_down_disabled.png");
        height: 12px;
        width: 12px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }}

    QScrollBar::add-line:vertical:hover, QScrollBar::add-line:vertical:on {{
        border-image: url(":/qss_icons/dark/rc/arrow_down.png");
        height: 12px;
        width: 12px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }}

    QScrollBar::sub-line:horizontal {{
        margin: 0px 3px 0px 3px;
        border-image: url(":/qss_icons/dark/rc/arrow_left_disabled.png");
        height: 12px;
        width: 12px;
        subcontrol-position: left;
        subcontrol-origin: margin;
    }}

    QScrollBar::sub-line:horizontal:hover, QScrollBar::sub-line:horizontal:on {{
        border-image: url(":/qss_icons/dark/rc/arrow_left.png");
        height: 12px;
        width: 12px;
        subcontrol-position: left;
        subcontrol-origin: margin;
    }}

    QScrollBar::sub-line:vertical {{
        margin: 3px 0px 3px 0px;
        border-image: url(":/qss_icons/dark/rc/arrow_up_disabled.png");
        height: 12px;
        width: 12px;
        subcontrol-position: top;
        subcontrol-origin: margin;
    }}

    QScrollBar::sub-line:vertical:hover, QScrollBar::sub-line:vertical:on {{
        border-image: url(":/qss_icons/dark/rc/arrow_up.png");
        height: 12px;
        width: 12px;
        subcontrol-position: top;
        subcontrol-origin: margin;
    }}

    QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal {{
        background: none;
    }}

    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
        background: none;
    }}

    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    /* QTextEdit -------------------------------------------------------------- */
    QTextEdit {{
        background-color: {main_background_color};
        color: {text_color};
        border-radius: {border_radius}px;
        border: 1px solid {border_color};
    }}

    QTextEdit:focus {{
        border: 1px solid {selected_element_color};
    }}

    QTextEdit:selected {{
        background: {selected_line_color};
        color: {border_color};
    }}

    /* QPlainTextEdit --------------------------------------------------------- */
    QPlainTextEdit {{
        background-color: {main_background_color};
        color: {text_color};
        border-radius: {border_radius}px;
        border: 1px solid {border_color};
    }}

    QPlainTextEdit:focus {{
        border: 1px solid {selected_element_color};
    }}

    QPlainTextEdit:selected {{
        background: {selected_line_color};
        color: {border_color};
    }}

    /* QSizeGrip -------------------------------------------------------------- */
    QSizeGrip {{
        background: transparent;
        width: 12px;
        height: 12px;
        image: url(":/qss_icons/dark/rc/window_grip.png");
    }}

    /* QStackedWidget --------------------------------------------------------- */
    QStackedWidget {{
        padding: 2px;
        border: 1px solid {border_color};
        border: 1px solid {main_background_color};
    }}

    /* QToolBar --------------------------------------------------------------- */
    QToolBar {{
        background-color: {border_color};
        border-bottom: 1px solid {main_background_color};
        padding: 1px;
        font-weight: bold;
        spacing: 2px;
    }}

    QToolBar:disabled {{
        background-color: {border_color};
    }}

    QToolBar::handle:horizontal {{
        width: 16px;
        image: url(":/qss_icons/dark/rc/toolbar_move_horizontal.png");
    }}

    QToolBar::handle:vertical {{
        height: 16px;
        image: url(":/qss_icons/dark/rc/toolbar_move_vertical.png");
    }}

    QToolBar::separator:horizontal {{
        width: 16px;
        image: url(":/qss_icons/dark/rc/toolbar_separator_horizontal.png");
    }}

    QToolBar::separator:vertical {{
        height: 16px;
        image: url(":/qss_icons/dark/rc/toolbar_separator_vertical.png");
    }}

    QToolButton#qt_toolbar_ext_button {{
        background: {border_color};
        border: 0px;
        color: {text_color};
        image: url(":/qss_icons/dark/rc/arrow_right.png");
    }}

    /* QAbstractSpinBox ------------------------------------------------------- */
    QAbstractSpinBox {{
        background-color: {main_background_color};
        border: 1px solid {border_color};
        color: {text_color};
        padding-top: 2px;
        padding-bottom: 2px;
        padding-left: 4px;
        padding-right: 4px;
        border-radius: {border_radius}px;
    }}

    QAbstractSpinBox:up-button {{
        background-color: transparent {main_background_color};
        subcontrol-origin: border;
        subcontrol-position: top right;
        border-left: 1px solid {border_color};
        border-bottom: 1px solid {border_color};
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
        margin: 1px;
        width: 12px;
        margin-bottom: -1px;
    }}

    QAbstractSpinBox::up-arrow, QAbstractSpinBox::up-arrow:disabled, QAbstractSpinBox::up-arrow:off {{
        image: url(":/qss_icons/dark/rc/arrow_up_disabled.png");
        height: 8px;
        width: 8px;
    }}

    QAbstractSpinBox::up-arrow:hover {{
        image: url(":/qss_icons/dark/rc/arrow_up.png");
    }}

    QAbstractSpinBox:down-button {{
        background-color: transparent {main_background_color};
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        border-left: 1px solid {border_color};
        border-top: 1px solid {border_color};
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
        margin: 1px;
        width: 12px;
        margin-top: -1px;
    }}

    QAbstractSpinBox::down-arrow, QAbstractSpinBox::down-arrow:disabled, QAbstractSpinBox::down-arrow:off {{
        image: url(":/qss_icons/dark/rc/arrow_down_disabled.png");
        height: 8px;
        width: 8px;
    }}

    QAbstractSpinBox::down-arrow:hover {{
        image: url(":/qss_icons/dark/rc/arrow_down.png");
    }}

    QAbstractSpinBox:hover {{
        border: 1px solid {selected_line_color};
        color: {text_color};
    }}

    QAbstractSpinBox:focus {{
        border: 1px solid {selected_element_color};
    }}

    QAbstractSpinBox:selected {{
        background: {selected_line_color};
        color: {border_color};
    }}

    /* DISPLAYS --------------------------------------------------------------- */
    /* QLabel ----------------------------------------------------------------- */
    QLabel {{
        background-color: {main_background_color};
        border: 0px solid {border_color};
        padding: 2px;
        margin: 0px;
        color: {text_color};
    }}

    QLabel:disabled {{
        background-color: {main_background_color};
        border: 0px solid {border_color};
        color: {disabled_text_color};
    }}

    /* QTextBrowser ----------------------------------------------------------- */
    QTextBrowser {{
        background-color: {main_background_color};
        border: 1px solid {border_color};
        color: {text_color};
        border-radius: {border_radius}px;
    }}

    QTextBrowser:disabled {{
        background-color: {main_background_color};
        border: 1px solid {border_color};
        color: {disabled_text_color};
        border-radius: {border_radius}px;
    }}

    QTextBrowser:hover, QTextBrowser:!hover, QTextBrowser:selected, QTextBrowser:pressed {{
        border: 1px solid {border_color};
    }}

    /* QGraphicsView ---------------------------------------------------------- */
    QGraphicsView {{
        background-color: {main_background_color};
        border: 1px solid {border_color};
        color: {text_color};
        border-radius: {border_radius}px;
    }}

    QGraphicsView:disabled {{
        background-color: {main_background_color};
        border: 1px solid {border_color};
        color: {disabled_text_color};
        border-radius: {border_radius}px;
    }}

    QGraphicsView:hover, QGraphicsView:!hover, QGraphicsView:selected, QGraphicsView:pressed {{
        border: 1px solid {border_color};
    }}

    /* QCalendarWidget -------------------------------------------------------- */
    QCalendarWidget {{
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
    }}

    QCalendarWidget:disabled {{
        background-color: {main_background_color};
        color: {disabled_text_color};
    }}

    /* QLCDNumber ------------------------------------------------------------- */
    QLCDNumber {{
        background-color: {main_background_color};
        color: {text_color};
    }}

    QLCDNumber:disabled {{
        background-color: {main_background_color};
        color: {disabled_text_color};
    }}

    /* QProgressBar ----------------------------------------------------------- */
    QProgressBar {{
        background-color: {main_background_color};
        border: 1px solid {border_color};
        color: {text_color};
        border-radius: {border_radius}px;
        text-align: center;
    }}

    QProgressBar:disabled {{
        background-color: {main_background_color};
        border: 1px solid {border_color};
        color: {disabled_text_color};
        border-radius: {border_radius}px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {selected_line_color};
        color: {main_background_color};
        border-radius: {border_radius}px;
    }}

    QProgressBar::chunk:disabled {{
        background-color: {background_color};
        color: {disabled_text_color};
        border-radius: {border_radius}px;
    }}

    /* BUTTONS ---------------------------------------------------------------- */
    /* QPushButton ------------------------------------------------------------ */
    QPushButton {{
        background-color: {button_color};
        color: {button_text_color};
        border-radius: {border_radius}px;
        padding: {button_padding};
        outline: none;
        border: none;
        height: {button_height}px;
        font: {button_font};
    }}

    QPushButton:disabled {{
        background-color: {button_disabled_color};
        color: {button_disabled_text_color};
        border-radius: {border_radius}px;
        padding: {button_padding};
    }}

    QPushButton:checked {{
        background-color: {pressed_button_color};
        border-radius: {border_radius}px;
        padding: {button_padding};
        outline: none;
    }}

    QPushButton:checked:disabled {{
        background-color: {pressed_button_color};
        color: {button_disabled_text_color};
        border-radius: {border_radius}px;
        padding: {button_padding};
        outline: none;
    }}

    QPushButton:checked:selected {{
        background: {pressed_button_color};
    }}

    QPushButton:hover {{
        background-color: {button_hover_color};
        color: {button_text_color};
    }}

    QPushButton:pressed {{
        background-color: {pressed_button_color};
    }}

    QPushButton:selected {{
        background: {pressed_button_color};
        color: {button_text_color};
    }}

    QPushButton::menu-indicator {{
        subcontrol-origin: padding;
        subcontrol-position: bottom right;
        bottom: 4px;
    }}

    QDialogButtonBox QPushButton {{
        min-width: 80px;
    }}

    /* QToolButton ------------------------------------------------------------ */
    QToolButton {{
        background-color: {border_color};
        color: {text_color};
        border-radius: {border_radius}px;
        padding: 2px;
        outline: none;
        border: none;
    }}

    QToolButton:disabled {{
        background-color: {border_color};
        color: {disabled_text_color};
        border-radius: {border_radius}px;
        padding: 2px;
    }}

    QToolButton:checked {{
        background-color: {pressed_button_color};
        border-radius: {border_radius}px;
        padding: 2px;
        outline: none;
    }}

    QToolButton:checked:disabled {{
        background-color: {pressed_button_color};
        color: {disabled_text_color};
        border-radius: {border_radius}px;
        padding: 2px;
        outline: none;
    }}

    QToolButton:checked:hover {{
        background-color: {hover_color};
        color: {text_color};
    }}

    QToolButton:checked:pressed {{
        background-color: {pressed_button_color};
    }}

    QToolButton:checked:selected {{
        background: {pressed_button_color};
        color: {text_color};
    }}

    QToolButton:hover {{
        background-color: {hover_color};
        color: {text_color};
    }}

    QToolButton:pressed {{
        background-color: {pressed_button_color};
    }}

    QToolButton:selected {{
        background: {pressed_button_color};
        color: {text_color};
    }}

    QToolButton[popupMode="0"] {{
        padding-right: 2px;
    }}

    QToolButton[popupMode="1"] {{
        padding-right: 20px;
    }}

    QToolButton[popupMode="1"]::menu-button {{
        border: none;
    }}

    QToolButton[popupMode="1"]::menu-button:hover {{
        border: none;
        border-left: 1px solid {border_color};
        border-radius: 0;
    }}

    QToolButton[popupMode="2"] {{
        padding-right: 2px;
    }}

    QToolButton::menu-button {{
        padding: 2px;
        border-radius: {border_radius}px;
        width: 12px;
        border: none;
        outline: none;
    }}

    QToolButton::menu-button:hover {{
        border: 1px solid {selected_line_color};
    }}

    QToolButton::menu-button:checked:hover {{
        border: 1px solid {selected_line_color};
    }}

    QToolButton::menu-indicator {{
        image: url(":/qss_icons/dark/rc/arrow_down.png");
        height: 8px;
        width: 8px;
        top: 0;
        left: -2px;
    }}

    QToolButton::menu-arrow {{
        image: url(":/qss_icons/dark/rc/arrow_down.png");
        height: 8px;
        width: 8px;
    }}

    QToolButton::menu-arrow:hover {{
        image: url(":/qss_icons/dark/rc/arrow_down_focus.png");
    }}

    /* QCommandLinkButton ----------------------------------------------------- */
    QCommandLinkButton {{
        background-color: transparent;
        border: 1px solid {border_color};
        color: {text_color};
        border-radius: {border_radius}px;
        padding: 0px;
        margin: 0px;
    }}

    QCommandLinkButton:disabled {{
        background-color: transparent;
        color: {disabled_text_color};
    }}

    /* INPUTS - NO FIELDS ----------------------------------------------------- */
    /* QComboBox -------------------------------------------------------------- */
    QComboBox {{
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
        selection-background-color: {selected_line_color};
        padding-left: 4px;
        padding-right: 4px;
        min-height: 1.5em;
    }}

    QComboBox QAbstractItemView {{
        border: 1px solid {border_color};
        border-radius: 0;
        background-color: {main_background_color};
        selection-background-color: {selected_line_color};
    }}

    QComboBox QAbstractItemView:hover {{
        background-color: {main_background_color};
        color: {text_color};
    }}

    QComboBox QAbstractItemView:selected {{
        background: {selected_line_color};
        color: {border_color};
    }}

    QComboBox QAbstractItemView:alternate {{
        background: {main_background_color};
    }}

    QComboBox:disabled {{
        background-color: {main_background_color};
        color: {disabled_text_color};
    }}

    QComboBox:hover {{
        border: 1px solid {selected_line_color};
    }}

    QComboBox:focus {{
        border: 1px solid {selected_element_color};
    }}

    QComboBox:on {{
        selection-background-color: {selected_line_color};
    }}

    QComboBox::indicator {{
        border: none;
        border-radius: 0;
        background-color: transparent;
        selection-background-color: transparent;
        color: transparent;
        selection-color: transparent;
    }}

    QComboBox::indicator:alternate {{
        background: {main_background_color};
    }}

    QComboBox::item {{
        /*&:checked {{
                    font-weight: bold;
            }}

                &:selected {{
                    border: 0px solid transparent;
            }}
                */
    }}

    QComboBox::item:alternate {{
        background: {main_background_color};
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 12px;
        border-left: 1px solid {border_color};
    }}

    QComboBox::down-arrow {{
        image: url(":/qss_icons/dark/rc/arrow_down_disabled.png");
        height: 8px;
        width: 8px;
    }}

    QComboBox::down-arrow:on, QComboBox::down-arrow:hover, QComboBox::down-arrow:focus {{
        image: url(":/qss_icons/dark/rc/arrow_down.png");
    }}

    /* QSlider ---------------------------------------------------------------- */
    QSlider:disabled {{
        background: {main_background_color};
    }}

    QSlider:focus {{
        border: none;
    }}

    QSlider::groove:horizontal {{
        background: {border_color};
        border: 1px solid {border_color};
        height: 4px;
        margin: 0px;
        border-radius: {border_radius}px;
    }}

    QSlider::groove:vertical {{
        background: {border_color};
        border: 1px solid {border_color};
        width: 4px;
        margin: 0px;
        border-radius: {border_radius}px;
    }}

    QSlider::add-page:vertical {{
        background: {selected_line_color};
        border: 1px solid {border_color};
        width: 4px;
        margin: 0px;
        border-radius: {border_radius}px;
    }}

    QSlider::add-page:vertical :disabled {{
        background: {background_color};
    }}

    QSlider::sub-page:horizontal {{
        background: {selected_line_color};
        border: 1px solid {border_color};
        height: 4px;
        margin: 0px;
        border-radius: {border_radius}px;
    }}

    QSlider::sub-page:horizontal:disabled {{
        background: {background_color};
    }}

    QSlider::handle:horizontal {{
        background: {disabled_text_color};
        border: 1px solid {border_color};
        width: 8px;
        height: 8px;
        margin: -8px 0px;
        border-radius: {border_radius}px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {selected_line_color};
        border: 1px solid {selected_line_color};
    }}

    QSlider::handle:horizontal:focus {{
        border: 1px solid {selected_element_color};
    }}

    QSlider::handle:vertical {{
        background: {disabled_text_color};
        border: 1px solid {border_color};
        width: 8px;
        height: 8px;
        margin: 0 -8px;
        border-radius: {border_radius}px;
    }}

    QSlider::handle:vertical:hover {{
        background: {selected_line_color};
        border: 1px solid {selected_line_color};
    }}

    QSlider::handle:vertical:focus {{
        border: 1px solid {selected_element_color};
    }}

    /* QLineEdit -------------------------------------------------------------- */
    QLineEdit {{
        background-color: {main_background_color};
        padding-top: 2px;
        padding-bottom: 2px;
        padding-left: 4px;
        padding-right: 4px;
        border-style: solid;
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
        color: {text_color};
    }}

    QLineEdit:disabled {{
        background-color: {main_background_color};
        color: {disabled_text_color};
    }}

    QLineEdit:hover {{
        border: 1px solid {selected_line_color};
        color: {text_color};
    }}

    QLineEdit:focus {{
        border: 1px solid {selected_element_color};
    }}

    QLineEdit:selected {{
        background-color: {selected_line_color};
        color: {border_color};
    }}

    /* QTabWiget -------------------------------------------------------------- */
    QTabWidget {{
        padding: 2px;
        selection-background-color: {border_color};
    }}

    QTabWidget QWidget {{
        border-radius: {border_radius}px;
    }}

    QTabWidget::pane {{
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
        margin: 0px;
        padding: 0px;
    }}

    QTabWidget::pane:selected {{
        background-color: {border_color};
        border: 1px solid {selected_line_color};
    }}

    /* QTabBar ---------------------------------------------------------------- */
    QTabBar, QDockWidget QTabBar {{
    Qproperty-drawBase: 0;
        border-radius: {border_radius}px;
        margin: 0px;
        padding: 2px;
        border: 0;
    }}

    QTabBar::close-button, QDockWidget QTabBar::close-button {{
        border: 0;
        margin: 0;
        padding: 4px;
        image: url(":/qss_icons/dark/rc/window_close.png");
    }}

    QTabBar::close-button:hover, QDockWidget QTabBar::close-button:hover {{
        image: url(":/qss_icons/dark/rc/window_close_focus.png");
    }}

    QTabBar::close-button:pressed, QDockWidget QTabBar::close-button:pressed {{
        image: url(":/qss_icons/dark/rc/window_close_pressed.png");
    }}

    QTabBar::tab, QDockWidget QTabBar::tab {{
    }}

    QTabBar::tab:top:selected:disabled, QDockWidget QTabBar::tab:top:selected:disabled {{
        border-bottom: 3px solid {background_color};
        color: {disabled_text_color};
        background-color: {border_color};
    }}

    QTabBar::tab:bottom:selected:disabled, QDockWidget QTabBar::tab:bottom:selected:disabled {{
        border-top: 3px solid {background_color};
        color: {disabled_text_color};
        background-color: {border_color};
    }}

    QTabBar::tab:left:selected:disabled, QDockWidget QTabBar::tab:left:selected:disabled {{
        border-right: 3px solid {background_color};
        color: {disabled_text_color};
        background-color: {border_color};
    }}

    QTabBar::tab:right:selected:disabled, QDockWidget QTabBar::tab:right:selected:disabled {{
        border-left: 3px solid {background_color};
        color: {disabled_text_color};
        background-color: {border_color};
    }}

    QTabBar::tab:top:!selected:disabled, QDockWidget QTabBar::tab:top:!selected:disabled {{
        border-bottom: 3px solid {main_background_color};
        color: {disabled_text_color};
        background-color: {main_background_color};
    }}

    QTabBar::tab:bottom:!selected:disabled, QDockWidget QTabBar::tab:bottom:!selected:disabled {{
        border-top: 3px solid {main_background_color};
        color: {disabled_text_color};
        background-color: {main_background_color};
    }}

    QTabBar::tab:left:!selected:disabled, QDockWidget QTabBar::tab:left:!selected:disabled {{
        border-right: 3px solid {main_background_color};
        color: {disabled_text_color};
        background-color: {main_background_color};
    }}

    QTabBar::tab:right:!selected:disabled, QDockWidget QTabBar::tab:right:!selected:disabled {{
        border-left: 3px solid {main_background_color};
        color: {disabled_text_color};
        background-color: {main_background_color};
    }}

    QTabBar::tab:top:!selected, QDockWidget QTabBar::tab:top:!selected {{
        border-bottom: 2px solid {main_background_color};
        margin-top: 2px;
    }}

    QTabBar::tab:bottom:!selected, QDockWidget QTabBar::tab:bottom:!selected {{
        border-top: 2px solid {main_background_color};
        margin-bottom: 2px;
    }}

    QTabBar::tab:left:!selected, QDockWidget QTabBar::tab:left:!selected {{
        border-left: 2px solid {main_background_color};
        margin-right: 2px;
    }}

    QTabBar::tab:right:!selected, QDockWidget QTabBar::tab:right:!selected {{
        border-right: 2px solid {main_background_color};
        margin-left: 2px;
    }}

    QTabBar::tab:top, QDockWidget QTabBar::tab:top {{
        background-color: {border_color};
        margin-left: 2px;
        padding-left: 4px;
        padding-right: 4px;
        padding-top: 2px;
        padding-bottom: 2px;
        min-width: 5px;
        border-bottom: 3px solid {border_color};
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}

    QTabBar::tab:top:selected, QDockWidget QTabBar::tab:top:selected {{
        background-color: {hover_color};
        border-bottom: 3px solid #259AE9;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}

    QTabBar::tab:top:!selected:hover, QDockWidget QTabBar::tab:top:!selected:hover {{
        border: 1px solid {selected_element_color};
        border-bottom: 3px solid {selected_element_color};
        padding-left: 3px;
        padding-right: 3px;
    }}

    QTabBar::tab:bottom, QDockWidget QTabBar::tab:bottom {{
        border-top: 3px solid {border_color};
        background-color: {border_color};
        margin-left: 2px;
        padding-left: 4px;
        padding-right: 4px;
        padding-top: 2px;
        padding-bottom: 2px;
        border-bottom-left-radius: 4px;
        border-bottom-right-radius: 4px;
        min-width: 5px;
    }}

    QTabBar::tab:bottom:selected, QDockWidget QTabBar::tab:bottom:selected {{
        background-color: {hover_color};
        border-top: 3px solid #259AE9;
        border-bottom-left-radius: 4px;
        border-bottom-right-radius: 4px;
    }}

    QTabBar::tab:bottom:!selected:hover, QDockWidget QTabBar::tab:bottom:!selected:hover {{
        border: 1px solid {selected_element_color};
        border-top: 3px solid {selected_element_color};
        padding-left: 3px;
        padding-right: 3px;
    }}

    QTabBar::tab:left, QDockWidget QTabBar::tab:left {{
        background-color: {border_color};
        margin-top: 2px;
        padding-left: 2px;
        padding-right: 2px;
        padding-top: 4px;
        padding-bottom: 4px;
        border-top-left-radius: 4px;
        border-bottom-left-radius: 4px;
        min-height: 5px;
    }}

    QTabBar::tab:left:selected, QDockWidget QTabBar::tab:left:selected {{
        background-color: {hover_color};
        border-right: 3px solid #259AE9;
    }}

    QTabBar::tab:left:!selected:hover, QDockWidget QTabBar::tab:left:!selected:hover {{
        border: 1px solid {selected_element_color};
        border-right: 3px solid {selected_element_color};
        margin-right: 0px;
        padding-right: -1px;
    }}

    QTabBar::tab:right, QDockWidget QTabBar::tab:right {{
        background-color: {border_color};
        margin-top: 2px;
        padding-left: 2px;
        padding-right: 2px;
        padding-top: 4px;
        padding-bottom: 4px;
        border-top-right-radius: 4px;
        border-bottom-right-radius: 4px;
        min-height: 5px;
    }}

    QTabBar::tab:right:selected, QDockWidget QTabBar::tab:right:selected {{
        background-color: {hover_color};
        border-left: 3px solid #259AE9;
    }}

    QTabBar::tab:right:!selected:hover, QDockWidget QTabBar::tab:right:!selected:hover {{
        border: 1px solid {selected_element_color};
        border-left: 3px solid {selected_element_color};
        margin-left: 0px;
        padding-left: 0px;
    }}

    QTabBar QToolButton, QDockWidget QTabBar QToolButton {{
        background-color: {border_color};
        height: 12px;
        width: 12px;
    }}

    QTabBar QToolButton:pressed, QDockWidget QTabBar QToolButton:pressed {{
        background-color: {border_color};
    }}

    QTabBar QToolButton:pressed:hover, QDockWidget QTabBar QToolButton:pressed:hover {{
        border: 1px solid {selected_line_color};
    }}

    QTabBar QToolButton::left-arrow:enabled, QDockWidget QTabBar QToolButton::left-arrow:enabled {{
        image: url(":/qss_icons/dark/rc/arrow_left.png");
    }}

    QTabBar QToolButton::left-arrow:disabled, QDockWidget QTabBar QToolButton::left-arrow:disabled {{
        image: url(":/qss_icons/dark/rc/arrow_left_disabled.png");
    }}

    QTabBar QToolButton::right-arrow:enabled, QDockWidget QTabBar QToolButton::right-arrow:enabled {{
        image: url(":/qss_icons/dark/rc/arrow_right.png");
    }}

    QTabBar QToolButton::right-arrow:disabled, QDockWidget QTabBar QToolButton::right-arrow:disabled {{
        image: url(":/qss_icons/dark/rc/arrow_right_disabled.png");
    }}

    /* QDockWiget ------------------------------------------------------------- */
    QDockWidget {{
        outline: 1px solid {border_color};
        background-color: {main_background_color};
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
        titlebar-close-icon: url(":/qss_icons/dark/rc/transparent.png");
        titlebar-normal-icon: url(":/qss_icons/dark/rc/transparent.png");
    }}

    QDockWidget::title {{
        padding: 3px;
        spacing: 4px;
        border: none;
        background-color: {border_color};
    }}

    QDockWidget::close-button {{
        icon-size: 12px;
        border: none;
        background: transparent;
        background-image: transparent;
        border: 0;
        margin: 0;
        padding: 0;
        image: url(":/qss_icons/dark/rc/window_close.png");
    }}

    QDockWidget::close-button:hover {{
        image: url(":/qss_icons/dark/rc/window_close_focus.png");
    }}

    QDockWidget::close-button:pressed {{
        image: url(":/qss_icons/dark/rc/window_close_pressed.png");
    }}

    QDockWidget::float-button {{
        icon-size: 12px;
        border: none;
        background: transparent;
        background-image: transparent;
        border: 0;
        margin: 0;
        padding: 0;
        image: url(":/qss_icons/dark/rc/window_undock.png");
    }}

    QDockWidget::float-button:hover {{
        image: url(":/qss_icons/dark/rc/window_undock_focus.png");
    }}

    QDockWidget::float-button:pressed {{
        image: url(":/qss_icons/dark/rc/window_undock_pressed.png");
    }}

    /* QTreeView QListView QTableView ----------------------------------------- */
    QTreeView:branch:selected, QTreeView:branch:hover {{
        background: url(":/qss_icons/dark/rc/transparent.png");
    }}

    QTreeView:branch:has-siblings:!adjoins-item {{
        border-image: url(":/qss_icons/dark/rc/branch_line.png") 0;
    }}

    QTreeView:branch:has-siblings:adjoins-item {{
        border-image: url(":/qss_icons/dark/rc/branch_more.png") 0;
    }}

    QTreeView:branch:!has-children:!has-siblings:adjoins-item {{
        border-image: url(":/qss_icons/dark/rc/branch_end.png") 0;
    }}

    QTreeView:branch:has-children:!has-siblings:closed, QTreeView:branch:closed:has-children:has-siblings {{
        border-image: none;
        image: url(":/qss_icons/dark/rc/branch_closed.png");
    }}

    QTreeView:branch:open:has-children:!has-siblings, QTreeView:branch:open:has-children:has-siblings {{
        border-image: none;
        image: url(":/qss_icons/dark/rc/branch_open.png");
    }}

    QTreeView:branch:has-children:!has-siblings:closed:hover, QTreeView:branch:closed:has-children:has-siblings:hover {{
        image: url(":/qss_icons/dark/rc/branch_closed_focus.png");
    }}

    QTreeView:branch:open:has-children:!has-siblings:hover, QTreeView:branch:open:has-children:has-siblings:hover {{
        image: url(":/qss_icons/dark/rc/branch_open_focus.png");
    }}

    QTreeView::indicator:checked,
    QListView::indicator:checked,
    QTableView::indicator:checked,
    QColumnView::indicator:checked {{
        image: url(":/qss_icons/dark/rc/checkbox_checked.png");
    }}

    QTreeView::indicator:checked:hover, QTreeView::indicator:checked:focus, QTreeView::indicator:checked:pressed,
    QListView::indicator:checked:hover,
    QListView::indicator:checked:focus,
    QListView::indicator:checked:pressed,
    QTableView::indicator:checked:hover,
    QTableView::indicator:checked:focus,
    QTableView::indicator:checked:pressed,
    QColumnView::indicator:checked:hover,
    QColumnView::indicator:checked:focus,
    QColumnView::indicator:checked:pressed {{
        image: url(":/qss_icons/dark/rc/checkbox_checked_focus.png");
    }}

    QTreeView::indicator:unchecked,
    QListView::indicator:unchecked,
    QTableView::indicator:unchecked,
    QColumnView::indicator:unchecked {{
        image: url(":/qss_icons/dark/rc/checkbox_unchecked.png");
    }}

    QTreeView::indicator:unchecked:hover, QTreeView::indicator:unchecked:focus, QTreeView::indicator:unchecked:pressed,
    QListView::indicator:unchecked:hover,
    QListView::indicator:unchecked:focus,
    QListView::indicator:unchecked:pressed,
    QTableView::indicator:unchecked:hover,
    QTableView::indicator:unchecked:focus,
    QTableView::indicator:unchecked:pressed,
    QColumnView::indicator:unchecked:hover,
    QColumnView::indicator:unchecked:focus,
    QColumnView::indicator:unchecked:pressed {{
        image: url(":/qss_icons/dark/rc/checkbox_unchecked_focus.png");
    }}

    QTreeView::indicator:indeterminate,
    QListView::indicator:indeterminate,
    QTableView::indicator:indeterminate,
    QColumnView::indicator:indeterminate {{
        image: url(":/qss_icons/dark/rc/checkbox_indeterminate.png");
    }}

    QTreeView::indicator:indeterminate:hover, QTreeView::indicator:indeterminate:focus, QTreeView::indicator:indeterminate:pressed,
    QListView::indicator:indeterminate:hover,
    QListView::indicator:indeterminate:focus,
    QListView::indicator:indeterminate:pressed,
    QTableView::indicator:indeterminate:hover,
    QTableView::indicator:indeterminate:focus,
    QTableView::indicator:indeterminate:pressed,
    QColumnView::indicator:indeterminate:hover,
    QColumnView::indicator:indeterminate:focus,
    QColumnView::indicator:indeterminate:pressed {{
        image: url(":/qss_icons/dark/rc/checkbox_indeterminate_focus.png");
    }}

    QTreeView,
    QListView,
    QTableView,
    QColumnView {{
        background-color: {main_background_color};
        border: 1px solid {border_color};
        color: {text_color};
        gridline-color: {border_color};
        border-radius: {border_radius}px;
    }}

    QTreeView:disabled,
    QListView:disabled,
    QTableView:disabled,
    QColumnView:disabled {{
        background-color: {main_background_color};
        color: {disabled_text_color};
    }}

    QTreeView:selected,
    QListView:selected,
    QTableView:selected,
    QColumnView:selected {{
        background-color: {selected_line_color};
        color: {border_color};
    }}

    QTreeView:focus,
    QListView:focus,
    QTableView:focus,
    QColumnView:focus {{
        border: 1px solid {selected_element_color};
    }}

    QTreeView::item:pressed,
    QListView::item:pressed,
    QTableView::item:pressed,
    QColumnView::item:pressed {{
        background-color: {selected_line_color};
    }}

    QTreeView::item:selected:active,
    QListView::item:selected:active,
    QTableView::item:selected:active,
    QColumnView::item:selected:active {{
        background-color: {selected_line_color};
    }}

    QTreeView::item:selected:!active,
    QListView::item:selected:!active,
    QTableView::item:selected:!active,
    QColumnView::item:selected:!active {{
        color: {text_color};
        background-color: {hover_string_color};
    }}

    QTreeView::item:!selected:hover,
    QListView::item:!selected:hover,
    QTableView::item:!selected:hover,
    QColumnView::item:!selected:hover {{
        outline: 0;
        color: {text_color};
        background-color: {hover_string_color};
    }}

    QTableCornerButton::section {{
        background-color: {main_background_color};
        border: 1px transparent {border_color};
        border-radius: 0px;
    }}

    /* QHeaderView ------------------------------------------------------------ */
    QHeaderView {{
        background-color: {border_color};
        border: 0px transparent {border_color};
        padding: 0;
        margin: 0;
        border-radius: 0;
    }}

    QHeaderView:disabled {{
        background-color: {border_color};
        border: 1px transparent {border_color};
    }}

    QHeaderView::section {{
        background-color: {border_color};
        color: {text_color};
        border-radius: 0;
        text-align: left;
        font: {header_view_font};
    }}

    QHeaderView::section::horizontal {{
        padding-top: 0;
        padding-bottom: 0;
        padding-left: 4px;
        padding-right: 4px;
        border-left: 1px solid {main_background_color};
    }}

    QHeaderView::section::horizontal::first, QHeaderView::section::horizontal::only-one {{
        border-left: 1px solid {border_color};
    }}

    QHeaderView::section::horizontal:disabled {{
        color: {disabled_text_color};
    }}

    QHeaderView::section::vertical {{
        padding-top: 0;
        padding-bottom: 0;
        padding-left: 4px;
        padding-right: 4px;
        border-top: 1px solid {main_background_color};
    }}

    QHeaderView::section::vertical::first, QHeaderView::section::vertical::only-one {{
        border-top: 1px solid {border_color};
    }}

    QHeaderView::section::vertical:disabled {{
        color: {disabled_text_color};
    }}

    QHeaderView::down-arrow {{
        background-color: {border_color};
        border: none;
        height: 12px;
        width: 12px;
        padding-left: 2px;
        padding-right: 2px;
        image: url(":/qss_icons/dark/rc/arrow_down.png");
    }}

    QHeaderView::up-arrow {{
        background-color: {border_color};
        border: none;
        height: 12px;
        width: 12px;
        padding-left: 2px;
        padding-right: 2px;
        image: url(":/qss_icons/dark/rc/arrow_up.png");
    }}

    /* QToolBox -------------------------------------------------------------- */
    QToolBox {{
        padding: 0px;
        border: 0px;
        border: 1px solid {border_color};
    }}

    QToolBox:selected {{
        padding: 0px;
        border: 2px solid {selected_line_color};
    }}

    QToolBox::tab {{
        background-color: {main_background_color};
        border: 1px solid {border_color};
        color: {text_color};
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}

    QToolBox::tab:disabled {{
        color: {disabled_text_color};
    }}

    QToolBox::tab:selected {{
        background-color: {pressed_button_color};
        border-bottom: 2px solid {selected_line_color};
    }}

    QToolBox::tab:selected:disabled {{
        background-color: {border_color};
        border-bottom: 2px solid {background_color};
    }}

    QToolBox::tab:!selected {{
        background-color: {border_color};
        border-bottom: 2px solid {border_color};
    }}

    QToolBox::tab:!selected:disabled {{
        background-color: {main_background_color};
    }}

    QToolBox::tab:hover {{
        border-color: {selected_element_color};
        border-bottom: 2px solid {selected_element_color};
    }}

    QToolBox QScrollArea QWidget QWidget {{
        padding: 0px;
        border: 0px;
        background-color: {main_background_color};
    }}

    /* QFrame ----------------------------------------------------------------- */
    .QFrame {{
        border-radius: {border_radius}px;
        border: 1px solid {border_color};
    }}

        .QFrame[frameShape="0"] {{
        border-radius: {border_radius}px;
        border: 1px transparent {border_color};
    }}

        .QFrame[frameShape="4"] {{
        max-height: 2px;
        border: none;
        background-color: {border_color};
    }}

        .QFrame[frameShape="5"] {{
        max-width: 2px;
        border: none;
        background-color: {border_color};
    }}

    /* QSplitter -------------------------------------------------------------- */
    QSplitter {{
        background-color: {border_color};
        spacing: 0px;
        padding: 0px;
        margin: 0px;
    }}

    QSplitter::handle {{
        background-color: {border_color};
        border: 0px solid {main_background_color};
        spacing: 0px;
        padding: 1px;
        margin: 0px;
    }}

    QSplitter::handle:hover {{
        background-color: {disabled_text_color};
    }}

    QSplitter::handle:horizontal {{
        width: 5px;
        image: url(":/qss_icons/dark/rc/line_vertical.png");
    }}

    QSplitter::handle:vertical {{
        height: 5px;
        image: url(":/qss_icons/dark/rc/line_horizontal.png");
    }}

    /* QDateEdit, QDateTimeEdit ----------------------------------------------- */
    QDateEdit, QDateTimeEdit {{
        selection-background-color: {selected_line_color};
        border-style: solid;
        border: 1px solid {border_color};
        border-radius: {border_radius}px;
        padding-top: 2px;
        padding-bottom: 2px;
        padding-left: 4px;
        padding-right: 4px;
        min-width: 10px;
    }}

    QDateEdit:on, QDateTimeEdit:on {{
        selection-background-color: {selected_line_color};
    }}

    QDateEdit::drop-down, QDateTimeEdit::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 12px;
        border-left: 1px solid {border_color};
    }}

    QDateEdit::down-arrow, QDateTimeEdit::down-arrow {{
        image: url(":/qss_icons/dark/rc/arrow_down_disabled.png");
        height: 8px;
        width: 8px;
    }}

    QDateEdit::down-arrow:on, QDateEdit::down-arrow:hover, QDateEdit::down-arrow:focus, QDateTimeEdit::down-arrow:on, QDateTimeEdit::down-arrow:hover, QDateTimeEdit::down-arrow:focus {{
        image: url(":/qss_icons/dark/rc/arrow_down.png");
    }}

    QDateEdit QAbstractItemView, QDateTimeEdit QAbstractItemView {{
        background-color: {main_background_color};
        border-radius: {border_radius}px;
        border: 1px solid {border_color};
        selection-background-color: {selected_line_color};
    }}

    /* QAbstractView ---------------------------------------------------------- */
    QAbstractView:hover {{
        border: 1px solid {selected_line_color};
        color: {text_color};
    }}

    QAbstractView:selected {{
        background: {selected_line_color};
        color: {border_color};
    }}

    /* PlotWidget ------------------------------------------------------------- */
    PlotWidget {{
        padding: 0px;
    }}

    QMenu::item {{
        padding: 4px 24px 4px 6px;
    }}
    """

    return style_sheet