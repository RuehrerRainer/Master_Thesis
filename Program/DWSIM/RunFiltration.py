
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

import clr, os, sys

#Filepath = sys.argv[1]
Filepath = "C:\\Users\\Maxim\\Documents\\GitHub\\MasterThesis\\Program\\DWSIM\\DWSIM_Files\\"

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
sim = interf.LoadFlowsheet2(Filepath + "Filtration.dwxmz")
errors = interf.CalculateFlowsheet4(sim)
if sys.argv[2] == "Simulation":
    print([1, 1])
    sys.stdout.flush()