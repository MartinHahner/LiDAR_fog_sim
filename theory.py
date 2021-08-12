__author__  = "Martin Hahner"
__contact__ = "martin.hahner@pm.me"
__license__ = "CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/)"

# GUI adapted from
# https://memotut.com/create-a-3d-model-viewer-with-pyqt5-and-pyqtgraph-b3916/ and
# https://matplotlib.org/3.1.1/gallery/user_interfaces/embedding_in_qt_sgskip.html

import sys
import math
import socket
import functools

import numpy as np
import matplotlib as plt
import multiprocessing as mp
import matplotlib.patches as mpatches
import scipy.integrate as scipy_integrate

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure
from fog_simulation import ParameterSet
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)

from scipy.constants import speed_of_light as c     # in m/s

SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

TAU_H = '\u03C4' + '\N{LATIN SUBSCRIPT SMALL LETTER H}'



class ApplicationWindow(QMainWindow):


    def __init__(self) -> None:

        super().__init__()

        self.p = ParameterSet()

        self.row_height = 20
        self.current_row = 0

        self.num_cpus = mp.cpu_count()
        self.pool = mp.Pool(self.num_cpus)

        hostname = socket.gethostname()

        if hostname == 'beast':

            self.monitor = QDesktopWidget().screenGeometry(1)
            self.monitor.translate(0, int(0.55 * self.monitor.height()))
            self.monitor.setHeight(int(0.45 * self.monitor.height()))

        elif hostname == 'hox':

            self.monitor = QDesktopWidget().screenGeometry(2)
            self.monitor.translate(0, int(0.55 * self.monitor.height()))
            self.monitor.setHeight(int(0.45 * self.monitor.height()))

        else:

            self.monitor = QDesktopWidget().screenGeometry(0)
            self.monitor.setHeight(self.monitor.height())

        self.setGeometry(self.monitor)

        self._main = QWidget()
        self.setCentralWidget(self._main)
        self.layout = QGridLayout(self._main)

        self.static_canvas = FigureCanvas(Figure(figsize=(3, 3)))
        self.layout.addWidget(self.static_canvas, self.current_row, 0, 1, 3)
        self.addToolBar(NavigationToolbar(self.static_canvas, self))

        self._static_ax = self.static_canvas.figure.subplots()
        self.current_row += 1

        if self.p.linear_xsi:
            self.xsi_btn = QPushButton(text="linear xsi active")
        else:
            self.xsi_btn = QPushButton(text="formula xsi active")

        self.xsi_btn.clicked.connect(self.toggle_xsi)
        self.layout.addWidget(self.xsi_btn, self.current_row, 0, 1, 1)

        self.reset_btn = QPushButton(text="reset values")
        self.reset_btn.clicked.connect(self.toggle_reset)
        self.reset_btn.setToolTip("resets one value at a time (from top to bottom)")
        self.layout.addWidget(self.reset_btn, self.current_row, 2, 1, 1)

        self.current_row += 1

        self.r_title = QLabel('range')
        self.r_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.r_title, self.current_row, 0)

        self.r_slider = QSlider(Qt.Horizontal)
        self.r_slider.setMinimum(self.p.r_range_min)
        self.r_slider.setMaximum(self.p.r_range_max)
        self.r_slider.setValue(self.p.r_range)

        self.layout.addWidget(self.r_slider, self.current_row, 1)
        self.r_slider.valueChanged.connect(self.update_labels)

        self.r_label = QLabel(f"r = {self.p.r_range}")
        self.r_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.r_label, self.current_row, 2)
        self.current_row += 1

        self.n_title = QLabel('quantization')
        self.n_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.n_title, self.current_row, 0)

        self.n_slider = QSlider(Qt.Horizontal)
        self.n_slider.setMinimum(self.p.n_min)
        self.n_slider.setMaximum(self.p.n_max)
        self.n_slider.setValue(self.p.n)

        self.layout.addWidget(self.n_slider, self.current_row, 1)
        self.n_slider.valueChanged.connect(self.update_labels)

        self.n_label = QLabel(f"n = {self.p.n}")
        self.n_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.n_label, self.current_row, 2)
        self.current_row += 1

        self.mor_label = QLabel(f'meteorological optical range (MOR) = {round(self.p.mor, 2)}m')
        self.mor_label.setAlignment(Qt.AlignCenter)
        self.mor_label.setMaximumSize(self.monitor.width(), self.row_height)
        self.layout.addWidget(self.mor_label, self.current_row, 0, 1, 3)
        self.current_row += 1

        self.alpha_title = QLabel('attenuation coefficient')
        self.alpha_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.alpha_title, self.current_row, 0)

        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setMinimum(int(self.p.alpha_min * self.p.alpha_scale))
        self.alpha_slider.setMaximum(int(self.p.alpha_max * self.p.alpha_scale))
        self.alpha_slider.setValue(int(self.p.alpha * self.p.alpha_scale))

        self.layout.addWidget(self.alpha_slider, self.current_row, 1)
        self.alpha_slider.valueChanged.connect(self.update_labels)

        self.alpha_label = QLabel(f"\u03B1 = {self.p.alpha}")
        self.alpha_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.alpha_label, self.current_row, 2)
        self.current_row += 1

        self.beta_title = QLabel('backscattering coefficient')
        self.beta_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.beta_title, self.current_row, 0)

        self.beta_slider = QSlider(Qt.Horizontal)
        self.beta_slider.setMinimum(int(self.p.beta_min * self.p.beta_scale))
        self.beta_slider.setMaximum(int(self.p.beta_max * self.p.beta_scale))
        self.beta_slider.setValue(int(self.p.beta * self.p.beta_scale))

        self.layout.addWidget(self.beta_slider, self.current_row, 1)
        self.beta_slider.valueChanged.connect(self.update_labels)

        self.beta_label = QLabel(f"\u03B2 = {round(self.p.beta * self.p.mor, 3)} / MOR")
        self.beta_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.beta_label, self.current_row, 2)
        self.current_row += 1

        self.e_p_label = QLabel(f'total pulse energy (E\N{LATIN SUBSCRIPT SMALL LETTER P}) = {round(self.p.e_p * 1e6, 1)} \u03BCJ')
        self.e_p_label.setAlignment(Qt.AlignCenter)
        self.e_p_label.setMaximumSize(self.monitor.width(), self.row_height)
        self.layout.addWidget(self.e_p_label, self.current_row, 0, 1, 3)
        self.current_row += 1

        self.p_0_title = QLabel('pulse peak power')
        self.p_0_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.p_0_title, self.current_row, 0)

        self.p_0_slider = QSlider(Qt.Horizontal)
        self.p_0_slider.setMinimum(int(self.p.p_0_min))
        self.p_0_slider.setMaximum(int(self.p.p_0_max))
        self.p_0_slider.setValue(int(self.p.p_0))

        self.layout.addWidget(self.p_0_slider, self.current_row, 1)
        self.p_0_slider.valueChanged.connect(self.update_labels)

        self.p_0_label = QLabel('P0'.translate(SUB) + f" = {self.p.p_0} W")
        self.p_0_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.p_0_label, self.current_row, 2)
        self.current_row += 1

        self.tau_h_title = QLabel('half-power pulse width')
        self.tau_h_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.tau_h_title, self.current_row, 0)

        self.tau_h_slider = QSlider(Qt.Horizontal)
        self.tau_h_slider.setMinimum(int(self.p.tau_h_min * self.p.tau_h_scale))
        self.tau_h_slider.setMaximum(int(self.p.tau_h_max * self.p.tau_h_scale))
        self.tau_h_slider.setValue(int(self.p.tau_h * self.p.tau_h_scale))

        self.layout.addWidget(self.tau_h_slider, self.current_row, 1)
        self.tau_h_slider.valueChanged.connect(self.update_labels)

        self.tau_h_label = QLabel(f"{TAU_H} = {int(self.p.tau_h * self.p.tau_h_scale)} ns")
        self.tau_h_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.tau_h_label, self.current_row, 2)
        self.current_row += 1

        self.c_a_label = QLabel(f'system constant (C\N{LATIN SUBSCRIPT SMALL LETTER A}) = {round(self.p.c_a)}')
        self.c_a_label.setAlignment(Qt.AlignCenter)
        self.c_a_label.setMaximumSize(self.monitor.width(), self.row_height)
        self.layout.addWidget(self.c_a_label, self.current_row, 0, 1, 3)
        self.current_row += 1

        self.a_r_title = QLabel('aperture area of the receiver')
        self.a_r_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.a_r_title, self.current_row, 0)

        self.a_r_slider = QSlider(Qt.Horizontal)
        self.a_r_slider.setMinimum(int(self.p.a_r_min * self.p.a_r_scale))
        self.a_r_slider.setMaximum(int(self.p.a_r_max * self.p.a_r_scale))
        self.a_r_slider.setValue(int(self.p.a_r * self.p.a_r_scale))

        self.layout.addWidget(self.a_r_slider, self.current_row, 1)
        self.a_r_slider.valueChanged.connect(self.update_labels)

        self.a_r_label = QLabel(f"A\N{LATIN SUBSCRIPT SMALL LETTER R} = {self.p.a_r} m²")
        self.a_r_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.a_r_label, self.current_row, 2)
        self.current_row += 1

        self.l_r_title = QLabel("loss of the receiver's optics")
        self.l_r_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.l_r_title, self.current_row, 0)

        self.l_r_slider = QSlider(Qt.Horizontal)
        self.l_r_slider.setMinimum(int(self.p.l_r_min * self.p.l_r_scale))
        self.l_r_slider.setMaximum(int(self.p.l_r_max * self.p.l_r_scale))
        self.l_r_slider.setValue(int(self.p.l_r * self.p.l_r_scale))

        self.layout.addWidget(self.l_r_slider, self.current_row, 1)
        self.l_r_slider.valueChanged.connect(self.update_labels)

        self.l_r_label = QLabel(f"L\N{LATIN SUBSCRIPT SMALL LETTER R} = {int(self.p.l_r * self.p.l_r_scale)} %")
        self.l_r_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.l_r_label, self.current_row, 2)
        self.current_row += 1

        self.optics_label = QLabel(f'sensor optics')
        self.optics_label.setAlignment(Qt.AlignCenter)
        self.optics_label.setMaximumSize(self.monitor.width(), self.row_height)
        self.layout.addWidget(self.optics_label, self.current_row, 0, 1, 3)
        self.current_row += 1

        self.r_1_title = QLabel("")
        self.r_1_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.r_1_title, self.current_row, 0)

        self.r_1_slider = QSlider(Qt.Horizontal)
        self.r_1_slider.setMinimum(int(self.p.r_1_min * self.p.r_1_scale))
        self.r_1_slider.setMaximum(int(self.p.r_1_max * self.p.r_1_scale))
        self.r_1_slider.setValue(int(self.p.r_1 * self.p.r_1_scale))

        self.layout.addWidget(self.r_1_slider, self.current_row, 1)
        self.r_1_slider.valueChanged.connect(self.update_labels)

        self.r_1_label = QLabel('R1'.translate(SUB) + f" = {self.p.r_1} m")
        self.r_1_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.r_1_label, self.current_row, 2)
        self.current_row += 1

        self.r_2_title = QLabel("")
        self.r_2_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.r_2_title, self.current_row, 0)

        self.r_2_slider = QSlider(Qt.Horizontal)
        self.r_2_slider.setMinimum(int(self.p.r_2_min * self.p.r_2_scale))
        self.r_2_slider.setMaximum(int(self.p.r_2_max * self.p.r_2_scale))
        self.r_2_slider.setValue(int(self.p.r_2 * self.p.r_2_scale))

        self.layout.addWidget(self.r_2_slider, self.current_row, 1)
        self.r_2_slider.valueChanged.connect(self.update_labels)

        self.r_2_label = QLabel('R2'.translate(SUB) + f" = {self.p.r_2} m")
        self.r_2_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.r_2_label, self.current_row, 2)
        self.current_row += 1

        self.beta_0_label = QLabel(f'differential reflextivity of the hard target (\u03B2' + '0)'.translate(SUB) +
                                   f' = {round(self.p.beta_0, 5)}')
        self.beta_0_label.setAlignment(Qt.AlignCenter)
        self.beta_0_label.setMaximumSize(self.monitor.width(), self.row_height)
        self.layout.addWidget(self.beta_0_label, self.current_row, 0, 1, 3)
        self.current_row += 1

        self.r_0_title = QLabel("distance to the hard target")
        self.r_0_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.r_0_title, self.current_row, 0)

        self.r_0_slider = QSlider(Qt.Horizontal)
        self.r_0_slider.setMinimum(self.p.r_0_min)
        self.r_0_slider.setMaximum(self.p.r_0_max)
        self.r_0_slider.setValue(self.p.r_0)

        self.layout.addWidget(self.r_0_slider, self.current_row, 1)
        self.r_0_slider.valueChanged.connect(self.update_labels)

        self.r_0_label = QLabel('R0'.translate(SUB) + f" = {self.p.r_0} m")
        self.r_0_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.r_0_label, self.current_row, 2)
        self.current_row += 1

        self.gamma_title = QLabel("reflextivity of the hard target")
        self.gamma_title.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.gamma_title, self.current_row, 0)

        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setMinimum(int(self.p.gamma_min * self.p.gamma_scale))
        self.gamma_slider.setMaximum(int(self.p.gamma_max * self.p.gamma_scale))
        self.gamma_slider.setValue(int(self.p.gamma * self.p.gamma_scale))

        self.layout.addWidget(self.gamma_slider, self.current_row, 1)
        self.gamma_slider.valueChanged.connect(self.update_labels)

        self.gamma_label = QLabel(f"\u0393 = {self.p.gamma}")
        self.gamma_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.gamma_label, self.current_row, 2)
        self.current_row += 1

        self._update_canvas()


    def toggle_xsi(self) -> None:

        self.p.linear_xsi = not self.p.linear_xsi

        if self.p.linear_xsi:
            self.xsi_btn.setText("linear xsi active")
        else:
            self.xsi_btn.setText("formula xsi active")

        self._update_canvas()


    def toggle_reset(self) -> None: # only resets one value at a time

        self.p = ParameterSet()

        self.r_slider.setValue(self.p.r_range)
        self.n_slider.setValue(self.p.n)
        self.alpha_slider.setValue(int(self.p.alpha * self.p.alpha_scale))
        self.beta_slider.setValue(int(self.p.beta * self.p.beta_scale))
        self.p_0_slider.setValue(self.p.p_0)
        self.tau_h_slider.setValue(int(self.p.tau_h * self.p.tau_h_scale))
        self.a_r_slider.setValue(int(self.p.a_r * self.p.a_r_scale))
        self.l_r_slider.setValue(int(self.p.l_r * self.p.l_r_scale))
        self.r_1_slider.setValue(int(self.p.r_1 * self.p.r_1_scale))
        self.r_2_slider.setValue(int(self.p.r_2 * self.p.r_2_scale))
        self.r_0_slider.setValue(self.p.r_0)
        self.gamma_slider.setValue(int(self.p.gamma * self.p.gamma_scale))

        self.update_labels()


    def update_labels(self) -> None:

        self.p.r_range = self.r_slider.value()
        self.r_label.setText(f"r = {self.p.r_range}")

        self.p.n = self.n_slider.value()
        self.n_label.setText(f"n = {self.p.n}")

        self.p.alpha = self.alpha_slider.value() / self.p.alpha_scale
        self.alpha_label.setText(f"\u03B1 = {self.p.alpha}")

        self.p.mor = np.log(20) / self.p.alpha
        self.mor_label.setText(f'meteorological optical range (MOR) = {round(self.p.mor, 2)}m')

        self.p.beta_scale = 1000 * self.p.mor
        self.p.beta = self.beta_slider.value() / self.p.beta_scale
        self.beta_label.setText(f"\u03B2 = {round(self.p.beta * self.p.mor, 3)} / MOR")

        self.p.p_0 = self.p_0_slider.value()
        self.p_0_label.setText('P0'.translate(SUB) + f" = {self.p.p_0} W")

        self.p.tau_h = self.tau_h_slider.value() / self.p.tau_h_scale
        self.tau_h_label.setText(f"{TAU_H} = {int(self.p.tau_h * self.p.tau_h_scale)} ns")

        self.p.e_p = self.p.p_0 * self.p.tau_h
        self.e_p_label.setText(f'total pulse energy (E\N{LATIN SUBSCRIPT SMALL LETTER P}) = {round(self.p.e_p * 1e6, 1)} \u03BCJ')

        self.p.a_r = self.a_r_slider.value() / self.p.a_r_scale
        self.a_r_label.setText(f"A\N{LATIN SUBSCRIPT SMALL LETTER R} = {self.p.a_r} m²")

        self.p.l_r = self.l_r_slider.value() / self.p.l_r_scale
        self.l_r_label.setText(f"L\N{LATIN SUBSCRIPT SMALL LETTER R} = {int(self.p.l_r * self.p.l_r_scale)} %")

        self.p.c_a = c * self.p.l_r * self.p.a_r / 2
        self.c_a_label.setText(f'system constant (C\N{LATIN SUBSCRIPT SMALL LETTER A}) = {round(self.p.c_a)}')

        self.p.r_1 = self.r_1_slider.value() / self.p.r_1_scale
        self.r_1_label.setText('R1'.translate(SUB) + f" = {self.p.r_1} m")

        self.p.r_2_min = self.p.r_1
        self.p.r_2 = self.r_2_slider.value() / self.p.r_2_scale
        if self.p.r_2 < self.p.r_1:
            self.p.r_2 = self.p.r_1
            self.r_2_slider.setValue(int(self.p.r_2 * self.p.r_2_scale))
        self.r_2_label.setText('R2'.translate(SUB) + f" = {self.p.r_2} m")

        self.p.r_0 = self.r_0_slider.value()
        self.r_0_label.setText('R0'.translate(SUB) + f" = {self.p.r_0} m")

        self.p.gamma = self.gamma_slider.value() / self.p.gamma_scale
        self.gamma_label.setText(f"\u0393 = {self.p.gamma}")

        self.p.beta_0 = self.p.gamma / np.pi
        self.beta_0_label.setText(f'differential reflextivity of the hard target (\u03B2' + '0)'.translate(SUB) +
                                  f' = {round(self.p.beta_0, 5)}')

        self._update_canvas()


    def _update_canvas(self) -> None:

        linewidth = 2
        fontsize = 10

        plt.rcParams["legend.fontsize"] = fontsize

        self._static_ax.clear()
        self._static_ax.set_xlabel('range (m)', fontsize=fontsize)
        self._static_ax.set_ylabel('received power (W)', fontsize=fontsize)
        self._static_ax.grid(linestyle=(0, (1, 10)))

        # change the fontsize of minor ticks label
        self._static_ax.tick_params(axis='both', which='major', labelsize=fontsize)
        self._static_ax.tick_params(axis='both', which='minor', labelsize=fontsize)

        ################
        # P_R_fog_hard #
        ################

        x_list = np.linspace(0, self.p.r_range, self.p.n)
        y_list = self.pool.map(functools.partial(P_R_fog_hard, self.p), x_list)

        # shift x so that the peak of the transmitted pulse is at t=0
        # and the peak response of the hard target is at R_0
        x_list = x_list - self.p.tau_h * c / 2

        self._static_ax.plot(x_list, y_list, linestyle='solid', color='red', linewidth=linewidth)

        ################
        # P_R_fog_soft #
        ################

        x_list = np.linspace(0, self.p.r_range, self.p.n)
        y_list = self.pool.map(functools.partial(P_R_fog_soft, self.p), x_list)

        # shift x so that the peak of the transmitted pulse is at t=0
        # and the peak response of the hard target is at R_0
        x_list = x_list - self.p.tau_h * c / 2

        self._static_ax.plot(x_list, y_list, linestyle=(0, (1, 1)), color='blue', linewidth=linewidth)

        ##########
        # legend #
        ##########

        blue_patch =  mpatches.Patch(color='blue', label=r'$P_{R, fog}^{soft}$')
        red_patch = mpatches.Patch(color='red', label=r'$P_{R, fog}^{hard}$')
        self._static_ax.legend(handles=[blue_patch, red_patch])

        self._static_ax.figure.canvas.draw()


def r_T(p: ParameterSet, R: float = None) -> float:

    if R is None:
        R = p.r_0

    return R * np.tan(p.GAMMA_T / 2) + p.ROH_T


def r_R(p: ParameterSet, R: float = None) -> float:

    if R is None:
        R = p.r_0

    return R * np.tan(p.GAMMA_R / 2) + p.ROH_R


def phi_T(p: ParameterSet, R: float = None) -> float:

    if R is None:
        R = p.r_0

    x = ((r_T(p, R) ** 2) - (r_R(p, R) ** 2) + (p.D ** 2)) / (2 * p.D * r_T(p, R))

    if x < 1:

        if x > -1:

            y = np.arccos(x)

        else:

            y = np.pi

    else:

        y = 0

    return 2 * y


def phi_R(p: ParameterSet, R: float = None) -> float:

    if R is None:
        R = p.r_0

    x = ((r_R(p, R) ** 2) - (r_T(p, R) ** 2) + (p.D ** 2)) / (2 * p.D * r_R(p, R))

    if x < 1:

        if x > -1:

            y = np.arccos(x)

        else:

            y = np.pi

    else:

        y = 0

    return 2 * y


def xsi(p: ParameterSet, R: float = None) -> float:

    if R is None:
        R = p.r_0

    if R <= p.r_1:  # emitted ligth beam from the tansmitter is not captured by the receiver

        return 0

    elif R >= p.r_2:  # emitted ligth beam from the tansmitter is fully captured by the receiver

        return 1

    else:  # emitted ligth beam from the tansmitter is partly captured by the receiver

        if p.linear_xsi:  # use a linear interpolation

            m = (1 - 0) / (p.r_2 - p.r_1)
            b = 0 - (m * p.r_1)
            y = m * R + b

        else:

            y = ((r_T(p, R) ** 2) * (phi_T(p, R) - np.sin(phi_T(p, R)))
                 + (r_R(p, R) ** 2) * (phi_R(p, R) - np.sin(phi_R(p, R)))) / (2 * np.pi * (r_T(p, R) ** 2))

        return y


def xsi_loop(p: ParameterSet, R: np.ndarray) -> np.ndarray:

    xsi_array = np.zeros(R.shape)

    for j, r in enumerate(R):
        xsi_array[j] = xsi(p, r)

    return xsi_array


def inverse_square_modified(p: ParameterSet, R: float, t: np.ndarray) -> np.ndarray:

    arr = np.zeros(t.shape)

    for j, t_star in enumerate(t):

        if t_star >= 2 * (R - p.r_1) / c:  # to avoid infinity * 0

            arr[j] = 0

        else:

            arr[j] = 1 / ((R - (c * t_star) / 2) ** 2)

    return arr


def P_R_clear_hard(p: ParameterSet, R: float) -> float:

    if p.r_0 <= R <= (p.r_0 + c * p.tau_h):

        return p.c_a * p.p_0 * (xsi(p) / (p.r_0 ** 2)) * p.beta_0 \
               * (math.sin((np.pi * (R - p.r_0)) / (c * p.tau_h)) ** 2)

    else:

        return 0


def P_R_clear(p: ParameterSet, R: float) -> float:

    return P_R_clear_hard(p, R)


def P_R_fog_hard(p: ParameterSet, R: float) -> float:

    return np.exp(-2 * p.alpha * p.r_0) * P_R_clear_hard(p, R)


def P_R_fog_soft(p, R: float, n: int = None) -> float:

    if n is None:
        n = p.n

    def integrand(t: np.ndarray) -> np.ndarray:
        arr = (np.sin(np.pi / (2 * p.tau_h) * t) ** 2) \
              * (np.exp(-2 * p.alpha * (R - ((c * t) / 2)))) \
              * inverse_square_modified(p, R, t) \
              * xsi_loop(p, R - ((c * t) / 2)) \
              * np.heaviside(p.r_0 - R + (c * t) / 2, 0)

        return arr

    start = 0
    stop = 2 * p.tau_h

    x = np.linspace(start, stop, n)
    y = integrand(x)

    integral = scipy_integrate.simps(y, x)

    return p.c_a * p.p_0 * p.beta * integral


def P_R_fog(p: ParameterSet, R: float, n: int = None) -> float:

    if n is None:
        n = p.n

    return P_R_fog_soft(p, R, n) + P_R_fog_hard(p, R)


if __name__ == "__main__":

    qapp = QApplication(sys.argv)
    app = ApplicationWindow()
    app.show()
    qapp.exec_()
