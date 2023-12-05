# -*- coding: utf-8 -*-

from __future__ import annotations

from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import pandas as pd
import sys
import os
import qdarktheme
import json
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import cm
mpl.use("QT5Agg")
from matplotlib.figure import Figure
from PyQt5.QtCore import pyqtSlot, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi

from typing import *

#Read JSON file (required to get some of the inputs)
JSON_file = open(os.path.join(os.getcwd(), "DWSIM") + "\\Input.json")
parsed_data = json.load(JSON_file)

CycleTime = parsed_data["CycleTime"]
CrystalModules = parsed_data["CrystallizationModules"]
delta = parsed_data["Delta"]
Length = parsed_data["Length"]

color1, color2, color3, color4, color5 = "#000000", "#E69E00", "#57B5E8", "#009E73", "#CC78A6"

#CrystallizationSim = int(sys.argv[1])
#FiltrationSim = int(sys.argv[2])
#WashingSim = int(sys.argv[3])
#DryingSim = int(sys.argv[3])

CrystallizationSim, FiltrationSim, WashingSim, DryingSim = 1, 1, 1, 1
fname = os.path.dirname(__file__)

class CSD_3D_MyMplCanvas(FigureCanvasQTAgg):
        def __init__(self, parent=None):

                #fig = Figure(figsize=(5, 3.3))
                fig = Figure()
                FigureCanvasQTAgg.__init__(self, fig)
                self.axes = fig.add_subplot(111, projection="3d")
                FigureCanvasQTAgg.__init__(self, fig)
                FigureCanvasQTAgg.setSizePolicy(self,
                                              QSizePolicy.Expanding,
                                              QSizePolicy.Expanding)
                FigureCanvasQTAgg.updateGeometry(self)
                self.compute_figure()
        def compute_figure(self):
                pass

class CSD_3D_MyStaticMplCanvas(CSD_3D_MyMplCanvas):
        def compute_figure(self):

                Excel_File = fname + '\\DWSIM\\Output\\CrystallizationOutput.xlsx'
                df = pd.read_excel(Excel_File, header=None)
                df = df.drop([1,2,3,4,5,6,7])
                #,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37
                df = df.drop(columns=[0])

                x = df.iloc[0].values
                df = df.iloc[1:16]
                y = np.array(Length)
                y = y[:15]
                X,Y = np.meshgrid(x,y)
                Z = df.values

                self.axes.set_xlim3d(left=delta, right=CrystalModules*CycleTime)
                self.axes.plot_surface(X, Y, Z, cmap=cm.coolwarm)
                self.axes.set_xlabel("Time [s]")
                self.axes.set_ylabel("Diameter [$\mu$m]")
                self.axes.set_ylim(ymin=y[0], ymax=y[14])
                self.axes.set_zlabel("$q_0$")
                self.axes.view_init(azim=-45, elev=30)
                self.axes.set_box_aspect((1, 1, 1))
                self.draw()
                return super().compute_figure()

class My_2D_StaticCanvas2Axes(FigureCanvasQTAgg):
        def __init__(self, parent=None):
                fig = Figure()
                FigureCanvasQTAgg.__init__(self, fig)
                self.axes = fig.add_subplot()
                fig.tight_layout(rect=[.1,.1,.9,.9])
                self.axes2 = self.axes.twinx()

                self.axes2.spines["right"].set_color(color2)
                self.axes2.spines["right"].set_position(("outward", 0))
                FigureCanvasQTAgg.__init__(self, fig)
                FigureCanvasQTAgg.setSizePolicy(self,
                                                QSizePolicy.Expanding,
                                                QSizePolicy.Expanding)
                FigureCanvasQTAgg.updateGeometry(self)
                self.compute_figure()
        def compute_figure(self):
                pass

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
                self.compute_figure()
        def compute_figure(self):
                pass

class YieldMass_StaticCanvas(My_2D_StaticCanvas2Axes):
        def compute_figure(self):
                                
                Excel_File = fname + '\\DWSIM\\Output\\CrystallizationOutput.xlsx'
                df = pd.read_excel(Excel_File, header=None)
                df = df.drop(columns=[0])
                x = df.iloc[0].values
                y_1 = df.iloc[4].values * 10**3
                y_2 = df.iloc[5].values

                self.axes.set_ylim(ymin=0)
                self.axes.set_ylim(ymin=0, ymax=25)
                self.axes2.set_ylim(ymin=0, ymax=100)

                self.axes.set_ylabel("Crystal mass [g]")
                self.axes.set_xlabel("Time [s]")
                self.axes2.set_ylabel("Yield [%]")

                line1, = self.axes.plot(x, y_1, color = color1)
                line2, = self.axes2.plot(x, y_2, color = color2)

                self.axes.legend([line1, line2],
                                 ["Crystal mass [g]", "Yield[%]"],
                                 prop={'size': 6})
                #plt.savefig(os.path.join(fname, "Test.svg"))
                self.draw()
                
                return super().compute_figure()
        
class ConcTime_staticCanvas(My_2D_StaticCanvas2Axes):
        def compute_figure(self):
                Excel_File = fname + '\\DWSIM\\Output\\CrystallizationOutput.xlsx'
                df = pd.read_excel(Excel_File, header=None)
                df = df.drop(columns=[0])
                x = df.iloc[0].values
                y_1 = df.iloc[2].values
                y_2 = df.iloc[1].values
                self.axes.set_ylabel("Concentration [$g\cdot g_{Solution}^{-1}$]")
                self.axes2.set_ylabel("Temperature [°C]")
                self.axes.set_xlabel("Time [s]")
                line1, = self.axes.plot(x, y_1, color=color1)
                line2, = self.axes2.plot(x, y_2, color=color2)

                self.axes.legend([line1, line2],
                                 ["Concentration [$g\cdot g_{Solution}^{-1}$]", "Temperature [°C]"],
                                 prop={"size": 6})

                self.draw()
                return super().compute_figure()
        
class ConcTemp_staticCanvas(My_2D_StaticCanvas):
        def compute_figure(self):

                Excel_File = fname + '\\DWSIM\\Output\\CrystallizationOutput.xlsx'
                df = pd.read_excel(Excel_File, header=None)
                df = df.drop(columns=[0])
                x = df.iloc[1].values
                y = df.iloc[2].values
                y2 = df.iloc[6].values
                line, = self.axes.plot(x, y, color=color1)
                line2, = self.axes.plot(x, y2, color=color2)
                self.axes.legend([line, line2],
                                 ["Solubility line", "Concentration"],
                                 prop={'size': 6})
                self.axes.set_ylabel("Concentration [$g\cdot g_{Solution}^{-1}$]")
                self.axes.set_xlabel("Temperature [°C]")
                self.draw()
                return super().compute_figure()

class FiltVol_staticCanvas(My_2D_StaticCanvas):
        def compute_figure(self):

                Excel_File = fname + "\\DWSIM\\Output\\FiltrationOutput.xlsx"
                df = pd.read_excel(Excel_File, "Results")
                x = df.iloc[:, 0]
                y = df.iloc[:, 1]

                if parsed_data["Confidence"] == "Est":
                        y_1 = df.iloc[:, 8]
                        y_2 = df.iloc[:, 9]
                        y_4 = df.iloc[:, 10]
                        y_5 = df.iloc[:, 11]


                colors_column = df.iloc[:, 7]
                color_mapping = {
                        "Filtration": "#FFCDCB",
                        "Deliquoring": "#AEE2FF",
                        "Washing": "#99DEBA"
                }
                colors = [color_mapping.get(value, "gray") for value in colors_column]

                line1, = self.axes.plot(x, y, color=color1)

                for i in range(len(x) - 1):
                        self.axes.fill_between(x[i:i+2], 0, max(y), color=colors[i])

                for i, (label, color) in enumerate(color_mapping.items()):
                        x_positions = [x[j] for j in range(len(colors)) if colors[j] == color]
                        if x_positions:
                                x_center = sum(x_positions) / len(x_positions)
                                y_center = max(y) / 20  # Adjust the y-position as needed
                                self.axes.text(x_center, y_center, label, color='black', fontsize=8, ha='center')
                if parsed_data["Confidence"] == "Est":
                        self.axes.fill_between(x, y_1, y_2, alpha=0.5, edgecolor=color1, facecolor=color2)
                        self.axes.fill_between(x, y_4, y_5, alpha=0.2, edgecolor=color1, facecolor=color3)
                self.axes.set_ylabel("Filtrate Volume [mL]")
                self.axes.set_xlabel("Time [s]")
                self.draw()
                return super().compute_figure()
        
class SatFilt_staticCanvas(My_2D_StaticCanvas2Axes):
        def compute_figure(self):
                Excel_File = fname + "\\DWSIM\\Output\\FiltrationOutput.xlsx"
                df = pd.read_excel(Excel_File, "Results")
                x = df.iloc[:, 0]
                y_1 = df.iloc[:, 4]
                y_2 = df.iloc[:, 6]

                if parsed_data["Confidence"] == "Est":
                        y_3 = df.iloc[:, 12]
                        y_4 = df.iloc[:, 13]
                        y_6 = df.iloc[:, 14]
                        y_7 = df.iloc[:, 15]

                colors_column = df.iloc[:, 7]
                color_mapping = {
                        "Filtration": "#FFCDCB",
                        "Deliquoring": "#AEE2FF",
                        "Washing": "#99DEBA"
                }
                colors = [color_mapping.get(value, "gray") for value in colors_column]

                self.axes.set_ylabel("Cake Loading [g$_{Liquid}\cdot$g$_{Crystal}^{-1}$]")
                self.axes.set_xlabel("Time [s]")
                self.axes2.set_ylabel("log(Cake Saturation) [-]")

                line1, = self.axes.plot(x, y_1, color = color1)

                line2, = self.axes2.plot(x, y_2, color = color2)

                for i in range(len(x) - 1):
                        self.axes.fill_between(x[i:i+2], 0, max(y_2), color=colors[i])

                for i, (label, color) in enumerate(color_mapping.items()):
                        x_positions = [x[j] for j in range(len(colors)) if colors[j] == color]
                        if x_positions:
                                x_center = sum(x_positions) / len(x_positions)
                                y_center = max(y_2) / 20  # Adjust the y-position as needed
                                self.axes.text(x_center, y_center, label, color='black', fontsize=8, ha='center')
                if parsed_data["Confidence"] == "Est":
                        self.axes.fill_between(x, y_3, y_4, alpha=0.5, edgecolor=color1, facecolor=color2)
                        self.axes.fill_between(x, y_6, y_7, alpha=0.2, edgecolor=color1, facecolor=color3)

                self.axes.legend([line1, line2],
                                 ["Cake Loading [g$\cdot$g$^{-1}$]", "Saturation [-]"],
                                 prop={'size': 6})
                
                self.axes2.set_yscale("log")

                self.draw()
                plt.show()
                return super().compute_figure()
        
class FracRem_staticCanvas(My_2D_StaticCanvas):
        def compute_figure(self):
                Excel_File = fname + "\\DWSIM\\Output\\FiltrationOutput.xlsx"
                df = pd.read_excel(Excel_File, "WashingResults")
                x = df.iloc[:, 1]
                y = df.iloc[:, 3]
                line, = self.axes.plot(x, y, color=color1)
                self.axes.set_xlabel("$\mathcal{W}$ [-]")
                self.axes.set_ylabel("Fractional removal [-]")
                self.draw()
                
                return super().compute_figure()

class WashPhi_staticCanvas(My_2D_StaticCanvas):
        def compute_figure(self):
                Excel_File = fname + "\\DWSIM\\Output\\FiltrationOutput.xlsx"
                df = pd.read_excel(Excel_File, "WashingResults")
                x = df.iloc[:, 1]
                y = df.iloc[:, 2]
                line, = self.axes.plot(x, y, color=color1)
                self.axes.set_xlabel("$\mathcal{W}$ [-]")
                self.axes.set_ylabel("$\phi$ [-]")
                self.draw()

                return super().compute_figure()
        
class DryingRate_staticCanvas(My_2D_StaticCanvas):
        def compute_figure(self):
                Excel_File = fname + "\\DWSIM\\Output\\DryingOutput.xlsx"
                df = pd.read_excel(Excel_File, "Results")
                x = df.iloc[:, 0]
                y = df.iloc[:, 1]
                line, = self.axes.plot(x,y, color=color1)
                self.axes.set_xlabel("Time [s]")
                self.axes.set_ylabel("Volumetric drying rate [kg/(m$^3$$\cdot$s)]")
                self.draw()
                return super().compute_figure()
        
class SatDry_staticCanvas(My_2D_StaticCanvas2Axes):
        def compute_figure(self):
                Excel_File = fname + "\\DWSIM\\Output\\DryingOutput.xlsx"
                df = pd.read_excel(Excel_File, "Results")
                x = df.iloc[:, 0]
                y = df.iloc[:, 2]
                y_1 = df.iloc[:, 3]
                line, = self.axes.plot(x,y, color=color1)
                line1, = self.axes2.plot(x,y_1, color=color2)
                self.axes.set_xlabel("Time [s]")
                self.axes.set_ylabel("Cake loading [kg$\cdot$kg$^{-1}$]")
                self.axes2.set_ylabel("Cake temperature [°C]")

                self.axes.legend([line, line1],
                                 ["Cake loading", "Temperature [°C]"],
                                 prop={"size": 6})

                self.draw()
                return super().compute_figure()
        
class CakeTemp_staticCanvas(CSD_3D_MyMplCanvas):
        def compute_figure(self):
                Excel_File = fname + "\\DWSIM\\Output\\DryingOutput.xlsx"
                df = pd.read_excel(Excel_File, "Results")
                x = df.iloc[:, 0]
                y = np.array([0, 1, 2, 3, 4, 5])
                X,Y = np.meshgrid(x,y)
                df = df.iloc[:, 11:17]
                Z = df.values.T
                #self.axes.set_xlim3d(left=0, right=CrystalModules*CycleTime)
                self.axes.plot_surface(X, Y, Z, cmap=cm.coolwarm)
                self.axes.set_xlabel("Time [s]")
                self.axes.set_ylabel("Discretization Interval")
                #self.axes.set_ylim(ymin=y[0], ymax=y[14])
                self.axes.set_zlabel("Air Temperature [°C]")
                self.axes.view_init(azim=-45, elev=30)
                self.axes.set_box_aspect((1, 1, 1))
                self.draw()

                return super().compute_figure()
        
class AirTemp_staticCanvas(CSD_3D_MyMplCanvas):
        def compute_figure(self):
                Excel_File = fname + "\\DWSIM\\Output\\DryingOutput.xlsx"
                df = pd.read_excel(Excel_File, "Results")
                x = df.iloc[:, 0]
                y = np.array([0, 1, 2, 3, 4, 5])
                X,Y = np.meshgrid(x,y)
                df = df.iloc[:, 5:11]
                Z = df.values.T
                #self.axes.set_xlim3d(left=0, right=CrystalModules*CycleTime)
                self.axes.plot_surface(X, Y, Z, cmap=cm.coolwarm)
                self.axes.set_xlabel("Time [s]")
                self.axes.set_ylabel("Discretization Interval")
                #self.axes.set_ylim(ymin=y[0], ymax=y[14])
                self.axes.set_zlabel("Air Loading [kg$\cdot$kg$^{-1}$]")
                self.axes.view_init(azim=-45, elev=30)
                self.axes.set_box_aspect((1, 1, 1))
                self.draw()

                return super().compute_figure()

#__________Generate and translate the main window________#
class Results_MainWindow(QtWidgets.QMainWindow):
        def setupUi(self, MainWindow):
                MainWindow.setObjectName("MainWindow")
                MainWindow.resize(1200, 785)
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(fname+"\\Graphics\\AD2.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)      
                MainWindow.setWindowIcon(icon)
                self.centralwidget = QtWidgets.QWidget(MainWindow)
                self.centralwidget.setObjectName("centralwidget")
                self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
                self.tabWidget.setGeometry(QtCore.QRect(25, 10, 1150, 765))
                font = QtGui.QFont()
                font.setFamily("Segoe UI Semibold")
                font.setPointSize(10)
                font.setBold(False)
                font.setItalic(False)
                font.setWeight(9)
                self.tabWidget.setFont(font)
                self.tabWidget.setObjectName("tabWidget")
                self.tabWidget.setStyleSheet("font-weight: 900; color: black;\n"
                "font: 75 10pt \"Segoe UI Semibold\";\n"
                "\n"
                "")

                if CrystallizationSim == 1:

                        self.Crystallization = QtWidgets.QWidget()
                        self.Crystallization.setObjectName("Crystallization")
                        self.CSD = QtWidgets.QGroupBox(self.Crystallization)
                        self.CSD.setGeometry(QtCore.QRect(25, 10, 540, 330))
                        self.CSD.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.CSD.setObjectName("CSD")

                        lay = QtWidgets.QVBoxLayout(self.CSD)
                        lay.setGeometry(QtCore.QRect(10, 20, 520, 300))
                        self.GraphCSD3D = CSD_3D_MyStaticMplCanvas(self.CSD)
                        lay.addWidget(self.GraphCSD3D)


                        self.Yield = QtWidgets.QGroupBox(self.Crystallization)
                        self.Yield.setGeometry(QtCore.QRect(580, 10, 540, 330))
                        self.Yield.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.Yield.setObjectName("Yield")

                        layYield = QtWidgets.QVBoxLayout(self.Yield)
                        layYield.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.YieldMass = YieldMass_StaticCanvas(self.Yield)
                        layYield.addWidget(self.YieldMass)

                        self.ConcTime = QtWidgets.QGroupBox(self.Crystallization)
                        self.ConcTime.setGeometry(QtCore.QRect(25, 355, 540, 330))
                        self.ConcTime.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.ConcTime.setObjectName("ConcTime")

                        layConcTime = QtWidgets.QVBoxLayout(self.ConcTime)
                        layConcTime.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.ConcTimePlot = ConcTime_staticCanvas(self.ConcTime)
                        layConcTime.addWidget(self.ConcTimePlot)

                        self.ConcTemp = QtWidgets.QGroupBox(self.Crystallization)
                        self.ConcTemp.setGeometry(QtCore.QRect(580, 355, 540, 330))
                        self.ConcTemp.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.ConcTemp.setObjectName("ConcTemp")

                        layConcTemp = QtWidgets.QVBoxLayout(self.ConcTemp)
                        layConcTemp.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.ConcTempPlot = ConcTemp_staticCanvas(self.ConcTemp)
                        layConcTemp.addWidget(self.ConcTempPlot)
                        
                        self.tabWidget.addTab(self.Crystallization, "")


                if FiltrationSim == 1:

                        self.Filtration = QtWidgets.QWidget()
                        self.Filtration.setObjectName("Filtration")
                        self.FiltVol = QtWidgets.QGroupBox(self.Filtration)
                        self.FiltVol.setGeometry(QtCore.QRect(25, 10, 540, 330))
                        self.FiltVol.setObjectName("FiltVol")
                        self.FiltVol.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        
                        layFiltVol = QtWidgets.QVBoxLayout(self.FiltVol)
                        layFiltVol.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.FiltVolPlot = FiltVol_staticCanvas(self.FiltVol)
                        layFiltVol.addWidget(self.FiltVolPlot)

                        self.SatFilt = QtWidgets.QGroupBox(self.Filtration)
                        self.SatFilt.setGeometry(QtCore.QRect(580, 10, 540, 330))
                        self.SatFilt.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.SatFilt.setObjectName("SatFilt")

                        laySatFilt = QtWidgets.QVBoxLayout(self.SatFilt)
                        laySatFilt.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.SatFiltPlot = SatFilt_staticCanvas(self.SatFilt)
                        laySatFilt.addWidget(self.SatFiltPlot)

                        self.tabWidget.addTab(self.Filtration, "")


                if WashingSim == 1:

                        self.Washing = QtWidgets.QWidget()
                        self.Washing.setObjectName("Washing")
                        self.FracRemoval = QtWidgets.QGroupBox(self.Washing)
                        self.FracRemoval.setGeometry(QtCore.QRect(25, 10, 540, 330))
                        self.FracRemoval.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.FracRemoval.setObjectName("FracRemoval")

                        layFracRem = QtWidgets.QVBoxLayout(self.FracRemoval)
                        layFracRem.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.FracRemPlot = FracRem_staticCanvas(self.FracRemoval)
                        layFracRem.addWidget(self.FracRemPlot)

                        self.WashPhi = QtWidgets.QGroupBox(self.Washing)
                        self.WashPhi.setGeometry(QtCore.QRect(580, 10, 540, 330))
                        self.WashPhi.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.WashPhi.setObjectName("WashPhi")

                        layWashPhi = QtWidgets.QVBoxLayout(self.WashPhi)
                        layWashPhi.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.WashPhiPlot = WashPhi_staticCanvas(self.WashPhi)
                        layWashPhi.addWidget(self.WashPhiPlot)

                        self.tabWidget.addTab(self.Washing, "")


                if DryingSim == 1:

                        self.Drying = QtWidgets.QWidget()
                        self.Drying.setObjectName("Drying")
                        self.DryingRate = QtWidgets.QGroupBox(self.Drying)
                        self.DryingRate.setGeometry(QtCore.QRect(25, 10, 540, 330))
                        self.DryingRate.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.DryingRate.setObjectName("DryingRate")

                        layDryingRate = QtWidgets.QVBoxLayout(self.DryingRate)
                        layDryingRate.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.DryingRatePlot = DryingRate_staticCanvas(self.DryingRate)
                        layDryingRate.addWidget(self.DryingRatePlot)

                        self.SatDry = QtWidgets.QGroupBox(self.Drying)
                        self.SatDry.setGeometry(QtCore.QRect(580, 10, 540, 330))
                        self.SatDry.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.SatDry.setObjectName("SatDry")

                        laySatDry = QtWidgets.QVBoxLayout(self.SatDry)
                        laySatDry.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.SatDryPlot = SatDry_staticCanvas(self.SatDry)
                        laySatDry.addWidget(self.SatDryPlot)

                        self.CakeTemp = QtWidgets.QGroupBox(self.Drying)
                        self.CakeTemp.setGeometry(QtCore.QRect(25, 355, 540, 330))
                        self.CakeTemp.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.CakeTemp.setObjectName("CakeTemp")

                        layCakeTemp = QtWidgets.QVBoxLayout(self.CakeTemp)
                        layCakeTemp.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.CakeTempPlot = CakeTemp_staticCanvas(self.CakeTemp)
                        layCakeTemp.addWidget(self.CakeTempPlot)

                        self.AirTemp = QtWidgets.QGroupBox(self.Drying)
                        self.AirTemp.setGeometry(QtCore.QRect(580, 355, 540, 330))
                        self.AirTemp.setStyleSheet(u"QGroupBox { \n"
                                "     border: 1px solid black; \n"
                                "     border-radius: 5px; \n"
                                "background-color: white;}\n"
                                "QGroupBox::title {\n"
                                "    subcontrol-origin: margin;\n"
                                "    left: 10px;\n"
                                "    padding: -6px 0px 0 0px;\n"
                                "	font-weight: 900;\n"
                                "	color: #84bc34;\n"
                                "	font: 75 12pt \"Segoe UI Semibold\";\n"
                                "}")
                        self.AirTemp.setObjectName("AirTemp")

                        layAirTemp = QtWidgets.QVBoxLayout(self.AirTemp)
                        layAirTemp.setGeometry(QtCore.QRect(20, 20, 500, 240))
                        self.AirTempPlot = AirTemp_staticCanvas(self.AirTemp)
                        layAirTemp.addWidget(self.AirTempPlot)

                        self.tabWidget.addTab(self.Drying, "")

                

                MainWindow.setCentralWidget(self.centralwidget)
                self.menubar = QtWidgets.QMenuBar(MainWindow)
                self.menubar.setGeometry(QtCore.QRect(0, 0, 1200, 21))
                self.menubar.setObjectName("menubar")
                MainWindow.setMenuBar(self.menubar)
                self.statusbar = QtWidgets.QStatusBar(MainWindow)
                self.statusbar.setObjectName("statusbar")
                MainWindow.setStatusBar(self.statusbar)

                self.retranslateUi(MainWindow)
                self.tabWidget.setCurrentIndex(0)
                QtCore.QMetaObject.connectSlotsByName(MainWindow)

        def retranslateUi(self, MainWindow):
                _translate = QtCore.QCoreApplication.translate
                MainWindow.setWindowTitle(_translate("MainWindow", "Simulation Results"))

                if CrystallizationSim == 1:

                        self.CSD.setTitle(_translate("MainWindow", "Crystal Size Distribution"))
                        self.Yield.setTitle(_translate("MainWindow", "Yield"))
                        self.ConcTime.setTitle(_translate("MainWindow", "Concentration Over Time"))
                        self.ConcTemp.setTitle(_translate("MainWindow", "Concentration Over Temperature"))
                        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Crystallization), _translate("MainWindow", "Crystallization"))

                if FiltrationSim == 1:

                        self.FiltVol.setTitle(_translate("MainWindow", "Filtrate Volume"))
                        self.SatFilt.setTitle(_translate("MainWindow", "Saturation and Cake Loading"))
                        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Filtration), _translate("MainWindow", "Filtration"))
                
                if WashingSim == 1:

                        self.FracRemoval.setTitle(_translate("MainWindow", "Fractional Removal"))
                        self.WashPhi.setTitle(_translate("MainWindow", "Phi"))
                        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Washing), _translate("MainWindow", "Washing"))
                
                if DryingSim == 1:
                
                        self.DryingRate.setTitle(_translate("MainWindow", "Drying Rate"))
                        self.SatDry.setTitle(_translate("MainWindow", "Cake Loading and Cake Temperature"))
                        self.CakeTemp.setTitle(_translate("MainWindow", "Air Temperature"))
                        self.AirTemp.setTitle(_translate("MainWindow", "Air Loading"))
                        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Drying), _translate("MainWindow", "Drying"))     


if __name__ == "__main__":
        import sys
        app = QtWidgets.QApplication(sys.argv)
        qdarktheme.setup_theme(theme="light",
                               corner_shape="sharp",
                               custom_colors={"[light]": {"primary": "#84bc34",}})
        MainWindow = QtWidgets.QMainWindow()
        ui = Results_MainWindow()
        ui.setupUi(MainWindow)
        MainWindow.show()
        sys.exit(app.exec_())
