# -*- coding: utf-8 -*-
#############
from __future__ import annotations
#############


WolframAlphaAPIKey = ""

from PyQt5 import QtCore, QtGui, QtWidgets, QtSvg
import json, random
import sys, os, subprocess
import qdarktheme
import math
import wolframalpha
import re
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use('QT5Agg')
from matplotlib.figure import Figure
from PyQt5.QtCore import pyqtSlot, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from qtwidgets import toggle, AnimatedToggle
from random import randint
from time import sleep
###########
from typing import *

color1, color2, color3, color4, color5 = "#000000", "#E69E00", "#57B5E8", "#009E73", "#CC78A6"
#Default states for the choice of optimization algorithm
NelderMead = "True"
PSO = "False"


def read_Output(lstIn):
        global ExitCode, IterationNumber, SimplexMinimum, SimplexMean, GrowthPara1, GrowthPara2, GrowthPara3, AgglPara1, AgglPara2
        IterationNumber = int(lstIn[1])
        SimplexMinimum = float(lstIn[2])
        SimplexMean = float(lstIn[3])
        GrowthPara1 = float(lstIn[4])
        GrowthPara2 = float(lstIn[5])
        GrowthPara3 = float(lstIn[6])
        AgglPara1 = float(lstIn[7])
        AgglPara2 = float(lstIn[8])

def extract_numbers(input_string): #Results are generated in the form "value unit (unit in words)" Sometimes they feature a comma, sometimes they dont. This function extracts a float from the string and works for both previously mentioned cases
    pattern = r'\d+\.\d+|\d+'
    matches = re.findall(pattern, input_string)
    
    if matches:
        numbers = [float(match) for match in matches]
        return numbers
    else:
        return None

SimulatedUnitOps = [0, 0, 0, 0] #Crystallization, Filtration, Washing, Drying
FilePathCSD = ""
FilePathNelMead = ""
Confidence = "Data"
ExitCodeCryst, ExitCodeFilt, ExitCodeFiltWash, ExitCodeDry = 0,0,0,0

class HelpCryst_Dialog(QDialog):
        def __init__(self):
                super(HelpCryst_Dialog, self).__init__()
                loadUi(os.path.dirname(__file__) + "\\Windows\\HelpCrystallization.ui", self)
class HelpWash_Dialog(QDialog):
        def __init__(self):
                super(HelpWash_Dialog, self).__init__()
                loadUi(os.path.dirname(__file__) + "\\Windows\\HelpWashing.ui", self)
class HelpDryDialog(QDialog):
        def __init__(self):
                super(HelpDryDialog, self).__init__()
                loadUi(os.path.dirname(__file__) + "\\Windows\\HelpDrying.ui", self)
class HelpFiltDialog(QDialog):
        def __init__(self):
                super(HelpFiltDialog, self).__init__()
                loadUi(os.path.dirname(__file__) + "\\Windows\\HelpFiltration.ui", self)
class HelpNelMeadDialog(QDialog):
        def __init__(self):
                super(HelpNelMeadDialog, self).__init__()
                loadUi(os.path.dirname(__file__) + "\\Windows\\HelpParaFit.ui", self)
#class AboutDialog(QDialog):
#        def __init__(self):
#                super(AboutDialog, self).__init__()
#                loadUi(os.path.dirname(__file__) + "\\Windows\\AboutDialog.ui", self)
class StartCalcHelp(QDialog):
        def __init__(self):
                super(StartCalcHelp, self).__init__()
                loadUi(os.path.dirname(__file__) + "\\Windows\\CalcHelp.ui", self)
class CalcFinishedDialog(QDialog):
        def __init__(self):
                super(CalcFinishedDialog, self).__init__()
                loadUi(os.path.dirname(__file__) + "\\Windows\\CalcFinished.ui", self)
                self.CloseCalcFinished = self.findChild(QtWidgets.QPushButton, "CloseCalcFinished")
                self.CloseCalcFinished.clicked.connect(self.close)

class WolframAlphaWindow(QDialog):
        def __init__(self):
                super(WolframAlphaWindow, self).__init__()
                loadUi(os.path.dirname(__file__) + "\\Windows\\WolframAlpha.ui", self)
                self.GetWolframAlphaData = self.findChild(QtWidgets.QPushButton, "RetrieveWeb")
                self.GetWolframAlphaData.clicked.connect(self.WolframAlphaQuery)

                self.CopyUserInput = self.findChild(QtWidgets.QPushButton, "CopyInput")
                self.CopyUserInput.clicked.connect(self.CopyDataWA)

                self.SolDensityData = self.findChild(QtWidgets.QLineEdit, "DensityLine")

                self.HeatCapaData = self.findChild(QtWidgets.QLineEdit, "HeatCapaLine")
                
                self.GasDensityData = self.findChild(QtWidgets.QLineEdit, "GasDensityLine")

        def WolframAlphaQuery(self):
                client = wolframalpha.Client(WolframAlphaAPIKey)
                res1 = client.query("density of {} at {} C".format(Crystal, TDry))
                res2 = client.query("heat capacity of {} at {} C".format(Crystal, TDry))
                res3 = client.query("denstiy of {} at {} C".format(DryingGas, TDry))

                answer1 = next(res1.results).text
                if answer1 == "(data not available)":
                        self.SolDensityData.setText("No data found")
                else:
                        Numbers = extract_numbers(answer1)
                        self.SolDensityData.setText(str(Numbers[0]))
                answer2 = next(res2.results).text
                if answer2 == "(data not available)":
                        self.HeatCapaData.setText("No data found")
                else:
                        Numbers2 = extract_numbers(answer2)
                        self.HeatCapaData.setText(str(Numbers2[0]))
                answer3 = next(res3.results).text
                if answer3 == "(data not available)":
                        self.GasDensityData.setText("No data found")
                else:
                        Numbers3 = extract_numbers(answer3)
                        self.GasDensityData.setText(str(Numbers3[0]))
        
        def CopyDataWA(self):
                HeatCapaCrystVar = self.HeatCapaData.text()
                GasDensityVar = self.GasDensityData.text()
                CrystDensityVar = self.SolDensityData.text()
                JSON_file = open(os.path.dirname(__file__) + "\\DWSIM\\Input.json")
                parsed_data = json.load(JSON_file)
                parsed_data["CrystalDensity"] = CrystDensityVar
                parsed_data["GasDensity"] = GasDensityVar
                parsed_data["HeatCapaCryst"] = HeatCapaCrystVar
                with open(os.path.dirname(__file__) + "\\DWSIM\\Input.json", "w") as json_file:
                        json.dump(parsed_data, json_file, indent=4)
                


##########################################################
class SubprocessThread(QThread):
        output_received = pyqtSignal(object)

        def __init__(self, command):
                super().__init__()
                self.command = command

        def run(self):
                with subprocess.Popen(self.command, stdout=subprocess.PIPE, universal_newlines=True, bufsize=1, text=True) as process:
                        for line in process.stdout:
                                self.output_received.emit(eval(line.strip()))
                

 
############################################################

class CSD_MyMplCanvas(FigureCanvasQTAgg):
        def __init__(self, parent=None):

                fig = Figure()
                FigureCanvasQTAgg.__init__(self, fig)
                self.axes = fig.add_subplot(111)
                FigureCanvasQTAgg.__init__(self, fig)
                FigureCanvasQTAgg.setSizePolicy(self,
                                                QSizePolicy.Expanding,
                                                QSizePolicy.Expanding)
                FigureCanvasQTAgg.updateGeometry(self)
                self.CSD_compute_initial_figure()       
        def CSD_compute_initial_figure(self):
                pass

class CSD_MyStaticMplCanvas(CSD_MyMplCanvas):
        def CSD_compute_initial_figure(self):
                #Default particle size Q0 distribution
                self.axes.clear()
                CSD = [
                        50.5427276198695,
                        58.0583480740074,
                        66.6915289264575,
                        76.608449570059,
                        88,
                        101.085455239739,
                        116.116696148015,
                        133.383057852915,
                        153.216899140118,
                        176,
                        202.170910479478,
                        232.23339229603,
                        266.76611570583,
                        306.433798280236,
                        352,
                        404.341820958957,
                        464.466784592059,
                        533.532231411661,
                        612.867596560472,
                        704.000000000001,
                        808.683641917914,
                        928.933569184119,
                        1067.06446282332,
                        1225.73519312095,
                        1408,
                        1617.36728383583,
                        1857.86713836824,
                        2134.12892564665,
                        2451.47038624189,
                        2816.00000000001
                        ]
                Q0 = [
                        2.91374411262628e-05,
                        0.0171675276446912,
                        3.39720064129196,
                        48194.7534246872,
                        31798.1628538781,
                        76922.8669618511,
                        87659.3771833807,
                        111724.185765209,
                        54814.8657883227,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                        ]
                
                self.axes.plot(CSD, Q0,"k--")
                self.axes.set_xscale("log")
                self.axes.scatter(CSD, Q0,c="black",linewidths=0.5)
                self.draw()
        def CSD_update_initial_figure(self, CSD_new, Q0_new):
                self.axes.plot(CSD_new, Q0_new,"#84bc34", linestyle="--")
                self.axes.scatter(CSD_new, Q0_new,c="#84bc34",linewidths=0.5)
                self.draw()
        def CSD_browsefiles(self):
                fname = QFileDialog.getOpenFileName(self, "Choose new initial CSD", os.path.dirname(__file__), "Excel files (*.xlsx)")
                global FilePathCSD
                FilePathCSD = fname[0]
                CSD_new = pd.read_excel(fname[0])
                CSD_MyStaticMplCanvas.CSD_update_initial_figure(self, CSD_new["Diameter"], CSD_new["Number"])
                JSON_file = open(os.path.dirname(__file__) + "\\DWSIM\\Input.json")
                parsed_data = json.load(JSON_file)
                parsed_data["Length"] = CSD_new["Diameter"]
                parsed_data["CSD_init"] = CSD_new["Number"]
                parsed_data["ClassWidth"] = CSD_new["ClassWidth"]
                with open(os.path.dirname(__file__) + "\\DWSIM\\Input.json", "w") as json_file:
                        json.dump(parsed_data, json_file, indent=4)
                


class MyFigureCanvas(FigureCanvasQTAgg):
    '''
    This is the FigureCanvas in which the live plot for the Nelder Mead fitting algorithm is drawn.

    '''
    def __init__(self, x_len:int, y_range:List, interval:int) -> None:
        '''
        :param x_len:       The nr of data points shown in one plot.
        :param y_range:     Range on y-axis.
        :param interval:    Get a new datapoint every .. milliseconds.

        '''
        super().__init__(mpl.figure.Figure())
        # Range settings
        #self._x_len_ = x_len
        self._y_range_ = y_range

        # Store two lists _x_ and _y_
        self._x_ = []
        self._y_ = []
        self._y2_ = []

        # Store a figure ax
        self._ax_ = self.figure.subplots()
        self.figure.tight_layout(pad = 6.7, rect=[0, -0.1, 1, 1.1])
        return

    def _update_canvas_(self) -> None:
        '''
        This function is called by the handle_output function as soon as an iteration is finished and a new output is printed from the subprocess
        '''
        self._x_.append(IterationNumber)
        self._y_.append(round(SimplexMinimum, 4))     # Add new datapoint
        self._y2_.append(round(SimplexMean, 4))
        #self._y_ = self._y_[-self._x_len_:]                 # Truncate list _y_
        self._ax_.clear()                                   # Clear ax
        line, = self._ax_.plot(self._x_, self._y_)                  # Plot y(x)
        line2, = self._ax_.plot(self._x_, self._y2_)
        self._ax_.set_ylim(ymin=self._y_range_[0], ymax=self._y_range_[1])
        self._ax_.legend([line, line2],
                                 ["Minimum", "Average"])
        self.draw()


class MyFigureCanvasValue(FigureCanvasQTAgg):
        def __init__(self) -> None:
                super().__init__(mpl.figure.Figure())
                self._x_ = []
                self._y1_ = []
                self._y2_ = []
                self._y3_ = []
                self._y4_ = []
                self._y5_ = []
                #Create new axes for each parameter
                self._ax_ = self.figure.subplots()
                self._ax2_ = self._ax_.twinx()
                self._ax3_ = self._ax_.twinx()
                self._ax4_ = self._ax_.twinx()
                self._ax5_ = self._ax_.twinx()
                
                self.figure.tight_layout(pad=6.7, w_pad=0, h_pad=1.0, rect=[-0.1,-0.1,0.9,1.1])
                #self.figure.subplots_adjust(wspace=1)
                #Create labels for each axis
                #self._ax_.set_ylabel("Growth Parameter 1")
                #self._ax2_.set_ylabel("Growth Parameter 2")
                #self._ax3_.set_ylabel("Growth Parameter 3")
                #self._ax4_.set_ylabel("Agglomeration Parameter 1")
                #self._ax5_.set_ylabel("Agglomeration Parameter 2")

                self._ax_.set_ylim(ymin=0, ymax=10)
                self._ax2_.set_ylim(ymin=0 ,ymax=10000)
                self._ax3_.set_ylim(ymin=0 ,ymax=2)
                self._ax4_.set_ylim(ymin=0 ,ymax=200)
                self._ax5_.set_ylim(ymin=0 ,ymax=1)

                self._ax2_.spines["right"].set_color(color2)
                self._ax3_.spines["right"].set_color(color3)
                self._ax4_.spines["right"].set_color(color4)
                self._ax5_.spines["right"].set_color(color5)

                self._ax2_.spines["right"].set_position(("outward", 0))
                self._ax3_.spines["right"].set_position(("outward", 40))
                self._ax4_.spines["right"].set_position(("outward", 75))
                self._ax5_.spines["right"].set_position(("outward", 105))
                return
        
        def _update_canvas_NM_(self) -> None:
                self._x_.append(IterationNumber)
                self._y1_.append(GrowthPara1)
                self._y2_.append(GrowthPara2)
                self._y3_.append(GrowthPara3)
                self._y4_.append(AgglPara1)
                self._y5_.append(AgglPara2)

                self._ax_.clear()
                self._ax2_.clear()
                self._ax3_.clear()
                self._ax4_.clear()
                self._ax5_.clear()

                if NelderMead == "True":
                        self._ax_.set_ylim(ymin=0, ymax=100)
                        self._ax2_.set_ylim(ymin=0 ,ymax=100000)
                        self._ax3_.set_ylim(ymin=0 ,ymax=2)
                        self._ax4_.set_ylim(ymin=0 ,ymax=250)
                        self._ax5_.set_ylim(ymin=0 ,ymax=0.001)
                else:
                        self._ax_.set_ylim(ymin=0, ymax=1000)
                        self._ax2_.set_ylim(ymin=0 ,ymax=5)
                        self._ax3_.set_ylim(ymin=0 ,ymax=2)
                        self._ax4_.set_ylim(ymin=0 ,ymax=250)
                        self._ax5_.set_ylim(ymin=0 ,ymax=0.001)

                self._ax2_.spines["right"].set_color(color2)
                self._ax3_.spines["right"].set_color(color3)
                self._ax4_.spines["right"].set_color(color4)
                self._ax5_.spines["right"].set_color(color5)

                self._ax2_.spines["right"].set_position(("outward", 0))
                self._ax3_.spines["right"].set_position(("outward", 40))
                self._ax4_.spines["right"].set_position(("outward", 75))
                self._ax5_.spines["right"].set_position(("outward", 105))

                line1, = self._ax_.plot(self._x_, self._y1_, color=color1)
                line2, = self._ax2_.plot(self._x_, self._y2_, color=color2)
                line3, = self._ax3_.plot(self._x_, self._y3_, color=color3)
                line4, = self._ax4_.plot(self._x_, self._y4_, color=color4)
                line5, = self._ax5_.plot(self._x_, self._y5_, color=color5)

                self._ax_.legend([line1, line2, line3, line4, line5],
                                 ["Growth Parameter 1", "Growth Parameter 2", "Growth Parameter 3", "Agglomeration Parameter 1", "Agglomeration Parameter 2"])
                self.draw()



class Ui_mainWindow(QtWidgets.QMainWindow):
        def setupUi(self, mainWindow):
        
                mainWindow.setObjectName("mainWindow")
                mainWindow.setFixedSize(1028, 764)
                font = QtGui.QFont()
                font.setFamily("Arial")
                mainWindow.setFont(font)
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(os.path.dirname(__file__)+"\\Graphics\\AD2.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)      
                mainWindow.setWindowIcon(icon)
                self.centralwidget = QtWidgets.QWidget(mainWindow)
                self.centralwidget.setObjectName("centralwidget")
                self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
                self.tabWidget.setGeometry(QtCore.QRect(10, 10, 1001, 721))
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold")
                font.setPointSize(10)
                font.setBold(False)
                font.setItalic(False)
                font.setWeight(9)

                self.tabWidget.setFont(font)
                self.tabWidget.setToolTipDuration(11)
                self.tabWidget.setStyleSheet("font-weight: 900; color: black;\n"
                                        "font: 75 10pt \"Segoe UI Semibold\";\n"
                                        "\n"
                                        "")
                self.tabWidget.setObjectName("tabWidget")

                self.InputTab = QtWidgets.QWidget()
                self.InputTab.setObjectName("InputTab")

                self.groupBox = QtWidgets.QGroupBox(self.InputTab)
                self.groupBox.setGeometry(QtCore.QRect(10, 10, 476, 311))
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold")
                font.setPointSize(10)
                font.setBold(False)
                font.setItalic(False)
                font.setWeight(9)
                self.groupBox.setFont(font)
                self.groupBox.setAutoFillBackground(False)
                self.groupBox.setStyleSheet(u"QGroupBox { \n"
                                        "     border: 1px solid black; \n"
                                        "     border-radius: 5px; \n"
                                        "background-color: white;}\n"
                                        "QGroupBox::title {\n"
                                        "    subcontrol-origin: margin;\n"
                                        "    left: 10px;\n"
                                        "    padding: -6px 0px 0 0px;\n"
                                        "	font-weight: 900;\n"
                                        "	color: #84bc34;\n"
                                        "	font: 75 10pt \"Segoe UI Semibold\";\n"
                                        "}")
                self.groupBox.setObjectName("groupBox")

                self.HelpCrystal = QtWidgets.QToolButton(self.groupBox)
                self.HelpCrystal.setGeometry(QtCore.QRect(10, 279, 27, 22))
                self.HelpCrystal.setAutoFillBackground(False)
                self.HelpCrystal.setStyleSheet("font-weight: bold; color: black")
                self.HelpCrystal.setObjectName("HelpCrystal")
                self.HelpCrystal.clicked.connect(self.executeCrystHelpUIWindow)

                self.CheckCrystal = QtWidgets.QCheckBox(self.groupBox)
                self.CheckCrystal.setGeometry(QtCore.QRect(225, 10, 241, 20))
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold")
                font.setPointSize(10)
                font.setBold(True)
                font.setItalic(False)
                font.setWeight(75)
                self.CheckCrystal.setFont(font)
                self.CheckCrystal.setToolTipDuration(-1)
                self.CheckCrystal.setLayoutDirection(QtCore.Qt.RightToLeft)
                self.CheckCrystal.setStyleSheet("color: black; font-weight: bold")
                self.CheckCrystal.setObjectName("CheckCrystal")
                self.CheckCrystal.stateChanged.connect(self.CheckCryst)

                self.StartTempIn = QtWidgets.QLineEdit(self.groupBox)
                self.StartTempIn.setGeometry(QtCore.QRect(160, 40, 110, 22))
                self.StartTempIn.setToolTipDuration(9)
                self.StartTempIn.setStyleSheet("color: black")
                self.StartTempIn.setText("")
                self.StartTempIn.setObjectName("StartTempIn")

                self.label_2 = QtWidgets.QLabel(self.groupBox)
                self.label_2.setGeometry(QtCore.QRect(10, 40, 141, 22))
                self.label_2.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_2.setStyleSheet("color: black")
                self.label_2.setObjectName("label_2")

                self.label_3 = QtWidgets.QLabel(self.groupBox)
                self.label_3.setGeometry(QtCore.QRect(10, 67, 141, 22))
                self.label_3.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_3.setStyleSheet("color: black")
                self.label_3.setObjectName("label_3")

                self.EndTempIn = QtWidgets.QLineEdit(self.groupBox)
                self.EndTempIn.setGeometry(QtCore.QRect(160, 67, 110, 22))
                self.EndTempIn.setStyleSheet("color: black")
                self.EndTempIn.setText("")
                self.EndTempIn.setObjectName("EndTempIn")

                self.CrModulNr = QtWidgets.QLineEdit(self.groupBox)
                self.CrModulNr.setGeometry(QtCore.QRect(160, 94, 110, 22))
                self.CrModulNr.setStyleSheet("color: black")
                self.CrModulNr.setText("")
                self.CrModulNr.setObjectName("CrModulNr")
                self.CrModulNr.textChanged.connect(self.SyncModulNr1)

                self.label_4 = QtWidgets.QLabel(self.groupBox)
                self.label_4.setGeometry(QtCore.QRect(10, 94, 141, 22))
                self.label_4.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_4.setStyleSheet("color: black")
                self.label_4.setObjectName("label_4")

                self.TempProf = QtWidgets.QComboBox(self.groupBox)
                self.TempProf.setGeometry(QtCore.QRect(160, 121, 110, 22))
                self.TempProf.setStyleSheet("color:black;")
                self.TempProf.setObjectName("TempProf")
                self.TempProf.addItem("")
                self.TempProf.addItem("")
                self.TempProf.addItem("")
                self.TempProf.currentTextChanged.connect(self.SyncProf1)

                self.label_5 = QtWidgets.QLabel(self.groupBox)
                self.label_5.setGeometry(QtCore.QRect(10, 121, 141, 22))
                self.label_5.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_5.setStyleSheet("color: black")
                self.label_5.setObjectName("label_5")

                self.label_8 = QtWidgets.QLabel(self.groupBox)
                self.label_8.setGeometry(QtCore.QRect(10, 148, 141, 22))
                self.label_8.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_8.setStyleSheet("color: black")
                self.label_8.setObjectName("label_8")

                self.AreaFactor = QtWidgets.QLineEdit(self.groupBox)
                self.AreaFactor.setGeometry(QtCore.QRect(160, 148, 110, 22))
                self.AreaFactor.setStyleSheet("color: black")
                self.AreaFactor.setText("")
                self.AreaFactor.setObjectName("AreaFactor")

                self.label_22 = QLabel(self.groupBox)
                self.label_22.setObjectName(u"label_22")
                self.label_22.setGeometry(QtCore.QRect(10, 175, 141, 22))
                self.label_22.setLayoutDirection(Qt.LeftToRight)
                self.label_22.setStyleSheet(u"color: black")

                self.SeedMass = QLineEdit(self.groupBox)
                self.SeedMass.setObjectName(u"SeedMass")
                self.SeedMass.setGeometry(QtCore.QRect(160, 175, 110, 22))
                self.SeedMass.setStyleSheet(u"color: black")

                self.label_43 = QtWidgets.QLabel(self.groupBox)
                self.label_43.setObjectName(u"label_43")
                self.label_43.setGeometry(QtCore.QRect(10, 202, 141, 22))
                self.label_43.setLayoutDirection(Qt.LeftToRight)

                self.GrowthKin = QtWidgets.QComboBox(self.groupBox)
                self.GrowthKin.addItem("")
                self.GrowthKin.addItem("")
                self.GrowthKin.setObjectName(u"GrowthKin")
                self.GrowthKin.setGeometry(QtCore.QRect(160, 202, 110, 22))

                self.groupBox_3 = QtWidgets.QGroupBox(self.InputTab)
                self.groupBox_3.setGeometry(QtCore.QRect(508, 10, 476, 311))
                self.groupBox_3.setLayoutDirection(QtCore.Qt.RightToLeft)
                self.groupBox_3.setStyleSheet(u"QGroupBox { \n"
                        "     border: 1px solid black; \n"
                        "     border-radius: 5px; \n"
                        "background-color: white;}\n"
                        "QGroupBox::title {\n"
                        "    subcontrol-origin: margin;\n"
                        "    left: 10px;\n"
                        "    padding: -6px 0px 0 0px;\n"
                        "	font-weight: 900;\n"
                        "	color: #84bc34;\n"
                        "	font: 75 10pt \"Segoe UI Semibold\";\n"
                        "}")
                self.groupBox_3.setObjectName("groupBox_3")

                self.groupBox_4 = QtWidgets.QGroupBox(self.groupBox_3)
                self.groupBox_4.setGeometry(QtCore.QRect(470, 300, 481, 301))
                self.groupBox_4.setObjectName("groupBox_4")
                self.groupBox_4.setStyleSheet(u"QGroupBox { \n"
                        "     border: 1px solid black; \n"
                        "     border-radius: 5px; \n"
                        "background-color: white;}\n"
                        "QGroupBox::title {\n"
                        "    subcontrol-origin: margin;\n"
                        "    left: 10px;\n"
                        "    padding: -6px 0px 0 0px;\n"
                        "	font-weight: 900;\n"
                        "	color: #84bc34;\n"
                        "	font: 75 10pt \"Segoe UI Semibold\";\n"
                        "}")
                
                self.HelpFiltration = QtWidgets.QToolButton(self.groupBox_3)
                self.HelpFiltration.setGeometry(QtCore.QRect(439, 279, 27, 22))
                self.HelpFiltration.setStyleSheet("font-weight: bold; color: black")
                self.HelpFiltration.setObjectName("HelpFiltration")
                self.HelpFiltration.clicked.connect(self.executeFiltHelpUIWindow)

                self.CheckFiltration = QtWidgets.QCheckBox(self.groupBox_3)
                self.CheckFiltration.setGeometry(QtCore.QRect(10, 10, 241, 20))
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold")
                font.setPointSize(10)
                font.setBold(True)
                font.setItalic(False)
                font.setWeight(75)
                self.CheckFiltration.setFont(font)
                self.CheckFiltration.setToolTipDuration(-7)
                self.CheckFiltration.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.CheckFiltration.setStyleSheet("color: black; font-weight: bold")
                self.CheckFiltration.setObjectName("CheckFiltration")
                self.CheckFiltration.toggled.connect(
                        lambda checked: not checked and self.CheckWashing.setChecked(False)
                )
                self.CheckFiltration.toggled.connect(
                        lambda checked: not checked and self.CheckDrying.setChecked(False)
                )
                self.CheckFiltration.stateChanged.connect(self.CheckFilt)

                self.FiltrationPressure = QtWidgets.QLineEdit(self.groupBox_3)
                self.FiltrationPressure.setGeometry(QtCore.QRect(356, 40, 110, 22))
                self.FiltrationPressure.setToolTipDuration(9)
                self.FiltrationPressure.setStyleSheet("color: black")
                self.FiltrationPressure.setText("")
                self.FiltrationPressure.setObjectName("FiltrationPressure")

                self.label_12 = QtWidgets.QLabel(self.groupBox_3)
                self.label_12.setGeometry(QtCore.QRect(206, 40, 141, 22))
                self.label_12.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_12.setStyleSheet("color: black")
                self.label_12.setObjectName("label_12")

                self.label_13 = QtWidgets.QLabel(self.groupBox_3)
                self.label_13.setGeometry(QtCore.QRect(206, 67, 141, 22))
                self.label_13.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_13.setStyleSheet("color: black")
                self.label_13.setObjectName("label_13")

                self.FiltrationTime = QtWidgets.QLineEdit(self.groupBox_3)
                self.FiltrationTime.setGeometry(QtCore.QRect(356, 67, 110, 22))
                self.FiltrationTime.setToolTipDuration(9)
                self.FiltrationTime.setStyleSheet("color: black")
                self.FiltrationTime.setText("")
                self.FiltrationTime.setObjectName("FiltrationTime")

                self.label_26 = QLabel(self.groupBox_3)
                self.label_26.setObjectName(u"label_26")
                self.label_26.setGeometry(QtCore.QRect(206, 148, 141, 22))
                self.label_26.setLayoutDirection(Qt.LeftToRight)
                self.label_26.setStyleSheet(u"color: black")

                self.FiltTemperature = QLineEdit(self.groupBox_3)
                self.FiltTemperature.setObjectName(u"FiltTemperature")
                self.FiltTemperature.setGeometry(QtCore.QRect(356, 148, 110, 22))
                self.FiltTemperature.setToolTipDuration(9)
                self.FiltTemperature.setStyleSheet(u"color: black")

                self.groupBox_5 = QtWidgets.QGroupBox(self.InputTab)
                self.groupBox_5.setGeometry(QtCore.QRect(10, 333, 476, 311))
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold")
                font.setPointSize(10)
                font.setBold(False)
                font.setItalic(False)
                font.setWeight(9)
                self.groupBox_5.setFont(font)
                self.groupBox_5.setStyleSheet(u"QGroupBox { \n"
                                        "     border: 1px solid black; \n"
                                        "     border-radius: 5px; \n"
                                        "background-color: white;}\n"
                                        "QGroupBox::title {\n"
                                        "    subcontrol-origin: margin;\n"
                                        "    left: 10px;\n"
                                        "    padding: -6px 0px 0 0px;\n"
                                        "	font-weight: 900;\n"
                                        "	color: #84bc34;\n"
                                        "	font: 75 10pt \"Segoe UI Semibold\";\n"
                                        "}")
                self.groupBox_5.setObjectName("groupBox_5")
                
                self.HelpWashing = QtWidgets.QToolButton(self.groupBox_5)
                self.HelpWashing.setGeometry(QtCore.QRect(10, 279, 27, 22))
                self.HelpWashing.setAutoFillBackground(False)
                self.HelpWashing.setStyleSheet("font-weight: bold; color: black")
                self.HelpWashing.setObjectName("HelpWashing")
                self.HelpWashing.clicked.connect(self.executeWashHelpUIWindow)

                self.CheckWashing = QtWidgets.QCheckBox(self.groupBox_5)
                self.CheckWashing.setGeometry(QtCore.QRect(225, 279, 241, 20))
                self.CheckWashing.toggled.connect(
                        lambda checked: checked and self.CheckFiltration.setChecked(True)
                )
                self.CheckWashing.stateChanged.connect(self.CheckWash)
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold")
                font.setPointSize(10)
                font.setBold(True)
                font.setItalic(False)
                font.setWeight(75)
                self.CheckWashing.setFont(font)
                self.CheckWashing.setToolTipDuration(-7)
                self.CheckWashing.setLayoutDirection(QtCore.Qt.RightToLeft)
                self.CheckWashing.setStyleSheet("color: black; font-weight: bold")
                self.CheckWashing.setObjectName("CheckWashing")

                self.label_14 = QtWidgets.QLabel(self.groupBox_5)
                self.label_14.setGeometry(QtCore.QRect(10, 195, 141, 22))
                self.label_14.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_14.setStyleSheet("color: black")
                self.label_14.setObjectName("label_14")

                self.WashTime = QtWidgets.QLineEdit(self.groupBox_5)
                self.WashTime.setGeometry(QtCore.QRect(160, 195, 110, 22))
                self.WashTime.setToolTipDuration(9)
                self.WashTime.setStyleSheet("color: black")
                self.WashTime.setText("")
                self.WashTime.setObjectName("WashTime")

                self.label_15 = QtWidgets.QLabel(self.groupBox_5)
                self.label_15.setGeometry(QtCore.QRect(10, 222, 141, 22))
                self.label_15.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_15.setStyleSheet("color: black")
                self.label_15.setObjectName("label_15")

                self.WashFlowRate = QtWidgets.QLineEdit(self.groupBox_5)
                self.WashFlowRate.setGeometry(QtCore.QRect(160, 222, 110, 22))
                self.WashFlowRate.setToolTipDuration(9)
                self.WashFlowRate.setStyleSheet("color: black")
                self.WashFlowRate.setText("")
                self.WashFlowRate.setObjectName("WashFlowRate")

                self.WashPressure = QLineEdit(self.groupBox_5)
                self.WashPressure.setObjectName(u"WashPressure")
                self.WashPressure.setGeometry(QtCore.QRect(160, 249, 110, 22))
                self.WashPressure.setToolTipDuration(9)
                self.WashPressure.setStyleSheet(u"color: black")

                self.label_25 = QLabel(self.groupBox_5)
                self.label_25.setObjectName(u"label_25")
                self.label_25.setGeometry(QtCore.QRect(10, 249, 141, 22))
                self.label_25.setLayoutDirection(Qt.LeftToRight)
                self.label_25.setStyleSheet(u"color: black")

                self.groupBox_7 = QtWidgets.QGroupBox(self.InputTab)
                self.groupBox_7.setGeometry(QtCore.QRect(508, 333, 476, 311))
                self.groupBox_7.setLayoutDirection(QtCore.Qt.RightToLeft)
                self.groupBox_7.setStyleSheet(u"QGroupBox { \n"
                                        "     border: 1px solid black; \n"
                                        "     border-radius: 5px; \n"
                                        "background-color: white;}\n"
                                        "QGroupBox::title {\n"
                                        "    subcontrol-origin: margin;\n"
                                        "    left: 10px;\n"
                                        "    padding: -6px 0px 0 0px;\n"
                                        "	font-weight: 900;\n"
                                        "	color: #84bc34;\n"
                                        "	font: 75 10pt \"Segoe UI Semibold\";\n"
                                        "}")
                self.groupBox_7.setObjectName("groupBox_7")

                self.groupBox_8 = QtWidgets.QGroupBox(self.groupBox_7)
                self.groupBox_8.setGeometry(QtCore.QRect(470, 300, 481, 301))
                self.groupBox_8.setObjectName("groupBox_8")

                self.HelpDrying = QtWidgets.QToolButton(self.groupBox_7)
                self.HelpDrying.setGeometry(QtCore.QRect(439, 279, 27, 22))
                self.HelpDrying.setStyleSheet("font-weight: bold; color: black")
                self.HelpDrying.setObjectName("HelpDrying")
                self.HelpDrying.clicked.connect(self.executeDryHelpUIWindow)

                self.CheckDrying = QtWidgets.QCheckBox(self.groupBox_7)
                self.CheckDrying.setGeometry(QtCore.QRect(10, 279, 241, 20))
                self.CheckDrying.toggled.connect(
                        lambda checked: checked and self.CheckFiltration.setChecked(True)
                )
                self.CheckDrying.stateChanged.connect(self.CheckDry)
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold")
                font.setPointSize(10)
                font.setBold(True)
                font.setItalic(False)
                font.setWeight(75)
                self.CheckDrying.setFont(font)
                self.CheckDrying.setToolTipDuration(-7)
                self.CheckDrying.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.CheckDrying.setStyleSheet("color: black; font-weight: bold")
                self.CheckDrying.setObjectName("CheckDrying")

                self.DryingTemp = QtWidgets.QLineEdit(self.groupBox_7)
                self.DryingTemp.setGeometry(QtCore.QRect(356, 222, 110, 22))
                self.DryingTemp.setToolTipDuration(9)
                self.DryingTemp.setStyleSheet("color: black")
                self.DryingTemp.setText("")
                self.DryingTemp.setObjectName("DryingTemp")

                self.label_16 = QtWidgets.QLabel(self.groupBox_7)
                self.label_16.setGeometry(QtCore.QRect(206, 222, 141, 22))
                self.label_16.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_16.setStyleSheet("color: black")
                self.label_16.setObjectName("label_16")

                self.DryGasPres = QtWidgets.QLineEdit(self.groupBox_7)
                self.DryGasPres.setGeometry(QtCore.QRect(356, 249, 110, 22))
                self.DryGasPres.setToolTipDuration(9)
                self.DryGasPres.setStyleSheet("color: black")
                self.DryGasPres.setText("")
                self.DryGasPres.setObjectName("DryGasPres")

                self.label_17 = QtWidgets.QLabel(self.groupBox_7)
                self.label_17.setGeometry(QtCore.QRect(206, 249, 141, 22))
                self.label_17.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_17.setStyleSheet("color: black")
                self.label_17.setObjectName("label_17")

                self.label = QtWidgets.QLabel(self.InputTab)
                self.label.setGeometry(QtCore.QRect(272, 110, 450, 450))
                self.label.setStyleSheet(" color: black;\n"
                "    border: 2px solid black;\n"
                "    border-radius: 225px;\n"
                "    border-style: outset;\n"
                "    padding: 5px;\n"
                "background-color: white;")
                self.label.setText("")
                self.label.setPixmap(QtGui.QPixmap(os.path.dirname(__file__) + "\\Graphics\\FilterBeltCrystallizer.png"))
                self.label.setScaledContents(True)
                self.label.setObjectName("label")

                self.CopyData = QtWidgets.QPushButton(self.InputTab)
                self.CopyData.setGeometry(QtCore.QRect(437, 656, 120, 31))
                self.CopyData.setStyleSheet("font-weight: bold")
                self.CopyData.setObjectName("CopyData")
                self.CopyData.clicked.connect(self.CopyData_ToJSON)

                self.label_23 = QLabel(self.groupBox_3)
                self.label_23.setObjectName(u"label_23")
                self.label_23.setGeometry(QtCore.QRect(206, 94, 141, 22))
                self.label_23.setLayoutDirection(Qt.LeftToRight)
                self.label_23.setStyleSheet(u"color: black")

                self.FiltSlope = QLineEdit(self.groupBox_3)
                self.FiltSlope.setObjectName(u"FiltSlope")
                self.FiltSlope.setGeometry(QtCore.QRect(356, 94, 110, 22))
                self.FiltSlope.setToolTipDuration(9)
                self.FiltSlope.setStyleSheet(u"color: black")

                self.label_24 = QLabel(self.groupBox_3)
                self.label_24.setObjectName(u"label_24")
                self.label_24.setGeometry(QtCore.QRect(206, 121, 141, 22))
                self.label_24.setLayoutDirection(Qt.LeftToRight)
                self.label_24.setStyleSheet(u"color: black")

                self.FiltYintercept = QLineEdit(self.groupBox_3)
                self.FiltYintercept.setObjectName(u"FiltYintercept")
                self.FiltYintercept.setGeometry(QtCore.QRect(356, 121, 110, 22))
                self.FiltYintercept.setToolTipDuration(9)
                self.FiltYintercept.setStyleSheet(u"color: black")

                self.ConfidenceToggle = AnimatedToggle(self.groupBox_3, checked_color="#84bc34")
                self.ConfidenceToggle.setObjectName(u"ConfidenceToggle")
                self.ConfidenceToggle.setGeometry(QtCore.QRect(356,176,60,30))
                self.ConfidenceToggle.setChecked(True)
                self.ConfidenceToggle.stateChanged.connect(self.FiltrConfi)

                self.Confidence = QtWidgets.QLabel(self.groupBox_3)
                self.Confidence.setObjectName(u"Confidence")
                self.Confidence.setGeometry(QtCore.QRect(206,180,141,22))
                self.Confidence.setLayoutDirection(Qt.LeftToRight)
                self.Confidence.setStyleSheet(u"color: black;\n"
                        "font: 75 10pt \\\"Segoe UI Semibold\\\";")

                self.tabWidget.addTab(self.InputTab, "")
                self.SubstanceDataTab = QtWidgets.QWidget()
                self.SubstanceDataTab.setObjectName("SubstanceDataTab")

                self.groupBox_6 = QtWidgets.QGroupBox(self.SubstanceDataTab)
                self.groupBox_6.setGeometry(QtCore.QRect(10, 370, 481, 251))
                self.groupBox_6.setStyleSheet(u"QGroupBox { \n"
                                        "     border: 1px solid black; \n"
                                        "     border-radius: 5px; \n"
                                        "background-color: white;}\n"
                                        "QGroupBox::title {\n"
                                        "    subcontrol-origin: margin;\n"
                                        "    left: 10px;\n"
                                        "    padding: -6px 0px 0 0px;\n"
                                        "	font-weight: 900;\n"
                                        "	color: #84bc34;\n"
                                        "	font: 75 10pt \"Segoe UI Semibold\";\n"
                                        "}")

                self.label_9 = QtWidgets.QLabel(self.groupBox_6)
                self.label_9.setGeometry(QtCore.QRect(10, 80, 411, 161))
                self.label_9.setWordWrap(True)
                self.label_9.setObjectName("label_9")
                self.label_9.setStyleSheet("color: black")

                self.groupBox_9 = QtWidgets.QGroupBox(self.SubstanceDataTab)
                self.groupBox_9.setGeometry(QtCore.QRect(10, 10, 481, 341))
                self.groupBox_9.setObjectName("groupBox_9")
                self.groupBox_9.setStyleSheet(u"QGroupBox { \n"
                        "     border: 1px solid black; \n"
                        "     border-radius: 5px; \n"
                        "background-color: white;}\n"
                        "QGroupBox::title {\n"
                        "    subcontrol-origin: margin;\n"
                        "    left: 10px;\n"
                        "    padding: -6px 0px 0 0px;\n"
                        "	font-weight: 900;\n"
                        "	color: #84bc34;\n"
                        "	font: 75 10pt \"Segoe UI Semibold\";\n"
                        "}")
                
                lay = QtWidgets.QVBoxLayout(self.groupBox_9)
                lay.setGeometry(QtCore.QRect(20, 30, 441, 291))
                self.GraphCSDInit = CSD_MyStaticMplCanvas(self.groupBox_9)
                lay.addWidget(self.GraphCSDInit)
                self.addToolBar(Qt.TopToolBarArea, NavigationToolbar2QT(self.GraphCSDInit, self))

                self.ResetGraph_2 = QtWidgets.QPushButton(self.groupBox_9)
                self.ResetGraph_2.setObjectName(u"ResetGraph_2")
                self.ResetGraph_2.setGeometry(QtCore.QRect(406, 15, 60, 22))
                self.ResetGraph_2.clicked.connect(self.GraphCSDInit.CSD_compute_initial_figure)           
                
                self.groupBox_6.setObjectName("groupBox_6")

                self.FileNameCSD = QtWidgets.QLineEdit(self.groupBox_6)
                self.FileNameCSD.setGeometry(QtCore.QRect(10, 40, 311, 22))
                self.FileNameCSD.setReadOnly(True)
                self.FileNameCSD.setObjectName("FileNameCSD")

                self.ChooseFileCSD = QtWidgets.QPushButton(self.groupBox_6)
                self.ChooseFileCSD.setStyleSheet("color: black")
                self.ChooseFileCSD.setGeometry(QtCore.QRect(330, 40, 93, 22))
                self.ChooseFileCSD.setObjectName("ChooseFileCSD")
                self.ChooseFileCSD.clicked.connect(self.GraphCSDInit.CSD_browsefiles)
                self.ChooseFileCSD.clicked.connect(self.writeCSDFile)

                self.groupBox_10 = QtWidgets.QGroupBox(self.SubstanceDataTab)
                self.groupBox_10.setGeometry(QtCore.QRect(508, 10, 476, 341))
                self.groupBox_10.setObjectName("groupBox_10")
                self.groupBox_10.setStyleSheet(u"QGroupBox { \n"
                                        "     border: 1px solid black; \n"
                                        "     border-radius: 5px; \n"
                                        "background-color: white;}\n"
                                        "QGroupBox::title {\n"
                                        "    subcontrol-origin: margin;\n"
                                        "    left: 10px;\n"
                                        "    padding: -6px 0px 0 0px;\n"
                                        "	font-weight: 900;\n"
                                        "	color: #84bc34;\n"
                                        "	font: 75 10pt \"Segoe UI Semibold\";\n"
                                        "}")

                self.label_10 = QtWidgets.QLabel(self.groupBox_10)
                self.label_10.setGeometry(QtCore.QRect(10, 40, 141, 22))
                self.label_10.setObjectName("label_10")
                self.label_10.setStyleSheet("color: black")

                self.label_11 = QtWidgets.QLabel(self.groupBox_10)
                self.label_11.setGeometry(QtCore.QRect(10, 67, 141, 22))
                self.label_11.setObjectName("label_11")
                self.label_11.setStyleSheet("color: black")

                self.CrystalComp = QtWidgets.QComboBox(self.groupBox_10)
                self.CrystalComp.setStyleSheet("color: black")
                self.CrystalComp.setGeometry(QtCore.QRect(160, 40, 141, 22))
                self.CrystalComp.setObjectName("CrystalComp")
                CrystalComps = ["Sucrose"]
                self.CrystalComp.addItems(CrystalComps)
                self.CrystalComp.setEditable(True)

                self.MothLiqComp = QtWidgets.QComboBox(self.groupBox_10)
                self.MothLiqComp.setStyleSheet("color: black")
                self.MothLiqComp.setGeometry(QtCore.QRect(160, 67, 141, 22))
                self.MothLiqComp.setObjectName("MothLiqComp")
                self.MothLiqComp.addItem("")

                self.DryGasComp = QtWidgets.QComboBox(self.groupBox_10)
                self.DryGasComp.setStyleSheet("color: black")
                self.DryGasComp.setGeometry(QtCore.QRect(160, 94, 141, 22))
                self.DryGasComp.setObjectName("DryGasComp")
                self.DryGasComp.addItem("")

                self.label_18 = QtWidgets.QLabel(self.groupBox_10)
                self.label_18.setGeometry(QtCore.QRect(10, 94, 141, 22))
                self.label_18.setObjectName("label_18")
                self.label_18.setStyleSheet("color: black")

                self.label_19 = QtWidgets.QLabel(self.groupBox_10)
                self.label_19.setGeometry(QtCore.QRect(10, 121, 141, 22))
                self.label_19.setObjectName("label_19")
                self.label_19.setStyleSheet("color: black")

                self.WashLiqComp = QtWidgets.QComboBox(self.groupBox_10)
                self.WashLiqComp.setStyleSheet("color: black")
                self.WashLiqComp.setGeometry(QtCore.QRect(160, 121, 141, 22))
                self.WashLiqComp.setObjectName("WashLiqComp")
                self.WashLiqComp.addItem("")

                self.GetSolidPhaseData = QPushButton(self.groupBox_10)
                self.GetSolidPhaseData.setObjectName(u"GetSolidPhaseData")
                self.GetSolidPhaseData.setGeometry(QtCore.QRect(179, 300, 150, 26))
                self.GetSolidPhaseData.clicked.connect(self.executeWolframAlphaAPIWindow)

                self.tabWidget.addTab(self.SubstanceDataTab, "")

                self.ParaDetTab = QtWidgets.QWidget()
                self.ParaDetTab.setObjectName("ParaDetTab")

                self.groupBox_11 = QtWidgets.QGroupBox(self.ParaDetTab)
                self.groupBox_11.setGeometry(QtCore.QRect(10, 10, 971, 671))
                self.groupBox_11.setObjectName("groupBox_11")
                self.groupBox_11.setStyleSheet("font-weight: 900; color: #84bc34;\n"
                                                "font: 75 10pt \"Segoe UI Semibold\";\n"
                                                "")
                self.groupBox_11.setStyleSheet(u"QGroupBox { \n"
                                                "     border: 1px solid black; \n"
                                                "     border-radius: 5px; \n"
                                                "background-color: white;}\n"
                                                "QGroupBox::title {\n"
                                                "    subcontrol-origin: margin;\n"
                                                "    left: 10px;\n"
                                                "    padding: -6px 0px 0 0px;\n"
                                                "	font-weight: 900;\n"
                                                "	color: #84bc34;\n"
                                                "	font: 75 10pt \"Segoe UI Semibold\";\n"
                                                "}")
                self.ChooseFileNelMead = QtWidgets.QPushButton(self.groupBox_11)
                self.ChooseFileNelMead.setGeometry(QtCore.QRect(330, 23, 93, 22))
                self.ChooseFileNelMead.setObjectName("ChooseFileNelMead")
                self.ChooseFileNelMead.setStyleSheet("color: black")
                self.ChooseFileNelMead.clicked.connect(self.writeNelMeadFile)

                self.FileNameNelMead = QtWidgets.QLineEdit(self.groupBox_11)
                self.FileNameNelMead.setGeometry(QtCore.QRect(10, 23, 311, 22))
                self.FileNameNelMead.setReadOnly(True)
                self.FileNameNelMead.setObjectName("FileNameNelMead")

                self.frm = QtWidgets.QFrame(self.groupBox_11)
                self.frm.setGeometry(QtCore.QRect(20, 100, 931, 511))
                self.frm.setStyleSheet("background-color: white;\n")
                self.lyt = QtWidgets.QHBoxLayout(self.groupBox_11)
                self.lyt.setGeometry(QtCore.QRect(20, 100, 931, 511))
                self.frm.setLayout(self.lyt)

                self.NelderMeadError = MyFigureCanvas(x_len=200, y_range=[0,200], interval=20)
                self.NelderMeadValue = MyFigureCanvasValue()
                self.lyt.addWidget(self.NelderMeadError, 1)
                self.lyt.addWidget(self.NelderMeadValue, 2)

                self.label_20 = QtWidgets.QLabel(self.groupBox_11)
                self.label_20.setGeometry(QtCore.QRect(185, 60, 135, 22))
                self.label_20.setStyleSheet("font: 10pt \"Segoe UI Semibold\";")
                self.label_20.setObjectName("label_20")
                self.label_20.setStyleSheet("color: black")

                self.IterationSpin = QtWidgets.QSpinBox(self.groupBox_11)
                self.IterationSpin.setGeometry(QtCore.QRect(330, 60, 50, 22))
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold")
                font.setPointSize(10)
                font.setBold(False)
                font.setItalic(False)
                font.setWeight(50)
                self.IterationSpin.setFont(font)
                self.IterationSpin.setStyleSheet("font: 10pt \"Segoe UI Semibold\"; color: black")
                self.IterationSpin.setMinimum(6) #%%%%%%%
                self.IterationSpin.setMaximum(250)
                self.IterationSpin.setObjectName("IterationSpin")

                self.ToggleNM = AnimatedToggle(self.groupBox_11, checked_color="#84bc34")
                self.ToggleNM.setObjectName(u"TogglePSO")
                self.ToggleNM.setGeometry(QtCore.QRect(740, 20, 60, 30))
                self.ToggleNM.setChecked(True)
                self.ToggleNM.stateChanged.connect(self.CheckNelMea)
                self.ToggleNM.toggled.connect(
                        lambda checked: checked and self.TogglePSO.setChecked(False)
                )

                self.label_44 = QtWidgets.QLabel(self.groupBox_11)
                self.label_44.setObjectName(u"label_44")
                self.label_44.setGeometry(QtCore.QRect(540, 24, 180, 22))

                self.TogglePSO = AnimatedToggle(self.groupBox_11, checked_color="#84bc34")
                self.TogglePSO.setObjectName(u"ToggleNM")
                self.TogglePSO.setGeometry(QtCore.QRect(740, 60, 60, 30))
                self.TogglePSO.stateChanged.connect(self.CheckPSO)
                self.TogglePSO.toggled.connect(
                        lambda checked: checked and self.ToggleNM.setChecked(False)
                )

                self.label_45 = QtWidgets.QLabel(self.groupBox_11)
                self.label_45.setObjectName(u"label_45")
                self.label_45.setGeometry(QtCore.QRect(540, 64, 180, 22))

                self.HelpNelMead = QtWidgets.QToolButton(self.groupBox_11)
                self.HelpNelMead.setGeometry(QtCore.QRect(933, 640, 27, 22))
                self.HelpNelMead.setStyleSheet("font-weight: bold; color: black")
                self.HelpNelMead.setObjectName("HelpNelMead")
                self.HelpNelMead.clicked.connect(self.executeNelMeadHelpUIWindow)

                self.StartCrystFit = QtWidgets.QPushButton(self.groupBox_11)
                self.StartCrystFit.setGeometry(QtCore.QRect(437, 630, 120, 31))
                self.StartCrystFit.setStyleSheet("font-weight: bold; color: black")
                self.StartCrystFit.setObjectName("StartCrystFit")

                #%_____Pressing the button starts the Nelder Mead algorithm and displays the live output graph_____%#
                self.StartCrystFit.clicked.connect(self.startFitting)


                self.tabWidget.addTab(self.ParaDetTab, "")
                self.CalcOptionsTab = QtWidgets.QWidget()
                self.CalcOptionsTab.setObjectName("CalcOptionsTab")

                self.groupBox_2 = QtWidgets.QGroupBox(self.CalcOptionsTab)
                self.groupBox_2.setGeometry(QtCore.QRect(10, 10, 476, 241))
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold Semibold")
                font.setPointSize(12)
                font.setBold(True)
                font.setItalic(False)
                font.setWeight(75)
                self.groupBox_2.setFont(font)
                self.groupBox_2.setStyleSheet(u"QGroupBox { \n"
                                                "     border: 1px solid black; \n"
                                                "     border-radius: 5px; \n"
                                                "background-color: white;}\n"
                                                "QGroupBox::title {\n"
                                                "    subcontrol-origin: margin;\n"
                                                "    left: 10px;\n"
                                                "    padding: -6px 0px 0 0px;\n"
                                                "	font-weight: 900;\n"
                                                "	color: #84bc34;\n"
                                                "	font: 75 10pt \"Segoe UI Semibold\";\n"
                                                "}")
                self.groupBox_2.setObjectName("groupBox_2")

                self.HelpCrystal_2 = QtWidgets.QToolButton(self.groupBox_2)
                self.HelpCrystal_2.setGeometry(QtCore.QRect(439, 209, 27, 22))
                self.HelpCrystal_2.setAutoFillBackground(False)
                self.HelpCrystal_2.setStyleSheet("font-weight: bold; color: black")
                self.HelpCrystal_2.setObjectName("HelpCrystal_2")
                self.HelpCrystal_2.clicked.connect(self.executeCalcHelpUIWindow)

                self.DeltaSpin = QtWidgets.QSpinBox(self.groupBox_2)
                self.DeltaSpin.setGeometry(QtCore.QRect(150, 110, 42, 22))
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold")
                font.setPointSize(10)
                font.setBold(False)
                font.setItalic(False)
                font.setWeight(50)
                self.DeltaSpin.setFont(font)
                self.DeltaSpin.setStyleSheet("font: 10pt \"Segoe UI Semibold\"; color: black")
                self.DeltaSpin.setMinimum(5)
                self.DeltaSpin.setMaximum(30)
                self.DeltaSpin.setObjectName("DeltaSpin")

                self.label_6 = QtWidgets.QLabel(self.groupBox_2)
                self.label_6.setGeometry(QtCore.QRect(10, 110, 121, 22))
                self.label_6.setStyleSheet("font: 10pt \"Segoe UI Semibold\"; color: black")
                self.label_6.setObjectName("label_6")

                self.label_7 = QtWidgets.QLabel(self.groupBox_2)
                self.label_7.setGeometry(QtCore.QRect(10, 30, 441, 71))
                self.label_7.setStyleSheet("font: 10pt \"Segoe UI Semibold\"; color: black")
                self.label_7.setWordWrap(True)
                self.label_7.setObjectName("label_7")

                self.StartSimulation = QtWidgets.QPushButton(self.groupBox_2)
                self.StartSimulation.setGeometry(QtCore.QRect(128, 200, 220, 31))
                self.StartSimulation.setStyleSheet("\n"
                                                "font: 10pt \"Segoe UI Semibold\";\n"
                                                "font-weight: bold; color: black")
                self.StartSimulation.setObjectName("StartSimulation")
                self.StartSimulation.clicked.connect(self.CopyData_ToJSON)

                self.StartSimulation.clicked.connect(self.on_simulation_click_cryst)

                self.label_21 = QLabel(self.groupBox_2)
                self.label_21.setObjectName(u"label_21")
                self.label_21.setGeometry(QtCore.QRect(10, 137, 121, 22))
                self.label_21.setStyleSheet(u"font: 10pt \"Segoe UI Semibold\"; color: black")

                self.CycleTimeIn = QLineEdit(self.groupBox_2)
                self.CycleTimeIn.setObjectName(u"CycleTimeIn")
                self.CycleTimeIn.setGeometry(QtCore.QRect(150, 137, 110, 22))
                self.CycleTimeIn.setToolTipDuration(9)
                self.CycleTimeIn.setStyleSheet("font-weight: 900; color: black;\n"
                "font: 75 10pt \"Segoe UI Semibold\";")
                self.CycleTimeIn.textChanged.connect(self.SyncCycleTime1)

                self.tabWidget.addTab(self.CalcOptionsTab, "")

                self.Customization = QtWidgets.QWidget()
                self.Customization.setObjectName("Customization")

                self.TempProfSettings = QtWidgets.QGroupBox(self.Customization)
                self.TempProfSettings.setGeometry(QtCore.QRect(10, 10, 476, 311))
                font = QtGui.QFont()
                font.setFamily("MS Shell Dlg 2")
                font.setPointSize(10)
                font.setBold(True)
                font.setItalic(False)
                font.setWeight(99)
                self.TempProfSettings.setFont(font)
                self.TempProfSettings.setAutoFillBackground(False)
                self.TempProfSettings.setStyleSheet(u"QGroupBox { \n"
                                                "     border: 1px solid black; \n"
                                                "     border-radius: 5px; \n"
                                                "background-color: white;}\n"
                                                "QGroupBox::title {\n"
                                                "    subcontrol-origin: margin;\n"
                                                "    left: 10px;\n"
                                                "    padding: -6px 0px 0 0px;\n"
                                                "	font-weight: 900;\n"
                                                "	color: #84bc34;\n"
                                                "	font: 75 10pt \"Segoe UI Semibold\";\n"
                                                "}")
                self.TempProfSettings.setObjectName("TempProfSettings")

                self.PreHeatTime = QtWidgets.QLineEdit(self.TempProfSettings)
                self.PreHeatTime.setGeometry(QtCore.QRect(160, 40, 110, 22))
                self.PreHeatTime.setToolTipDuration(9)
                self.PreHeatTime.setStyleSheet("color: black")
                self.PreHeatTime.setText("")
                self.PreHeatTime.setObjectName("PreHeatTime")

                self.label_38 = QtWidgets.QLabel(self.TempProfSettings)
                self.label_38.setGeometry(QtCore.QRect(10, 40, 141, 22))
                font = QtGui.QFont()
                font.setFamily("\"Segoe UI Semibold\"")
                font.setPointSize(10)
                font.setBold(False)
                font.setItalic(False)
                font.setWeight(9)
                self.label_38.setFont(font)
                self.label_38.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_38.setStyleSheet("color: black;\n"
                                        "font: 75 10pt \\\"Segoe UI Semibold\\\";")
                self.label_38.setObjectName("label_38")

                self.label_39 = QtWidgets.QLabel(self.TempProfSettings)
                self.label_39.setGeometry(QtCore.QRect(10, 67, 141, 22))
                self.label_39.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_39.setStyleSheet("color: black;\n"
                                        "font: 75 10pt \\\"Segoe UI Semibold\\\";")
                self.label_39.setObjectName("label_39")

                self.RipeTime = QtWidgets.QLineEdit(self.TempProfSettings)
                self.RipeTime.setGeometry(QtCore.QRect(160, 67, 110, 22))
                self.RipeTime.setStyleSheet("color: black")
                self.RipeTime.setText("")
                self.RipeTime.setObjectName("RipeTime")

                self.CrModulNr_3 = QtWidgets.QLineEdit(self.TempProfSettings)
                self.CrModulNr_3.setGeometry(QtCore.QRect(160, 94, 110, 22))
                self.CrModulNr_3.setStyleSheet("color: black")
                self.CrModulNr_3.setText("")
                self.CrModulNr_3.setObjectName("CrModulNr_3")
                self.CrModulNr_3.textChanged.connect(self.SyncModulNr2)

                self.label_40 = QtWidgets.QLabel(self.TempProfSettings)
                self.label_40.setGeometry(QtCore.QRect(10, 94, 141, 22))
                self.label_40.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_40.setStyleSheet("color: black;\n"
                                        "font: 75 10pt \\\"Segoe UI Semibold\\\";")
                self.label_40.setObjectName("label_40")

                self.TempProf_3 = QtWidgets.QComboBox(self.TempProfSettings)
                self.TempProf_3.setGeometry(QtCore.QRect(160, 121, 110, 22))
                self.TempProf_3.setStyleSheet("color:black;")
                self.TempProf_3.setObjectName("TempProf_3")
                self.TempProf_3.addItem("")
                self.TempProf_3.addItem("")
                self.TempProf_3.addItem("")
                self.TempProf_3.currentTextChanged.connect(self.SyncProf2)

                self.label_41 = QtWidgets.QLabel(self.TempProfSettings)
                self.label_41.setGeometry(QtCore.QRect(10, 121, 141, 22))
                self.label_41.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_41.setStyleSheet("color: black;\n"
                                        "font: 75 10pt \\\"Segoe UI Semibold\\\";")
                self.label_41.setObjectName("label_41")

                self.label_42 = QtWidgets.QLabel(self.TempProfSettings)
                self.label_42.setGeometry(QtCore.QRect(10, 148, 141, 22))
                self.label_42.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.label_42.setStyleSheet("color: black;\n"
                                        "font: 75 10pt \\\"Segoe UI Semibold\\\";")
                self.label_42.setObjectName("label_42")

                self.CycleTimeIn2 = QtWidgets.QLineEdit(self.TempProfSettings)
                self.CycleTimeIn2.setGeometry(QtCore.QRect(160, 148, 110, 22))
                self.CycleTimeIn2.setStyleSheet("color: black")
                self.CycleTimeIn2.setText("")
                self.CycleTimeIn2.setPlaceholderText("")
                self.CycleTimeIn2.setObjectName("CycleTimeIn2")
                self.CycleTimeIn2.textChanged.connect(self.SyncCycleTime2)

                self.UpdateGraph = QtWidgets.QPushButton(self.TempProfSettings)
                self.UpdateGraph.setGeometry(QtCore.QRect(178, 270, 120, 31))
                self.UpdateGraph.setStyleSheet("font-weight: bold")
                self.UpdateGraph.setObjectName("UpdateGraph")

                self.ResetGraph = QtWidgets.QPushButton(self.TempProfSettings)
                self.ResetGraph.setObjectName("ResetGraph")
                self.ResetGraph.setGeometry(QtCore.QRect(406, 279, 60, 22))

                self.TempProfPlot = QtWidgets.QGroupBox(self.Customization)
                self.TempProfPlot.setGeometry(QtCore.QRect(510, 10, 476, 311))
                self.TempProfPlot.setLayoutDirection(QtCore.Qt.RightToLeft)
                self.TempProfPlot.setStyleSheet("font-weight: 900; color: limegreen;\n"
                                        "font: 75 10pt \"MS Shell Dlg 2\";")
                self.TempProfPlot.setTitle("")
                self.TempProfPlot.setObjectName("TempProfPlot")

                self.TempProfPlot.setStyleSheet(u"QGroupBox { \n"
                                        "     border: 1px solid black; \n"
                                        "     border-radius: 5px; \n"
                                        "background-color: white;}\n"
                                        "QGroupBox::title {\n"
                                        "    subcontrol-origin: margin;\n"
                                        "    left: 10px;\n"
                                        "    padding: -6px 0px 0 0px;\n"
                                        "	font-weight: 900;\n"
                                        "	color: #84bc34;\n"
                                        "	font: 75 10pt \"Segoe UI Semibold\";\n"
                                        "}")

                self.layTempProfPlot = QtWidgets.QWidget(self.TempProfPlot)
                self.layTempProfPlot.setGeometry(QtCore.QRect(10, 10, 456, 291))
                self.layTempProfPlot.setObjectName("layTempProfPlot")
                self.tabWidget.addTab(self.Customization, "")

                Ui_mainWindowInstance = Ui_mainWindow()
                layTempProf = QtWidgets.QVBoxLayout(self.TempProfPlot)
                layTempProf.setGeometry(QtCore.QRect(10, 5, 456, 291))
                self.TempProfPlot = TempProfile(self.TempProfPlot)
                layTempProf.addWidget(self.TempProfPlot)

                self.UpdateGraph.clicked.connect(self.GetParams)
                self.UpdateGraph.clicked.connect(self.TempProfPlot.updateGraph)
                self.ResetGraph.clicked.connect(self.TempProfPlot.compute_initialFigure)
                self.ResetGraph.clicked.connect(self.ResetParams)
                mainWindow.setCentralWidget(self.centralwidget)

                self.retranslateUi(mainWindow)
                self.tabWidget.setCurrentIndex(0)
                QtCore.QMetaObject.connectSlotsByName(mainWindow)

        def retranslateUi(self, mainWindow):    
                _translate = QtCore.QCoreApplication.translate
                mainWindow.setWindowTitle(_translate("mainWindow", "Belt Crystallizer Simulation"))
                self.tabWidget.setToolTip(_translate("mainWindow", "Test"))
                self.groupBox.setTitle(_translate("mainWindow", "Crystallization"))
                self.HelpCrystal.setText(_translate("mainWindow", "?"))
                self.CheckCrystal.setToolTip(_translate("mainWindow", "If this box is checked, the unit operation is simulated."))
                self.CheckCrystal.setText(_translate("mainWindow", "Simulate Unit Operation?"))
                self.StartTempIn.setToolTip(_translate("mainWindow", "Test"))
                self.StartTempIn.setText(_translate("mainWindow", u"59", None))
                self.EndTempIn.setText(_translate("mainWindow", u"20", None))
                self.CrModulNr.setText(_translate("mainWindow", u"4", None))
                self.CrModulNr_3.setText(_translate("mainWindow", u"4", None))
                self.label_2.setText(_translate("mainWindow", "Starting Temperature:"))
                self.label_3.setText(_translate("mainWindow", "End Temperature:"))
                self.label_4.setText(_translate("mainWindow", "Number of Modules:"))
                self.CycleTimeIn.setText(_translate("mainWindow", u"1800", None))
                self.CycleTimeIn2.setText(_translate("mainWindow", u"1800", None))
                self.TempProf.setItemText(0, _translate("mainWindow", "Linear"))
                self.TempProf.setItemText(1, _translate("mainWindow", "Progressive"))
                self.TempProf.setItemText(2, _translate("mainWindow", "Alternating"))
                self.label_5.setText(_translate("mainWindow", "Temperature Profile:"))
                self.label_8.setText(_translate("mainWindow", "Shape factor:"))
                self.AreaFactor.setToolTip(_translate("mainWindow", "<html><head/><body><p>Shape factor used in the determination of crystal mass. Default value is Pi()/6.</p></body></html>"))
                self.AreaFactor.setText(_translate("mainWindow", "0.523598776"))
                self.label_22.setText(_translate("mainWindow", u"Seed Mass:", None))
                self.label_43.setText(_translate("mainWindow", "Growth Kinetic:", None))
                self.GrowthKin.setItemText(0, _translate("mainWindow", "Exponential", None))
                self.GrowthKin.setItemText(1, _translate("mainWindow", "BCF", None))
                self.groupBox_3.setTitle(_translate("mainWindow", "Filtration"))
                self.groupBox_4.setTitle(_translate("mainWindow", "GroupBox"))
                self.HelpFiltration.setText(_translate("mainWindow", "?"))
                self.CheckFiltration.setToolTip(_translate("mainWindow", "If this box is checked, the unit operation is simulated."))
                self.CheckFiltration.setText(_translate("mainWindow", "Simulate Unit Operation?"))
                self.FiltrationPressure.setToolTip(_translate("mainWindow", "Test"))
                self.label_12.setText(_translate("mainWindow", "Filtration Pressure:"))
                self.label_13.setText(_translate("mainWindow", "Filtration Time:"))
                self.FiltrationTime.setToolTip(_translate("mainWindow", "Testingggg"))
                self.label_26.setText(_translate("mainWindow", u"Temperature:", None))
                self.groupBox_5.setTitle(_translate("mainWindow", "Cake Washing"))
                self.HelpWashing.setText(_translate("mainWindow", "?"))
                self.CheckWashing.setToolTip(_translate("mainWindow", "If this box is checked, the unit operation is simulated."))
                self.CheckWashing.setText(_translate("mainWindow", "Simulate Unit Operation?"))
                self.label_14.setText(_translate("mainWindow", "Washing Time:"))
                self.WashTime.setToolTip(_translate("mainWindow", "Test"))
                self.label_15.setText(_translate("mainWindow", "Washing flow rate:"))
                self.WashFlowRate.setToolTip(_translate("mainWindow", "Test"))
                self.label_25.setText(_translate("mainWindow", u"Washing Pressure:", None))
                self.groupBox_7.setTitle(_translate("mainWindow", "Drying"))
                self.groupBox_8.setTitle(_translate("mainWindow", "GroupBox"))
                self.HelpDrying.setText(_translate("mainWindow", "?"))
                self.CheckDrying.setToolTip(_translate("mainWindow", "If this box is checked, the unit operation is simulated."))
                self.CheckDrying.setText(_translate("mainWindow", "Simulate Unit Operation?"))
                self.DryingTemp.setToolTip(_translate("mainWindow", "Test"))
                self.label_16.setText(_translate("mainWindow", "Drying Temperature:"))
                self.DryGasPres.setToolTip(_translate("mainWindow", "Test"))
                self.label_17.setText(_translate("mainWindow", "Drying gas pressure:"))
                self.CopyData.setToolTip(_translate("mainWindow", "<html><head/><body><p><span style=\" font-size:8pt;\">Copies the input data to the .JSON file used in the simulation.</span></p></body></html>"))
                self.CopyData.setText(_translate("mainWindow", "Copy Data"))
                self.label_23.setText(_translate("mainWindow", u"Slope:", None))
                self.label_24.setText(_translate("mainWindow", u"y-Intercept:", None))
                self.ConfidenceToggle.setToolTip(_translate("mainWindow", u"<html><head/><body><p>If the box is toggle is switched on, reliable data for slope and y-intercept is available.</p><p>If not, then the fields serve as inputs for known x- and y-coordinates.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
                self.ConfidenceToggle.setText(_translate("mainWindow", u"CheckBox", None))
                self.Confidence.setText(_translate("mainWindow", u"Data available?", None))
                self.tabWidget.setTabText(self.tabWidget.indexOf(self.InputTab), _translate("mainWindow", "Simulation Input"))
                self.groupBox_6.setTitle(_translate("mainWindow", "Choose a custom distribution"))
                self.ChooseFileCSD.setText(_translate("mainWindow", "Choose File"))
                self.label_9.setText(_translate("mainWindow", "<html><head/><body><p><span style=\" font-size:10pt;\">Pressing the button opens a dialog to select an Excel file with a custom crystal size distribution. Data is extracted using the Pandas package and should appear in the above plot afterwards.</span></p><p><span style=\" font-size:10pt;\">Labels for the data should be </span><span style=\" font-size:10pt; font-weight:600;\">Diameter, Number </span><span style=\" font-size:10pt;\">and </span><span style=\" font-size:10pt; font-weight:600;\">ClassWidth</span><span style=\" font-size:10pt;\">. The size distribution data is automatically sent to the input .json file.</span></p></body></html>"))
                self.groupBox_9.setTitle(_translate("mainWindow", "Currently used distribution"))
                self.ResetGraph_2.setText(_translate("mainWindow", "Reset", None))
                self.groupBox_10.setTitle(_translate("mainWindow", "Edit components"))
                self.label_10.setText(_translate("mainWindow", "Crystal:"))
                self.label_11.setText(_translate("mainWindow", "Mother liquor:"))
                self.CrystalComp.setItemText(0, _translate("mainWindow", "Sucrose"))
                self.MothLiqComp.setItemText(0, _translate("mainWindow", "Water"))
                self.DryGasComp.setItemText(0, _translate("mainWindow", "Air"))
                self.label_18.setText(_translate("mainWindow", "Drying Gas:"))
                self.label_19.setText(_translate("mainWindow", "Washing Liquid:"))
                self.WashLiqComp.setItemText(0, _translate("mainWindow", "Ethanol"))
                self.GetSolidPhaseData.setText(_translate("mainWindow", u"Retrieve Crystal Data", None))
                self.tabWidget.setTabText(self.tabWidget.indexOf(self.SubstanceDataTab), _translate("mainWindow", "Substance Data"))
                self.groupBox_11.setTitle(_translate("mainWindow", "Crystallization"))
                self.ChooseFileNelMead.setText(_translate("mainWindow", "Choose File"))
                self.label_20.setText(_translate("mainWindow", "Number of Iterations:"))
                self.HelpNelMead.setText(_translate("mainWindow", "?"))
                self.StartCrystFit.setToolTip(_translate("mainWindow", "<html><head/><body><p><span style=\" font-size:8pt;\">Copies the input data to the .JSON file used in the simulation.</span></p></body></html>"))
                self.StartCrystFit.setText(_translate("mainWindow", "Start Fitting"))
                self.label_44.setText(_translate("mainWindow", "Nelder-Mead Algorithm:", None))
                self.label_45.setText(_translate("mainWindow", "Particle Swarm Optimization:", None))
                self.tabWidget.setTabText(self.tabWidget.indexOf(self.ParaDetTab), _translate("mainWindow", "Parameter Determination"))
                self.groupBox_2.setTitle(_translate("mainWindow", "Calculation Settings"))
                self.HelpCrystal_2.setText(_translate("mainWindow", "?"))
                self.label_6.setText(_translate("mainWindow", "Solver Resolution:"))
                self.label_7.setText(_translate("mainWindow", "Changes the resolution of the solver. The number equates to the duration between steps for the ODE solver. A higher number equates to a coarser calculation but faster results. A lower number equates to a better resolution of the results but slower calculations."))
                self.StartSimulation.setToolTip(_translate("mainWindow", "<html><head/><body><p><span style=\" font-size:8pt;\">Copy data to .json and start the simulation.</span></p></body></html>"))
                self.StartSimulation.setText(_translate("mainWindow", "Copy Data and Start Simulation"))
                self.label_21.setText(_translate("mainWindow", u"Cycle Time:", None))
                self.tabWidget.setTabText(self.tabWidget.indexOf(self.CalcOptionsTab), _translate("mainWindow", "Calculation Options"))
                self.TempProfSettings.setTitle(_translate("mainWindow", "Customize Temperature Profile"))
                self.PreHeatTime.setToolTip(_translate("mainWindow", "Test"))
                self.PreHeatTime.setText(_translate("mainWindow", u"600", None))
                self.RipeTime.setText(_translate("mainWindow", u"600", None))
                self.label_38.setText(_translate("mainWindow", "Preheating Time:"))
                self.label_39.setText(_translate("mainWindow", "Ripening Time:"))
                self.label_40.setText(_translate("mainWindow", "Number of modules:"))
                self.TempProf_3.setItemText(0, _translate("mainWindow", "Linear"))
                self.TempProf_3.setItemText(1, _translate("mainWindow", "Progressive"))
                self.TempProf_3.setItemText(2, _translate("mainWindow", "Alternating"))
                self.label_41.setText(_translate("mainWindow", "Temperature Profile:"))
                self.label_42.setText(_translate("mainWindow", "Cycle time:"))
                self.CycleTimeIn2.setToolTip(_translate("mainWindow", "<html><head/><body><p>Area factor used in the determination of crystal mass. If the field is left empty, it is set to Pi/6 as default.</p></body></html>"))
                self.UpdateGraph.setToolTip(_translate("mainWindow", "<html><head/><body><p><span style=\" font-size:8pt;\">Copies the input data to the .JSON file used in the simulation.</span></p></body></html>"))
                self.UpdateGraph.setText(_translate("mainWindow", "Update Graph"))
                self.ResetGraph.setText(_translate("mainWindow", "Reset"))
                self.tabWidget.setTabText(self.tabWidget.indexOf(self.Customization), _translate("mainWindow", "Customization"))
        #from mpl_csd_plot import MPL_CSD_Plot
        def executeCrystHelpUIWindow(self):
                Dialog = HelpCryst_Dialog()
                Dialog.exec()
        def executeWashHelpUIWindow(self):
                Dialog = HelpWash_Dialog()
                Dialog.exec()
        def executeDryHelpUIWindow(self):
                Dialog = HelpDryDialog()
                Dialog.exec()
        def executeFiltHelpUIWindow(self):
                Dialog = HelpFiltDialog()
                Dialog.exec()
        def executeNelMeadHelpUIWindow(self):
                Dialog = HelpNelMeadDialog()
                Dialog.exec()
        def executeCalcFinishedUIWindow(self):
                Dialog = CalcFinishedDialog()
                Dialog.exec()
        #def executeAboutUIWindow(self):
        #        Dialog = AboutDialog()
        #        Dialog.exec()
        def executeCalcHelpUIWindow(self):
                Dialog = StartCalcHelp()
                Dialog.exec()

        def executeWolframAlphaAPIWindow(self):
                global Crystal, TDry, DryingGas
                Crystal = self.CrystalComp.currentText()
                DryingGas = self.DryGasComp.currentText()
                TDry = int(self.DryingTemp.text())
                print(self.CrystalComp.currentText())
                print(TDry)
                Dialog = WolframAlphaWindow()
                Dialog.exec()

        #####################################################
        def CopyData_ToJSON(self):
                JSON_file = open(os.path.dirname(__file__) + "\\DWSIM\\Input.json")
                parsed_data = json.load(JSON_file)

                ##Copy Data from Gui to the JSON input file for DWSIM:
                        #_____Copy Data for crystallization_____#
                if SimulatedUnitOps[0] == 1:
                        if self.StartTempIn.text() != "":
                                parsed_data["T_Start"] = float(self.StartTempIn.text())
                        if self.EndTempIn.text() != "":
                                parsed_data["T_End"] = float(self.EndTempIn.text())
                        if self.CrModulNr.text() != "":
                                parsed_data["CrystallizationModules"] = int(self.CrModulNr.text())
                        if self.SeedMass.text() != "":
                                parsed_data["SeedMass"] = float(self.SeedMass.text())
                        if self.AreaFactor.text() != "0.523598776":
                                parsed_data["ShapeFactor"] = float(self.AreaFactor.text())
                        parsed_data["Profile"] = self.TempProf.currentText()
                        parsed_data["Crystal"] = self.CrystalComp.currentText()
                        parsed_data["MotherLiquor"] = self.MothLiqComp.currentText()
                        parsed_data["GrowthRate"] = self.GrowthKin.currentText()
                        parsed_data["RipeningTime"] = int(self.RipeTime.text())
                        parsed_data["PreheatingTime"] = int(self.PreHeatTime.text())

                        #_____Copy data for filtration_____#
                if SimulatedUnitOps[1] == 1:
                        parsed_data["Confidence"] = Confidence
                        if self.FiltrationPressure.text() != "":
                                parsed_data["DeltaP_Filt"] = float(self.FiltrationPressure.text())
                        if self.FiltrationTime.text() != "":
                                parsed_data["FiltrationTime"] = int(self.FiltrationTime.text())
                        if self.FiltSlope.text() != "" and Confidence == "Data":
                                parsed_data["Slope"] = float(self.FiltSlope.text())
                        elif self.FiltSlope.text() != "" and Confidence == "Est":
                                parsed_data["KnownX"] = float(self.FiltSlope.text())
                        if self.FiltYintercept.text() != "" and Confidence == "Data":
                                parsed_data["yIntercept"] = float(self.FiltYintercept.text())
                        elif self.FiltSlope.text() != "" and Confidence == "Est":
                                parsed_data["KnownY"] = float(self.FiltYintercept.text())
                        if self.FiltTemperature.text() != "":
                                parsed_data["T_Filt"] = float(self.FiltTemperature.text())
                        
                        #_____Copy data for washing_____#
                if SimulatedUnitOps[2] == 1:
                        if self.WashFlowRate.text() != "":
                                parsed_data["FlowRate_Wash"] = float(self.WashFlowRate.text())
                        if self.WashPressure.text() != "":
                                parsed_data["DeltaP_Wash"] = float(self.WashPressure.text())
                        if self.FiltTemperature.text() != "":
                                parsed_data["T_Filt"] = float(self.FiltTemperature.text())
                        if self.WashTime.text() != "":
                                parsed_data["WashingTime"] = int(self.WashTime.text())
                        parsed_data["WashFluid"] = self.WashLiqComp.currentText()

                        #_____Copy data for drying_____#
                if SimulatedUnitOps[3] == 1:
                        if self.DryingTemp.text() != "":
                                parsed_data["T_Dry"] = float(self.DryingTemp.text())
                        if self.DryGasPres.text() != "":
                                parsed_data["DeltaP_Dry"] = float(self.DryGasPres.text())
                        parsed_data["DryingGas"] = self.DryGasComp.currentText()
                
                        #_____Copy general data_____#
                parsed_data["Delta"] = self.DeltaSpin.value()
                if self.CycleTimeIn.text() != "":
                        parsed_data["CycleTime"] = int(self.CycleTimeIn.text())
                
                print(SimulatedUnitOps)
                with open(os.path.dirname(__file__) + "\\DWSIM\\Input.json", "w") as json_file:
                        json.dump(parsed_data, json_file, indent=4)
        #####################################################
        #Functions for synchronization of line edits
        def SyncModulNr1(self, text):
                self.CrModulNr_3.setText(self.CrModulNr.text())
        def SyncModulNr2(self, text):
                self.CrModulNr.setText(self.CrModulNr_3.text())
        def SyncProf1(self, text):
                self.TempProf_3.setCurrentText(self.TempProf.currentText())
        def SyncProf2(self, text):
                self.TempProf.setCurrentText(self.TempProf_3.currentText())
        def SyncCycleTime1(self, text):
                self.CycleTimeIn2.setText(self.CycleTimeIn.text())
        def SyncCycleTime2(self, text):
                self.CycleTimeIn.setText(self.CycleTimeIn2.text())
        #####################################################
        def GetParams(self):
                global T_Start, T_End, CrystModules, CycleTime, Profile, HoldingTime, RipeningTime
                T_Start = int(self.StartTempIn.text())
                T_End = int(self.EndTempIn.text())
                CrystModules = int(self.CrModulNr.text())
                CycleTime = int(self.CycleTimeIn.text())
                Profile = self.TempProf.currentText()
                HoldingTime = int(self.PreHeatTime.text())
                RipeningTime = int(self.RipeTime.text())

        def ResetParams(self):
                self.StartTempIn.setText("59")
                self.EndTempIn.setText("20")
                self.CrModulNr.setText("4")
                self.CycleTimeIn.setText("1800")
                self.PreHeatTime.setText("600")
                self.RipeTime.setText("600")
        #####################################################
        def CheckCryst(self, state):
                global SimulatedUnitOps
                if state == 2:
                        SimulatedUnitOps[0] = 1
                else:
                        SimulatedUnitOps[0] = 0
                print(SimulatedUnitOps)
        def CheckFilt(self, state):
                global SimulatedUnitOps
                if state == 2:
                        SimulatedUnitOps[1] = 1
                else:
                        SimulatedUnitOps[1] = 0
                print(SimulatedUnitOps)
        def CheckWash(self, state):
                global SimulatedUnitOps
                if state == 2:
                        SimulatedUnitOps[2] = 1
                else:
                        SimulatedUnitOps[2] = 0
                print(SimulatedUnitOps)
        def CheckDry(self, state):
                global SimulatedUnitOps
                if state == 2:
                        SimulatedUnitOps[3] = 1
                else:
                        SimulatedUnitOps[3] = 0
                print(SimulatedUnitOps)
        def writeCSDFile(self):
                self.FileNameCSD.setText(FilePathCSD)

        def writeNelMeadFile(self):
                fnameNM = QFileDialog.getOpenFileName(self, "Choose new initial CSD", os.path.dirname(__file__), "Excel files (*.xlsx)")
                global FilePathNelMead
                FilePathNelMead = fnameNM[0]
                self.FileNameNelMead.setText(FilePathNelMead)
                print(FilePathNelMead)

        def CheckNelMea(self, state):
                global NelderMead
                if state == 2:
                        NelderMead = "True"
                else:
                        NelderMead = "False"
                print(NelderMead)
        def CheckPSO(self, state):
                global PSO
                if state == 2:
                        PSO = "True"
                else:
                        PSO = "False"
                print(PSO)
        def FiltrConfi(self, state):
                global Confidence
                if state == 2:
                        Confidence = "Data"
                else:
                        Confidence = "Est"
                print(Confidence)
        
#############################################################
        def startFitting(self):
                print("Starting fitting algorithm")
                global Iterations
                Iterations = self.IterationSpin.value()
                if NelderMead == "True":
                        command = ['python',
                                   os.path.join(os.path.dirname(__file__), "DWSIM", 'CrystFitting.py'),
                                   "%s" % FilePathNelMead,
                                   "%f" % self.IterationSpin.value(),
                                   "%s" %NelderMead,
                                   "%s" %PSO]
                else:
                        command = ['python',
                                   os.path.join(os.path.dirname(__file__), "DWSIM", 'FittingCombined_2ObjFunc.py'),
                                   "%s" % FilePathNelMead,
                                   "%f" % self.IterationSpin.value(),
                                   "%s" %NelderMead,
                                   "%s" %PSO] 

                self.subprocess_thread = SubprocessThread(command)
                self.subprocess_thread.output_received.connect(self.handle_output)
                self.subprocess_thread.start()

        def handle_output(self, output):
                read_Output(output)
                self.NelderMeadError._update_canvas_()
                self.NelderMeadValue._update_canvas_NM_()
                if int(output[0]) == 1:
                        Dialog = CalcFinishedDialog()
                        Dialog.exec()
                        global ExitCode
                        ExitCode = int(output[0])
                pass

        def on_simulation_click_cryst(self):

                if SimulatedUnitOps[0] == 1:

                        command = ["python", os.path.join(os.path.dirname(__file__), "DWSIM", "RunCrystallization.py"),
                                os.path.dirname(__file__) +  "\\DWSIM\\DWSIM_Files\\", "Simulation"]
                        process = subprocess.Popen(command)
                        process.wait()

                if SimulatedUnitOps[1] == 1 and SimulatedUnitOps[2] == 0:

                        command = ["python", os.path.join(os.path.dirname(__file__),  "DWSIM", "RunFiltration.py"),
                                   os.path.dirname(__file__) + "\\DWSIM\\DWSIM_Files\\", "Simulation"]
                        process = subprocess.Popen(command)
                        process.wait()

                if SimulatedUnitOps[1] == 1 and SimulatedUnitOps[2] == 1:
                        command = ["python", os.path.join(os.path.dirname(__file__), "DWSIM", "RunFiltrationWashing.py"),
                                   os.path.dirname(__file__) + "\\DWSIM\\DWSIM_Files\\"]
                        process = subprocess.Popen(command)
                        process.wait()

                if SimulatedUnitOps[3] == 1:
                        command = ["python", os.path.join(os.path.dirname(__file__), "DWSIM", "RunDrying.py"),
                                   os.path.dirname(__file__) + "\\DWSIM\\DWSIM_Files\\"]
                        process = subprocess.Popen(command)
                        process.wait()

                subprocess.Popen(["python",
                                  os.path.join(os.path.dirname(__file__), "ResultWindow.py"),
                                  str(SimulatedUnitOps[0]),
                                  str(SimulatedUnitOps[1]),
                                  str(SimulatedUnitOps[2]),
                                  str(SimulatedUnitOps[3])])

        def Simu_OutputCryst(self, output):
                print(output)
                if int(output[0]) == 1:
                        global ExitCodeCryst
                        ExitCodeCryst = int(output[0])
                        print([ExitCodeCryst, ExitCodeFilt, ExitCodeFiltWash, ExitCodeDry])
                        print(sum([ExitCodeCryst, ExitCodeFilt, ExitCodeFiltWash, ExitCodeDry]))
                pass
        def Simu_OutputFilt(self, output):
                global ExitCodeFilt
                ExitCodeFilt = int(output[0])
                print([ExitCodeCryst, ExitCodeFilt, ExitCodeFiltWash, ExitCodeDry])
                print(sum([ExitCodeCryst, ExitCodeFilt, ExitCodeFiltWash, ExitCodeDry]))
                pass
        def Simu_OutputFiltWash(self, output):
                global ExitCodeFiltWash
                ExitCodeFiltWash = int(output[0])
                print([ExitCodeCryst, ExitCodeFilt, ExitCodeFiltWash, ExitCodeDry])
                print(sum([ExitCodeCryst, ExitCodeFilt, ExitCodeFiltWash, ExitCodeDry]))
                pass
        def Simu_OutputDry(self, output):
                global ExitCodeDry
                ExitCodeDry = int(output[0])
                print([ExitCodeCryst, ExitCodeFilt, ExitCodeFiltWash, ExitCodeDry])
                print(sum([ExitCodeCryst, ExitCodeFilt, ExitCodeFiltWash, ExitCodeDry]))
                pass

#############################################################
class My_2D_StaticCanvas(FigureCanvasQTAgg):
        def __init__(self, parent=None):
                fig = Figure()
                FigureCanvasQTAgg.__init__(self, fig)
                self.axes = fig.add_subplot()
                fig.tight_layout(rect=[.1,.1,.9,.9])

                FigureCanvasQTAgg.__init__(self, fig)
                FigureCanvasQTAgg.setSizePolicy(self,
                                                QSizePolicy.Expanding,
                                                QSizePolicy.Expanding)
                FigureCanvasQTAgg.updateGeometry(self)
                self.compute_initialFigure()
        def compute_initialFigure(self):
                pass
class TempProfile(My_2D_StaticCanvas):
        def compute_initialFigure(self):
                self.axes.clear()
                T_Start_init = 59
                T_End_init = 20
                t_Process_init = 1800 * 4
                t_values = np.linspace(0, t_Process_init, 1000)
                HoldingTime_init = 600
                RipeningTime_init = 600

                JSON_file = open(os.path.dirname(__file__) + "\\DWSIM\\Input.json")
                parsed_data = json.load(JSON_file)
                parsed_data["A"] = 12.871
                parsed_data["B"] = 9.4248
                parsed_data["C"] = 13.2579
                parsed_data["D"] = 46.129
                with open(os.path.dirname(__file__) + "\\DWSIM\\Input.json", "w") as json_file:
                        json.dump(parsed_data, json_file, indent=4)

                def temperature_function(t):
                        if t < HoldingTime_init:
                                return T_Start_init
                        elif HoldingTime_init <= t < t_Process_init - RipeningTime_init:
                                return T_Start_init - (T_Start_init - T_End_init) * ((t - HoldingTime_init)*(t_Process_init - (HoldingTime_init + RipeningTime_init))**(-1))**1
                        else:
                                return T_End_init
                temperatures = [temperature_function(t) for t in t_values]
                self.axes.plot(t_values, temperatures, color=color1)
                self.axes.set_xlabel("Time [s]")
                self.axes.set_ylabel("Temperature [°C]")
                for i in range(1, 4):
                        line_position = 1800 * i
                        if i == 1:
                                self.axes.axvline(x=line_position, color=color2, label="Module change")
                        else:
                                self.axes.axvline(x=line_position, color=color2)
                self.axes.fill_between([0, HoldingTime_init], 0, T_Start_init, alpha=0.5, color="#FFCDCB", label="Holding Time")
                self.axes.fill_between([t_Process_init-RipeningTime_init, t_Process_init], 0, T_Start_init, alpha=0.5, color="#AEE2FF", label="Ripening Time")
                self.axes.legend(prop={"size": 6})
                self.draw()
                return super().compute_initialFigure()
        def updateGraph(self):
                self.axes.clear()
                t_Process = CrystModules * CycleTime
                def Temp1(t):
                        return T_Start
                def Temp2(t):
                        return T_End
                def Linear(t):
                        return T_Start - (T_Start - T_End) * (t - HoldingTime)*(t_Process - (HoldingTime + RipeningTime))**(-1)
                def Progressive(t):
                        return T_Start - (T_Start - T_End) * ((t - HoldingTime)*(t_Process - (HoldingTime + RipeningTime))**(-1))**3
                def Alternating(t, A, B, C, D):
                        return A * np.cos(B * (t - HoldingTime)/(t_Process - (HoldingTime+RipeningTime))) - C * (t - HoldingTime)/(t_Process - (HoldingTime+RipeningTime)) + D
                t_values = np.linspace(0, t_Process, 2000)

                temperatures1 = [Temp1(t) for t in t_values[t_values < HoldingTime]]
                temperatures3 = [Temp2(t) for t in t_values[t_values >= t_Process - RipeningTime]]

                if Profile == "Linear":
                        temperatures2 = [Linear(t) for t in t_values[np.where(np.logical_and(t_values >= HoldingTime, t_values < t_Process - RipeningTime))]]
                elif Profile == "Progressive":
                        temperatures2 = [Progressive(t) for t in t_values[np.where(np.logical_and(t_values >= HoldingTime, t_values < t_Process - RipeningTime))]]
                else:
                        init_guess = [12.871, 9.4248, 13.2579, 46.129]
                        xdata = [HoldingTime, t_Process - RipeningTime, 0.25*t_Process, 0.5*t_Process]
                        ydata = [T_Start, T_End, (T_Start + T_End)/2, (T_Start + T_End)/2]
                        popt, pcov = curve_fit(Alternating, xdata, ydata, init_guess)
                        print(popt)
                        temperatures2 = [Alternating(t, *popt) for t in t_values[np.where(np.logical_and(t_values >= HoldingTime, t_values < t_Process - RipeningTime))]]
                self.axes.plot(t_values[t_values < HoldingTime], temperatures1, color=color1)
                self.axes.plot(t_values[np.where(np.logical_and(t_values >= HoldingTime, t_values < t_Process - RipeningTime))], temperatures2, color=color1)
                self.axes.plot(t_values[t_values >= t_Process - RipeningTime], temperatures3, color=color1)
                self.axes.set_xlabel("Time [s]")
                self.axes.set_ylabel("Temperature [°C]")
                for i in range(1, CrystModules):
                        line_position = CycleTime * i
                        if i == 1:
                                self.axes.axvline(x=line_position, color=color2, label="Module change")
                        else:
                                self.axes.axvline(x=line_position, color=color2)
                self.axes.fill_between([0, HoldingTime], 0, T_Start, alpha=0.5, color="#FFCDCB", label="Holding Time")
                self.axes.fill_between([t_Process-RipeningTime, t_Process], 0, T_Start, alpha=0.5, color="#AEE2FF", label="Ripening Time")
                self.axes.legend(prop={"size": 6})
                self.draw()

                if Profile == "Alternating":
                        JSON_file = open(os.path.dirname(__file__) + "\\DWSIM\\Input.json")
                        parsed_data = json.load(JSON_file)
                        parsed_data["A"] = popt[0]
                        parsed_data["B"] = popt[1]
                        parsed_data["C"] = popt[2]
                        parsed_data["D"] = popt[3]
                        with open(os.path.dirname(__file__) + "\\DWSIM\\Input.json", "w") as json_file:
                                json.dump(parsed_data, json_file, indent=4)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    qdarktheme.setup_theme(theme="light", corner_shape="sharp", custom_colors={
        "[light]": {
            "primary": "#84bc34",
        }})
    mainWindow = QtWidgets.QMainWindow()
    ui = Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec_())