import os
import sys
import types

import pytest


def _install_pyqt6_stubs() -> None:
    """Install minimal PyQt6 stubs when PyQt6 is unavailable."""
    try:
        import PyQt6  # noqa: F401
        return
    except Exception:
        pass

    pyqt6 = types.ModuleType("PyQt6")
    qtcore = types.ModuleType("PyQt6.QtCore")
    qtgui = types.ModuleType("PyQt6.QtGui")
    qtwidgets = types.ModuleType("PyQt6.QtWidgets")

    class _Signal:
        def connect(self, *args, **kwargs):
            return None

        def emit(self, *args, **kwargs):
            return None

    def pyqtSignal(*args, **kwargs):
        return _Signal()

    class _QtBase:
        def __init__(self, *args, **kwargs):
            self._layout = None
            self._text = ""
            self._items = []
            self._selected_items = []

        def setLayout(self, layout, *args, **kwargs):
            self._layout = layout
            return None

        def layout(self, *args, **kwargs):
            return self._layout

        def count(self, *args, **kwargs):
            return len(self._items)

        def takeAt(self, index, *args, **kwargs):
            if 0 <= index < len(self._items):
                value = self._items.pop(index)
            else:
                value = None

            class _Item:
                def __init__(self, payload):
                    self._payload = payload

                def widget(self):
                    return self._payload if isinstance(self._payload, _QtBase) else None

                def layout(self):
                    return self._payload if isinstance(self._payload, _QtBase) else None

            return _Item(value)

        def setStyleSheet(self, *args, **kwargs):
            return None

        def setFont(self, *args, **kwargs):
            return None

        def setFixedHeight(self, *args, **kwargs):
            return None

        def setFixedWidth(self, *args, **kwargs):
            return None

        def setFixedSize(self, *args, **kwargs):
            return None

        def setMinimumSize(self, *args, **kwargs):
            return None

        def setMaximumSize(self, *args, **kwargs):
            return None

        def setCursor(self, *args, **kwargs):
            return None

        def setObjectName(self, *args, **kwargs):
            return None

        def setText(self, *args, **kwargs):
            if args:
                self._text = str(args[0])
            return None

        def setToolTip(self, *args, **kwargs):
            return None

        def setWordWrap(self, *args, **kwargs):
            return None

        def setMaximumWidth(self, *args, **kwargs):
            return None

        def setMinimumWidth(self, *args, **kwargs):
            return None

        def setMinimumSize(self, *args, **kwargs):
            return None

        def setMaximumSize(self, *args, **kwargs):
            return None

        def setGeometry(self, *args, **kwargs):
            return None

        def move(self, *args, **kwargs):
            return None

        def setWindowTitle(self, *args, **kwargs):
            return None

        def setModal(self, *args, **kwargs):
            return None

        def setWindowState(self, *args, **kwargs):
            return None

        def windowState(self, *args, **kwargs):
            return 0

        def setGraphicsEffect(self, *args, **kwargs):
            return None

        def findChildren(self, *args, **kwargs):
            return []

        def update(self, *args, **kwargs):
            return None

        def setPlaceholderText(self, *args, **kwargs):
            return None

        def setReadOnly(self, *args, **kwargs):
            return None

        def setLineWrapMode(self, *args, **kwargs):
            return None

        def setMinimumHeight(self, *args, **kwargs):
            return None

        def setChecked(self, *args, **kwargs):
            return None

        def addWidget(self, *args, **kwargs):
            if args:
                self._items.append(args[0])
            return None

        def addTab(self, *args, **kwargs):
            if args:
                self._items.append(args[0])
            return None

        def setWidget(self, *args, **kwargs):
            if args:
                self._items.append(args[0])
            return None

        def setWidgetResizable(self, *args, **kwargs):
            return None

        def setHorizontalScrollBarPolicy(self, *args, **kwargs):
            return None

        def setVerticalScrollBarPolicy(self, *args, **kwargs):
            return None

        def setCurrentIndex(self, *args, **kwargs):
            return None

        def addTopLevelItem(self, *args, **kwargs):
            if args:
                self._items.append(args[0])
            return None

        def setHeaderHidden(self, *args, **kwargs):
            return None

        def setTextVisible(self, *args, **kwargs):
            return None

        def setRange(self, *args, **kwargs):
            return None

        def setApplicationName(self, *args, **kwargs):
            return None

        def setApplicationVersion(self, *args, **kwargs):
            return None

        def setPalette(self, *args, **kwargs):
            return None

        def exec(self, *args, **kwargs):
            return 0

        def addLayout(self, *args, **kwargs):
            if args:
                self._items.append(args[0])
            return None

        def addStretch(self, *args, **kwargs):
            return None

        def addSpacing(self, *args, **kwargs):
            return None

        def setContentsMargins(self, *args, **kwargs):
            return None

        def setSpacing(self, *args, **kwargs):
            return None

        def setAlignment(self, *args, **kwargs):
            return None

        def hide(self, *args, **kwargs):
            return None

        def show(self, *args, **kwargs):
            return None

        def currentText(self, *args, **kwargs):
            return self._text

        def isChecked(self, *args, **kwargs):
            return False

        def text(self, *args, **kwargs):
            return self._text

        def toPlainText(self, *args, **kwargs):
            return self._text

        def setPlainText(self, *args, **kwargs):
            self._text = str(args[0]) if args else ""
            return None

        def insertPlainText(self, *args, **kwargs):
            if args:
                self._text += str(args[0])
            return None

        def append(self, *args, **kwargs):
            if args:
                self._text += ("\n" if self._text else "") + str(args[0])
            return None

        def clear(self, *args, **kwargs):
            self._text = ""
            self._items = []
            self._selected_items = []
            return None

        def addItems(self, *args, **kwargs):
            if args:
                self._items.extend(list(args[0]))
            return None

        def addItem(self, *args, **kwargs):
            if args:
                self._items.append(args[0])
            return None

        def selectedItems(self, *args, **kwargs):
            return list(self._selected_items)

        def row(self, item, *args, **kwargs):
            try:
                return self._items.index(item)
            except ValueError:
                return -1

        def exec(self, *args, **kwargs):
            return 0

        def accept(self, *args, **kwargs):
            return None

        def reject(self, *args, **kwargs):
            return None

        def rect(self, *args, **kwargs):
            class _Rect:
                def width(self):
                    return 1200

                def height(self):
                    return 800

            return _Rect()

        def width(self, *args, **kwargs):
            return 1200

        def height(self, *args, **kwargs):
            return 800

        def y(self, *args, **kwargs):
            return 0

        def adjustSize(self, *args, **kwargs):
            return None

        def raise_(self, *args, **kwargs):
            return None

        def layout(self, *args, **kwargs):
            return None

        def __getattr__(self, name):
            signal_names = {
                "clicked",
                "pressed",
                "released",
                "toggled",
                "stateChanged",
                "textChanged",
                "currentTextChanged",
                "valueChanged",
                "accepted",
                "rejected",
                "triggered",
                "timeout",
                "enter_pressed",
                "buttonClicked",
                "itemDoubleClicked",
                "activated",
            }
            if name in signal_names or name.endswith("Changed"):
                return _Signal()
            raise AttributeError(name)

    class Qt:
        class CursorShape:
            ArrowCursor = 0
            PointingHandCursor = 1

        class AlignmentFlag:
            AlignCenter = 0

        class Key:
            Key_Return = 0
            Key_Enter = 1

        class KeyboardModifier:
            ControlModifier = 1

        class WindowState:
            WindowMaximized = 1

        class ScrollBarPolicy:
            ScrollBarAlwaysOff = 0

        class MouseButton:
            LeftButton = 1

        class TextFormat:
            PlainText = 0

    class QFont(_QtBase):
        class Weight:
            Bold = 700

    class QApplication(_QtBase):
        _instance = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            QApplication._instance = self

        @staticmethod
        def instance():
            return QApplication._instance

    class QColor(_QtBase):
        pass

    class QPalette(_QtBase):
        class ColorRole:
            Window = 0
            WindowText = 1
            Base = 2
            AlternateBase = 3
            Text = 4
            PlaceholderText = 5
            Button = 6
            ButtonText = 7
            Highlight = 8
            HighlightedText = 9
            ToolTipBase = 10
            ToolTipText = 11

        class ColorGroup:
            Disabled = 0

        def setColor(self, *args, **kwargs):
            return None

        def setColorGroup(self, *args, **kwargs):
            return None

    class QTextEdit(_QtBase):
        class LineWrapMode:
            WidgetWidth = 0

    class QSize(_QtBase):
        pass

    class QObject(_QtBase):
        pass

    class QTimer(_QtBase):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.timeout = _Signal()

        def start(self, *args, **kwargs):
            return None

        def stop(self, *args, **kwargs):
            return None

        @staticmethod
        def singleShot(_ms, callback):
            if callable(callback):
                callback()

    class QPoint(_QtBase):
        pass

    class QEasingCurve:
        class Type:
            OutCubic = 0
            InCubic = 1

    class QPropertyAnimation(_QtBase):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.finished = _Signal()

        def setDuration(self, *args, **kwargs):
            return None

        def setEasingCurve(self, *args, **kwargs):
            return None

        def setStartValue(self, *args, **kwargs):
            return None

        def setEndValue(self, *args, **kwargs):
            return None

        def start(self, *args, **kwargs):
            return None

    qtcore.Qt = Qt
    qtcore.pyqtSignal = pyqtSignal
    qtcore.QSize = QSize
    qtcore.QObject = QObject
    qtcore.QTimer = QTimer
    qtcore.QPoint = QPoint
    qtcore.QEasingCurve = QEasingCurve
    qtcore.QPropertyAnimation = QPropertyAnimation

    qtgui.QCursor = type("QCursor", (_QtBase,), {})
    qtgui.QFont = QFont
    qtgui.QColor = QColor
    qtgui.QPalette = QPalette
    qtgui.QPixmap = type("QPixmap", (_QtBase,), {})
    qtgui.QImage = type("QImage", (_QtBase,), {})
    qtgui.QKeyEvent = type("QKeyEvent", (_QtBase,), {})
    qtgui.QTextCursor = type("QTextCursor", (_QtBase,), {})
    qtgui.QKeySequence = type("QKeySequence", (_QtBase,), {})
    qtgui.QShortcut = type("QShortcut", (_QtBase,), {})

    widget_names = [
        "QWidget",
        "QMainWindow",
        "QVBoxLayout",
        "QHBoxLayout",
        "QGridLayout",
        "QLabel",
        "QPushButton",
        "QFrame",
        "QStackedWidget",
        "QDialog",
        "QFileDialog",
        "QLineEdit",
        "QComboBox",
        "QRadioButton",
        "QButtonGroup",
        "QSizePolicy",
        "QSpacerItem",
        "QTextEdit",
        "QListWidget",
        "QListWidgetItem",
        "QScrollArea",
        "QPlainTextEdit",
        "QCheckBox",
        "QTabWidget",
        "QMessageBox",
        "QGraphicsDropShadowEffect",
        "QProgressBar",
        "QTreeWidget",
        "QTreeWidgetItem",
        "QSplitter",
    ]
    qtwidgets.QApplication = QApplication

    class QFileDialog(_QtBase):
        @staticmethod
        def getOpenFileNames(*args, **kwargs):
            return ([], "")

    qtwidgets.QFileDialog = QFileDialog
    for name in widget_names:
        cls = QTextEdit if name == "QTextEdit" else type(name, (_QtBase,), {})
        setattr(qtwidgets, name, cls)

    pyqt6.QtCore = qtcore
    pyqt6.QtGui = qtgui
    pyqt6.QtWidgets = qtwidgets

    sys.modules.setdefault("PyQt6", pyqt6)
    sys.modules.setdefault("PyQt6.QtCore", qtcore)
    sys.modules.setdefault("PyQt6.QtGui", qtgui)
    sys.modules.setdefault("PyQt6.QtWidgets", qtwidgets)


_install_pyqt6_stubs()


@pytest.fixture(autouse=True, scope="session")
def fake_env():
    key_name = "ZHIPU_API_KEY"
    device_name = "PHONE_AGENT_DEVICE_TYPE"

    old_key = os.environ.get(key_name)
    old_device = os.environ.get(device_name)

    os.environ[key_name] = "test-key"
    os.environ[device_name] = "android"

    yield

    if old_key is None:
        os.environ.pop(key_name, None)
    else:
        os.environ[key_name] = old_key

    if old_device is None:
        os.environ.pop(device_name, None)
    else:
        os.environ[device_name] = old_device


@pytest.fixture(autouse=True)
def isolate_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("FOREVER_MEMORY_FILE", str(tmp_path / "forever_memory.txt"))


@pytest.fixture
def fake_emit_event(monkeypatch):
    events = []

    def _emit(name, payload, source=None, level=None):
        events.append({"name": name, "payload": payload, "source": source, "level": level})

    monkeypatch.setattr("phone_agent.events.emit_agent_event", _emit, raising=False)
    return events
