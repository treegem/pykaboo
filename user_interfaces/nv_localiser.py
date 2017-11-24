import os

import numpy as np
from PyQt5 import QtWidgets
from scipy import optimize as opt
from scipy.interpolate import griddata

from helper_classes.dwg_xch_file import DwgXchFile
from helper_classes.stack import Stack
from plot_classes.color_plot import ColorPlot
from utility.config import paths
from utility.utility_functions import two_d_gaussian_sym, flatten_list, affine_trafo


# noinspection PyAttributeOutsideInit
class NVLocaliser(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(NVLocaliser, self).__init__(parent)

        self.raw_buffer = Stack()
        self.dxf_buffer = Stack()

        self.dxf_loaded = False
        self.raw_loaded = False
        self.nv_select_mode = False

        self.local_menu = self.parent().bar.addMenu(
            "NV Localiser")  # menu with different tasks (fitting, finding NVs,...)
        self.local_menu.addAction("Load *.mat")
        self.local_menu.addAction("Load *.dxf")
        self.local_menu.addAction("New *.dxf")
        self.local_menu.triggered[QtWidgets.QAction].connect(self.local_menu_windowaction)

        self.setGeometry(300, 300, 300, 220)
        self.raw_img = ColorPlot(self, width=4, height=4, dpi=100)
        self.raw_img.mpl_connect('button_release_event', self.raw_mouse_released)
        self.dxf_img = ColorPlot(self, width=4, height=4, dpi=100)
        self.dxf_img.mpl_connect('scroll_event', self.zoom_dxf)
        self.dxf_img.mpl_connect('button_release_event', self.dxf_mouse_released)

        self.bwd_btn = QtWidgets.QPushButton('<< Last', self)
        self.bwd_btn.setToolTip('Load previous image')
        self.bwd_btn.setObjectName('-1')
        self.bwd_btn.clicked.connect(self.file_crawl)
        self.bwd_btn.resize(self.bwd_btn.sizeHint())
        self.fwd_btn = QtWidgets.QPushButton('Next >>', self)
        self.fwd_btn.setToolTip('Load next image')
        self.fwd_btn.setObjectName('1')
        self.fwd_btn.clicked.connect(self.file_crawl)
        self.fwd_btn.resize(self.fwd_btn.sizeHint())
        self.edt_curr_file = QtWidgets.QLineEdit('n/a', self)
        self.edt_curr_file.setReadOnly(True)
        self.lbl_max = QtWidgets.QLabel('Max. Cts.:', self)
        self.edt_max = QtWidgets.QLineEdit('5e5', self)
        self.edt_max.returnPressed.connect(self.change_cts)
        self.lbl_min = QtWidgets.QLabel('Min. Cts.:', self)
        self.edt_min = QtWidgets.QLineEdit('3e4', self)
        self.edt_min.returnPressed.connect(self.change_cts)
        self.magnets_cb = QtWidgets.QComboBox()
        #        self.magnets_cb.addItems(['windmill_s', 'mercedes_s', 'sierpinski_s', 'hazard_s', 'hazard2_s', 'holey_s', 'flag_s', 'cross_s',
        #                          'mitsubishi_s', 'windmill_b', 'mercedes_b', 'hazard_b', 'hazard2_b', 'holey_b', 'flag_b', 'cross_b',
        #                          'mitsubishi_b'])
        #        self.magnets_cb.addItems(['mitsubishi_b', 'windmill_b', 'hazard_b'])#, 'nuclear_b', 'nuclear2_b'])
        #        self.magnets_cb.addItems(['mitsubishi_xp', 'mitsubishi_xm', 'mitsubishi_yp', 'mitsubishi_ym', 'windmill_xp', 'windmill_xm', 'windmill_yp', 'windmill_ym'])
        self.magnets_cb.addItems(
            ['mitsubishi5', 'windmill_5B1', 'mitsubishi5xp', 'mitsubishi5xm', 'mitsubishi5yp', 'mitsubishi5ym',
             'windmill5xp', 'windmill5xm', 'windmill5yp', 'windmill5ym'])
        self.trafo_btn = QtWidgets.QPushButton('Transform', self)
        self.trafo_btn.setToolTip('Transform raw image into coordinate system')
        self.trafo_btn.clicked.connect(self.trafo)
        self.trafo_btn.resize(self.trafo_btn.sizeHint())
        self.save_dxf_btn = QtWidgets.QPushButton('Save dxf', self)
        self.save_dxf_btn.setToolTip('Add selection to dxf')
        self.save_dxf_btn.clicked.connect(self.save_dxf)
        self.save_dxf_btn.resize(self.save_dxf_btn.sizeHint())
        self.save_png_btn = QtWidgets.QPushButton('Save png', self)
        self.save_png_btn.setToolTip('Save current view as image')
        self.save_png_btn.clicked.connect(self.save_png)
        self.save_png_btn.resize(self.save_png_btn.sizeHint())
        self.overwrite_cb = QtWidgets.QCheckBox('Overwrite dxf', self)
        self.overwrite_cb.setChecked(False)

        hbox = QtWidgets.QHBoxLayout()
        hbox.setSpacing(30)
        hbox.addWidget(self.raw_img)
        hbox.addWidget(self.dxf_img)

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.setSpacing(10)
        hbox1.addWidget(self.bwd_btn)
        hbox1.addWidget(self.fwd_btn)
        hbox1.addStretch(5)
        hbox1.addWidget(self.magnets_cb)
        hbox1.addStretch(1)
        hbox1.addWidget(self.trafo_btn)
        hbox1.addWidget(self.save_dxf_btn)
        hbox1.addWidget(self.save_png_btn)

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.setSpacing(10)
        hbox2.addWidget(self.edt_curr_file)
        hbox2.addStretch(1)
        hbox2.addWidget(self.lbl_max)
        hbox2.addWidget(self.edt_max)
        hbox2.addWidget(self.lbl_min)
        hbox2.addWidget(self.edt_min)
        hbox2.addStretch(5)
        hbox2.addWidget(self.overwrite_cb)

        main_vbox = QtWidgets.QVBoxLayout(self)
        main_vbox.setSpacing(10)
        main_vbox.addLayout(hbox)
        main_vbox.addLayout(hbox1)
        main_vbox.addLayout(hbox2)

    def local_menu_windowaction(self, q):  # executes when file menu item selected

        if q.text() == "Load *.mat":
            self.load_raw()

        elif q.text() == "Load *.dxf":
            fname = \
                QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', paths['registration'],
                                                      "Drawing interchange files (*.dxf)")[0]
            self.load_dxf(fname)

        elif q.text() == "New *.dxf":
            fname = os.path.join(paths['dxf'], 'coords_new.dxf')
            self.load_dxf(fname)

        else:
            pass

    def load_raw(self):
        self.dir_name = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open folder',
                                                                   paths['registration'])
        if self.dir_name == '':
            return

        self.dir_content = [f for f in os.listdir(self.dir_name) if
                            (f.startswith('scan') or f.startswith('field')) and f.endswith('.mat')]
        try:
            self.raw_img.load_mat(os.path.join(self.dir_name, self.dir_content[0]))
            self.change_cts()
            self.edt_curr_file.setText(self.dir_content[0])
            self.raw_loaded = True
        except:
            pass

    def file_crawl(self):
        up_down = self.sender()
        if self.raw_loaded:
            if (self.dir_content.index(self.edt_curr_file.text()) == 0 and int(up_down.objectName()) == -1) or (
                            self.dir_content.index(self.edt_curr_file.text()) == len(self.dir_content) - 1 and int(
                        up_down.objectName()) == 1):
                pass
            else:
                self.edt_curr_file.setText(
                    self.dir_content[self.dir_content.index(self.edt_curr_file.text()) + int(up_down.objectName())])
                self.raw_img.load_mat(os.path.join(self.dir_name, self.edt_curr_file.text()))
                self.raw_img.select_coord = []
                self.raw_buffer.empty()
                if self.dxf_loaded:
                    self.dxf_img.select_coord = []
                    self.dxf_buffer.empty()
                    self.dxf_img.cts_xy = []
                    self.dxf_img.draw_dxf()
                self.nv_select_mode = False
        else:
            pass

    def raw_mouse_released(self, event):
        if any([event.xdata, event.ydata]):
            if event.button == 1:

                x_ax = self.raw_img.x_axis
                y_ax = self.raw_img.y_axis[::-1]
                x_ax, y_ax = np.meshgrid(x_ax, y_ax)

                initial_guess = (self.raw_img.cts_vmax, event.xdata, event.ydata, 0.2, min(
                    self.raw_img.cts_xy.ravel()))  # self.raw_img.cts_vmax/2) # amplitude, x0, y0, sigma, offset
                param_bounds = ([0, event.xdata - 1, event.ydata - 1, 0, -np.inf],
                                [np.inf, event.xdata + 1, event.ydata + 1, np.inf, np.inf])
                popt, pcov = opt.curve_fit(two_d_gaussian_sym, [x_ax, y_ax], self.raw_img.cts_xy.ravel(),
                                           p0=initial_guess, bounds=param_bounds)
                print(str(popt))
                print(str(np.sqrt(pcov[1, 1] ** 2 + pcov[2, 2] ** 2)))
                self.raw_buffer.push([popt[1], popt[2]])
                if not self.nv_select_mode:
                    self.raw_img.select_coord.append([popt[1], popt[2]])
                else:
                    self.raw_img.select_nv.append([popt[1], popt[2]])
                    trafo_coords = np.dot(np.array([self.raw_img.select_nv[-1][0], self.raw_img.select_nv[-1][1], 1]),
                                          self.trafo_matrix)[:-1]
                    self.dxf_in.add(self.magnets_cb.currentText(), trafo_coords)
                    self.dxf_img.select_nv = flatten_list(self.dxf_in.new_patch_list)
                    self.dxf_img.draw_dxf()
                self.raw_img.redraw()
            if event.button == 2:  # manually select point by pressing wheel
                self.raw_buffer.push([event.xdata, event.ydata])
                if not self.nv_select_mode:
                    self.raw_img.select_coord.append([event.xdata, event.ydata])
                else:
                    self.raw_img.select_nv.append([event.xdata, event.ydata])
                    trafo_coords = np.dot(np.array([self.raw_img.select_nv[-1][0], self.raw_img.select_nv[-1][1], 1]),
                                          self.trafo_matrix)[:-1]
                    self.dxf_in.add(self.magnets_cb.currentText(), trafo_coords)
                    self.dxf_img.select_nv = flatten_list(self.dxf_in.new_patch_list)
                    self.dxf_img.draw_dxf()
                self.raw_img.redraw()
            if event.button == 3 and not self.raw_buffer.is_empty():
                x, y = self.raw_buffer.pop()
                if not self.nv_select_mode:
                    self.raw_img.select_coord.pop()
                else:
                    self.raw_img.select_nv.pop()
                    self.dxf_in.remove_last()
                    self.dxf_img.select_nv = flatten_list(self.dxf_in.new_patch_list)
                    self.dxf_img.draw_dxf()
                self.raw_img.redraw()

    def trafo(self):
        if len(self.raw_img.select_coord) == len(self.dxf_img.select_coord) and len(self.raw_img.select_coord) >= 3:
            self.trafo_matrix = affine_trafo(self.raw_img.select_coord, self.dxf_img.select_coord)
            if np.trace(self.trafo_matrix) < 2.85:
                print(str(self.trafo_matrix))
            elif len(self.trafo_matrix):
                print(str(self.trafo_matrix))
                x_ax = self.raw_img.x_axis
                y_ax = self.raw_img.y_axis[::-1]
                x_ax, y_ax = np.meshgrid(x_ax, y_ax)
                x_ax, y_ax, _ = np.dot(np.array([x_ax, y_ax, 1]), self.trafo_matrix)
                x_ax, y_ax = x_ax.ravel(), y_ax.ravel()

                nx, ny = 300, 300
                # Generate a regular grid to interpolate the data.
                xi = np.linspace(min(x_ax), max(x_ax), nx)
                yi = np.linspace(min(y_ax), max(y_ax), ny)
                xi, yi = np.meshgrid(xi, yi)
                # Interpolate using linear triangularization
                self.raw_img.cts_xy = self.raw_img.graph[
                    'result']  # when using LP580 technique, switch to full image at this point
                self.dxf_img.cts_xy = griddata((x_ax, y_ax), self.raw_img.cts_xy.ravel(), (xi, yi), method='linear',
                                               fill_value=min(self.raw_img.cts_xy.ravel()))[::-1]
                #                self.raw_img.cts_xy = ctsi.filled(min(self.raw_img.cts_xy.ravel()))
                self.dxf_img.x_axis = xi[0]
                self.dxf_img.y_axis = yi.transpose()[0]
                self.dxf_img.cts_vmin = self.raw_img.cts_vmin
                self.dxf_img.cts_vmax = self.raw_img.cts_vmax
                self.dxf_img.select_coord = []
                self.raw_img.select_coord = []
                self.dxf_buffer.empty()
                self.raw_buffer.empty()
                self.dxf_img.draw_dxf()
                self.raw_img.redraw()
                self.nv_select_mode = True
            else:
                pass
        else:
            pass

    def change_cts(self):
        try:
            self.raw_img.cts_vmin = float(self.edt_min.text())
            self.dxf_img.cts_vmin = float(self.edt_min.text())
        except:
            pass
        try:
            self.raw_img.cts_vmax = float(self.edt_max.text())
            self.dxf_img.cts_vmax = float(self.edt_max.text())
        except:
            pass
        self.raw_img.redraw()
        if len(self.dxf_img.cts_xy):
            self.dxf_img.draw_dxf()

    def load_dxf(self, fname):
        self.dxf_in = DwgXchFile()
        self.dxf_in.load(fname, ['ALIGN', 'COORD', 'MAGNET'], ['POLYLINE', 'CIRCLE', 'POLYLINE'])
        self.dxf_img.x_lim = np.array([0, 100])
        self.dxf_img.y_lim = np.array([0, 100])
        self.dxf_img.cts_xy = []
        self.dxf_img.dxf_objects = self.dxf_in.patch_list
        self.dxf_img.draw_dxf()
        self.dxf_loaded = True

    def save_dxf(self):
        if not self.overwrite_cb.isChecked():
            fname = \
                QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', paths['registration'],
                                                      "Drawing interchange files (*.dxf)")[0]
            if not fname.endswith('.dxf'):
                fname += ".dxf"
        elif self.overwrite_cb.isChecked():
            fname = self.dxf_in.location
        else:
            print('Checkbox isn\'t working')
            fname = \
                QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', paths['registration'],
                                                      "Drawing interchange files (*.dxf)")[0]
            if not fname.endswith('.dxf'):
                fname += ".dxf"
        self.dxf_in.save(fname)

        self.dxf_img.select_nv = []
        self.dxf_buffer.empty()
        self.load_dxf(fname)

        self.raw_img.select_nv = []
        self.raw_buffer.empty()
        self.raw_img.redraw()

    def zoom_dxf(self, event):
        if self.dxf_loaded:
            if event.button == 'up':
                self.dxf_img.x_lim = np.array([(self.dxf_img.x_lim[0] - event.xdata) / 1.2 + event.xdata,
                                               (self.dxf_img.x_lim[1] - event.xdata) / 1.2 + event.xdata])
                self.dxf_img.y_lim = np.array([(self.dxf_img.y_lim[0] - event.ydata) / 1.2 + event.ydata,
                                               (self.dxf_img.y_lim[1] - event.ydata) / 1.2 + event.ydata])
            elif event.button == 'down':
                self.dxf_img.x_lim = np.array([(self.dxf_img.x_lim[0] - event.xdata) * 1.2 + event.xdata,
                                               (self.dxf_img.x_lim[1] - event.xdata) * 1.2 + event.xdata])
                self.dxf_img.y_lim = np.array([(self.dxf_img.y_lim[0] - event.ydata) * 1.2 + event.ydata,
                                               (self.dxf_img.y_lim[1] - event.ydata) * 1.2 + event.ydata])
            self.dxf_img.draw_dxf()
        else:
            print('you are at ', event.xdata, event.ydata, 'and something went wrong')

    def dxf_mouse_released(self, event):
        if any([event.xdata, event.ydata]):
            if event.button == 1:
                x, y = event.xdata, event.ydata
                if not self.nv_select_mode:
                    all_coord_ctr = [entity.center[:-1] for entity in
                                     self.dxf_in.entities[1]]  # centres of coordinate points (list [1] in entities)
                    ds = [np.sqrt((x - coord[0]) ** 2 + (y - coord[1]) ** 2) for coord in all_coord_ctr]
                    if min(ds) < 0.3:
                        print(str(all_coord_ctr[ds.index(min(ds))]))
                        self.dxf_buffer.push(all_coord_ctr[ds.index(min(ds))])
                        self.dxf_img.select_coord.append(all_coord_ctr[ds.index(min(ds))])
                        self.dxf_img.draw_dxf()
                else:
                    pass
            if event.button == 3 and not self.dxf_buffer.is_empty():
                if not self.nv_select_mode:
                    x, y = self.dxf_buffer.pop()
                    self.dxf_img.select_coord.pop()
                    self.dxf_img.draw_dxf()
                else:
                    pass

    def save_png(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', paths['registration'],
                                                      "Portable network graphics (*.png)")[0]
        if not fname.endswith('.png'):
            fname += ".png"
        self.dxf_img.save(fname)