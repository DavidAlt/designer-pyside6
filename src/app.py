import sys # Used for access to command line arguments
from datetime import datetime # Logger timestamps

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QDockWidget
from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction, QIcon # Menus
from PySide6.QtWidgets import QPlainTextEdit # Logger
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPalette, QColor, QBrush, QPen

from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsRectItem

class Logger(QPlainTextEdit):
    def __init__(self, include_timestamp=False):
        super().__init__()
        self._include_timestamp = include_timestamp;
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setReadOnly(True)

    def add(self, msg):
        if(self._include_timestamp):
            timestamp = datetime.now().strftime("%m/%d/%Y %H:%M")
            self.appendPlainText(timestamp + ":  " + msg)
        else:
            self.appendPlainText(msg)

    # Clearing the log: inherits clear()


# temp - remove once dock panels populated
class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)

# no custom functionality yet
class CanvasRectItem(QGraphicsRectItem):
    def __init__(self, x, y, width, height, *args, **kwargs):
        super().__init__(x, y, width, height, *args, **kwargs)


class Canvas(QGraphicsView):
    def __init__(self, parent=None):
        self.scene = QGraphicsScene(0, 0, 400, 300) # starting size
        super().__init__(self.scene, parent)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setBackgroundBrush(QBrush(QColor(Qt.GlobalColor.lightGray)))

    def add_item(self, x, y, width, height, brush_color, pen_color):
        rect = CanvasRectItem(0, 0, width, height)
        rect.setPos(x, y)
        rect.setBrush(QBrush(brush_color))
        rect.setPen(QPen(pen_color, 2))
        rect.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.scene.addItem(rect)

    # reset the scene dimensions based on the items it contains (with a little padding)
    def update_scene_size(self):
        items_rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(items_rect.adjusted(-10, -10, 10, 10))
    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discern Prompt Designer")
        self.resize(1000, 600)
        #self.setMouseTracking(True) # This causes mouse move events w/o holding down the button

        self.log = Logger()

        # Build the UI
        self.create_menu()
        self.create_toolbar()
        self.setup_docking_panels()
        
        # The canvas will be the application's central widget
        self.canvas = Canvas()
        self.setCentralWidget(self.canvas) # replace with canvas

        # Setup complete
        self.statusBar().showMessage("Ready")

    def create_menu(self):
        # Create the menubar 
        menubar = self.menuBar() 
        
        # Add File menu 
        file_menu = menubar.addMenu("File") 
        new_action = QAction("New", self) 
        open_action = QAction("Open", self) 
        save_action = QAction("Save", self) 
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(new_action) 
        file_menu.addAction(open_action) 
        file_menu.addAction(save_action) 
        file_menu.addSeparator() 
        file_menu.addAction(exit_action)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.toggleViewAction().setEnabled(False) # prevent user from hiding toolbar
        self.addToolBar(toolbar)

        # Create actions and connect them to functions. Actions work like buttons.
        base_widget_action = QAction(QIcon("assets/icons/application--plus.png"), "Base Widget", self)
        base_widget_action.setStatusTip("Base Widget")
        base_widget_action.triggered.connect(self.on_base_widget_action)
        
        reset_action = QAction(QIcon("assets/icons/cross.png"), "Reset", self)
        reset_action.setStatusTip("Reset")
        reset_action.triggered.connect(self.on_reset_action)

        test_action = QAction("Test", self)
        test_action.triggered.connect(self.on_test_action)

        # Add the actions
        toolbar.addAction(base_widget_action)
        toolbar.addSeparator()
        toolbar.addAction(reset_action)
        toolbar.addAction(test_action)

    def on_base_widget_action(self):
        self.log.add("on_base_widget_action")
        self.canvas.add_item(10, 10, 50, 50, Qt.GlobalColor.red, Qt.GlobalColor.blue)    

    def on_reset_action(self):
        self.log.clear()

    def on_test_action(self):
        self.log.add(f"View size: {self.canvas.viewport().width()}, {self.canvas.viewport().height()}")
        self.log.add(f"Scene size: {self.canvas.scene.sceneRect().width()}, {self.canvas.scene.sceneRect().height()}")

    def setup_docking_panels(self):
        # Dummy widgets to show panels
        green = Color("green")
        blue = Color("blue")
        red = Color("red")

        # Set up the docking panels
        self.tool_dock = QDockWidget("Toolbox", self)
        self.tool_dock.setFeatures(QDockWidget.DockWidgetMovable)
        self.tool_dock.setWidget(green)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool_dock)
        self.tool_dock.setGeometry(QRect(0, 0, 200, self.height()))

        self.obj_list_dock = QDockWidget("Object List", self)
        self.obj_list_dock.setFeatures(QDockWidget.DockWidgetMovable)
        self.obj_list_dock.setWidget(red)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.obj_list_dock)

        self.log_dock = QDockWidget("Log", self)
        self.log_dock.setFeatures(QDockWidget.DockWidgetMovable)
        self.log_dock.setWidget(self.log)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)

        # Give side docks priority to fill the window height
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        
        # Set the initial dock size and priority
        self.resizeDocks([self.tool_dock], [200], Qt.Horizontal)
        self.resizeDocks([self.obj_list_dock], [160], Qt.Vertical)
        
        # Only show one bottom panel control, others in tabs
        # Whichever is listed last will be shown on startup
        self.tabifyDockWidget(self.obj_list_dock, self.log_dock)     



    def mouseMoveEvent(self, e): # This overrides the parent event
        x = e.globalX() # These are screen coordinates, not MainWindow
        y = e.globalY() # These are screen coordinates, not MainWindow
        rx = e.x()
        ry = e.y()
        self.statusBar().showMessage(f"Global: {x}, {y}    Relative: {rx}, {ry}")
        
        #self.statusBar().showMessage("Ready")


# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments, QApplication([]) works too.
app = QApplication(sys.argv)
window = MainWindow()
window.show() # Windows are hidden by default

# Start the event loop
app.exec()

# Your application won't reach here until you exit and the event loop stops.