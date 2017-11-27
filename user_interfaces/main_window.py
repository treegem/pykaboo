from PyQt5 import QtWidgets

from user_interfaces.logger import Logger
from user_interfaces.nv_localiser import NVLocaliser
from utility.config import global_confs


# noinspection PyAttributeOutsideInit
class MainWindow(QtWidgets.QMainWindow):
    count = 0  # number of opened windows
    nvloc_isopen = False  # status of NV Localiser widget

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.screenShape = QtWidgets.QDesktopWidget().screenGeometry(-1)
        self.resize(self.screenShape.width()*2//3, self.screenShape.height()*2//3)

        self.mdi = QtWidgets.QMdiArea()  # create multiple document interface widget
        self.setCentralWidget(self.mdi)

        self.bar = self.menuBar()

        task = self.bar.addMenu("Task")  # menu with different tasks (fitting, finding NVs,...)
        task.addAction("NV Localiser")
        task.triggered[QtWidgets.QAction].connect(self.task_windowaction)

        file = self.bar.addMenu("File")  # menu with file tasks (open, load, close, new,...) Currently dummy
        file.addAction("New")
        file.addAction("Cascade")
        file.addAction("Tiled")
        file.triggered[QtWidgets.QAction].connect(self.file_windowaction)

        self.setWindowTitle("%s %s" % (global_confs['progname'], global_confs['progversion']))

        self.logger = Logger(self)
        self.log_widget = QtWidgets.QMdiSubWindow()
        self.log_widget.setWidget(self.logger)
        self.log_widget.setWindowTitle("Logger")
        self.log_widget.setObjectName('WIN_LOG')
        self.mdi.addSubWindow(self.log_widget)
        self.log_widget.resize(self.frameGeometry().width(), self.frameGeometry().height()//4)
        self.log_widget.move(0, self.geometry().height()*3//4)
        self.log_widget.show()


    def task_windowaction(self, q):  # executes when task menu item selected

        if q.text() == "NV Localiser":
            if not MainWindow.nvloc_isopen:  # no nvloc window yet
                MainWindow.count = MainWindow.count + 2
                MainWindow.nvloc_isopen = True

                self.nv_localiser = NVLocaliser(self.logger, self)
                self.nvloc_widget = QtWidgets.QMdiSubWindow()
                self.nvloc_widget.setWidget(self.nv_localiser)
                self.nvloc_widget.setWindowTitle("NV Localiser")
                self.nvloc_widget.setObjectName('WIN_NVLOC')
                self.mdi.addSubWindow(self.nvloc_widget)
                self.nvloc_widget.show()

            else:
                pass

        else:
            pass

    def file_windowaction(self, q):  # executes when file menu item selected

        if q.text() == "New":
            MainWindow.count = MainWindow.count + 1
            sub = QtWidgets.QMdiSubWindow()
            sub.setWidget(QtWidgets.QTextEdit())
            sub.setWindowTitle("subwindow" + str(MainWindow.count))
            self.mdi.addSubWindow(sub)
            sub.show()

        elif q.text() == "Cascade":
            self.mdi.cascadeSubWindows()

        elif q.text() == "Tiled":
            self.mdi.tileSubWindows()

        else:
            pass

