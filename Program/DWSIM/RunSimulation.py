#%_________________________IMPORTANT_________________________%
#|                                                           |#
#|WHEN THE SCRIPT IS RUN ON A DIFFERENT MACHINE,             |#
#|THIS FILEPATH TO THE DWSIM DLLs HAS TO BE CHANGED MANUALLY!|#
#|                                                           |#
dwsimpath = "C:\\Program Files\\DWSIM\\"
#|                                                           |#
#|WHEN THE SCRIPT IS RUN ON A DIFFERENT MACHINE,             |#
#|THIS FILEPATH TO THE DWSIM DLLs HAS TO BE CHANGED MANUALLY!|#
#|                                                           |#
#%_________________________IMPORTANT_________________________%

import clr
import os
import sys

Filepath = sys.argv[1]
SimulateCryst = int(float(sys.argv[2]))
SimulateFilt = int(float(sys.argv[3]))
SimulateWash = int(float(sys.argv[4]))
SimulateDry = int(float(sys.argv[5]))

import pythoncom
pythoncom.CoInitialize()

from System.IO import Directory, Path, File
from System import String, Environment

clr.AddReference(dwsimpath + "DWSIM")
clr.AddReference(dwsimpath + "CapeOpen.dll")
clr.AddReference(dwsimpath + "DWSIM.Automation.dll")
clr.AddReference(dwsimpath + "DWSIM.Interfaces.dll")
clr.AddReference(dwsimpath + "DWSIM.GlobalSettings.dll")
clr.AddReference(dwsimpath + "DWSIM.SharedClasses.dll")
clr.AddReference(dwsimpath + "DWSIM.Thermodynamics.dll")
clr.AddReference(dwsimpath + "DWSIM.UnitOperations.dll")
clr.AddReference(dwsimpath + "DWSIM.FlowsheetSolver.dll")
clr.AddReference(dwsimpath + "DWSIM.Inspector.dll")
clr.AddReference(dwsimpath + "System.Buffers.dll")

from DWSIM.Automation import Automation3
Directory.SetCurrentDirectory(dwsimpath)

interf = Automation3()

if SimulateCryst == 1:
    sim = interf.LoadFlowsheet2(Filepath + "\\Crystallization.dwxmz")
if SimulateFilt == 1 and SimulateWash == 0:
    sim2 = interf.LoadFlowsheet2(Filepath + "\\Filtration.dwxmz")
if SimulateFilt == 1 and SimulateWash == 1:
    sim3 = interf.LoadFlowsheet2(Filepath + "\\FiltrationWashing.dwxmz")
if SimulateDry == 1:
    sim4 = interf.LoadFlowsheet2(Filepath + "\\Drying.dwxmz")

print([1])
sys.stdout.flush()