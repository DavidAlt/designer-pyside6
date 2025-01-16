import sys # Used for access to command line arguments
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QDockWidget
from PySide6.QtCore import Qt, QRect

from PySide6.QtGui import QPalette, QColor

class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discern Prompt Designer")
        self.resize(1000, 600)
        #self.setMouseTracking(True) # This causes mouse move events w/o holding down the button

        # Build the UI
        self.setup_docking_panels()
        
        # The canvas will be the application's central widget
        self.setCentralWidget(Color("black")) # replace with canvas

        # Setup complete
        self.statusBar().showMessage("Ready")

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
        self.log_dock.setWidget(blue)
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