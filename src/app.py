import sys # Used for access to command line arguments
from datetime import datetime # Logger timestamps

from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar, QWidget, QDockWidget, QPlainTextEdit
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem
from PySide6.QtGui import QAction, QIcon, QPalette, QColor, QBrush, QPen
from PySide6.QtCore import Qt, Signal, QRect, QRectF

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

class CanvasItem(QGraphicsItem):
    def __init__(self, width, height):
        super().__init__()
        self.width = width
        self.height = height
        self.setPos(25, 25)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(Qt.GlobalColor.blue))
        painter.drawRect(0, 0, self.width, self.height)

        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.magenta, 2))
            painter.drawRect(self.boundingRect())

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def resize(self, new_width, new_height):
        self.prepareGeometryChange()
        self.width = new_width
        self.height = new_height

    def __str__(self):
        return(f"{type(self)} (x: {self.pos().x()}, y: {self.pos().y()}, w: {self.width}, h: {self.height})")



class Canvas(QGraphicsView):
    cursor_position_changed = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(0, 0, 400, 300)
        self.setScene(self.scene)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setBackgroundBrush(QBrush(QColor(Qt.GlobalColor.lightGray)))
        self.setMouseTracking(True)
        self.resizing_item = None
        self.resize_direction = None

    def add_item(self, x, y, width, height, brush_color, pen_color):
        item = CanvasItem(width, height)
        self.scene.addItem(item)
        print(str(item) + " added")

    def update_scene_size(self):
        items_rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(items_rect.adjusted(-10, -10, 10, 10))

    def reset(self):
        self.scene.clear()

    def delete_selected_items(self):
        for item in self.scene.selectedItems():
            print(str(item) + " removed")
            self.scene.removeItem(item)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        self.cursor_position_changed.emit(scene_pos.x(), scene_pos.y())

        if self.resizing_item:
            new_width = max(10, scene_pos.x() - self.resizing_item.pos().x())
            new_height = max(10, scene_pos.y() - self.resizing_item.pos().y())
            if self.resize_direction == "horizontal":
                self.resizing_item.resize(new_width, self.resizing_item.height)
            elif self.resize_direction == "vertical":
                self.resizing_item.resize(self.resizing_item.width, new_height)
            elif self.resize_direction == "both":
                self.resizing_item.resize(new_width, new_height)
        else:
            items = self.scene.items(scene_pos)
            if items:
                for item in items:
                    if isinstance(item, CanvasItem):
                        bounds = item.boundingRect()
                        right_edge = abs(bounds.right() - (scene_pos.x() - item.pos().x())) < 5
                        bottom_edge = abs(bounds.bottom() - (scene_pos.y() - item.pos().y())) < 5
                        if right_edge and bottom_edge:
                            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                            return
                        elif right_edge:
                            self.setCursor(Qt.CursorShape.SizeHorCursor)
                            return
                        elif bottom_edge:
                            self.setCursor(Qt.CursorShape.SizeVerCursor)
                            return
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            items = self.scene.items(scene_pos)
            for item in items:
                if isinstance(item, CanvasItem):
                    #right_edge = abs(item.boundingRect().right() - (scene_pos.x() - item.pos().x())) < 5
                    #bottom_edge = abs(item.boundingRect().bottom() - (scene_pos.y() - item.pos().y())) < 5
                    if self.cursor().shape() == Qt.CursorShape.SizeHorCursor:
                        self.resizing_item = item
                        self.resize_direction = "horizontal"
                        return
                    elif self.cursor().shape() == Qt.CursorShape.SizeVerCursor:
                        self.resizing_item = item
                        self.resize_direction = "vertical"
                        return
                    elif self.cursor().shape() == Qt.CursorShape.SizeFDiagCursor:
                        self.resizing_item = item
                        self.resize_direction = "both"
                        return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing_item = None
            self.resize_direction = None
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discern Prompt Designer")
        self.resize(1000, 600)
        self.log = Logger()

        # Build the UI
        self.create_menu()
        self.create_toolbar()
        self.setup_docking_panels()
        
        # The canvas will be the application's central widget
        self.canvas = Canvas()
        self.canvas.cursor_position_changed.connect(self.statusbar_show_canvas_coords)
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

        # Add Canvas menu
        canvas_menu = menubar.addMenu("Canvas")
        reset_action = QAction("Reset", self)
        reset_action.triggered.connect(self.on_reset_action)

        canvas_menu.addAction(reset_action)

        # Add Canvas Item menu
        canvas_item_menu = menubar.addMenu("Canvas Item")
        delete_item_action = QAction("Delete", self)
        delete_item_action.setShortcut(Qt.Key_Delete)
        delete_item_action.triggered.connect(self.on_delete_item)

        canvas_item_menu.addAction(delete_item_action)

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
        test_action.setStatusTip("Test")
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
        self.canvas.reset()

    def on_delete_item(self):
        self.canvas.delete_selected_items()

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

    def statusbar_show_canvas_coords(self, x, y):
        self.statusBar().showMessage(f"{int(x)}, {int(y)}")
        


# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments, QApplication([]) works too.
app = QApplication(sys.argv)
window = MainWindow()
window.show() # Windows are hidden by default

# Start the event loop
app.exec()

# Your application won't reach here until you exit and the event loop stops.