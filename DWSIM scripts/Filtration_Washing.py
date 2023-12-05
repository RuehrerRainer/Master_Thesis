#Filepath where input and output worksheets are stored


# ___________________IMPORTANT____________________
#/                                                \
#| THIS PATH NEEDS TO BE ADJUSTED MANUALLY IF THE  |
#| SCRIPT IS RUN ON A DIFFERENT MACHINE!           |
#|                                                 |
SystemPath = "C:\\Users\\Maxim\\Documents\\GitHub\\MasterThesis\\Program\\DWSIM\\"
#|                                                 |
#| THIS PATH NEEDS TO BE ADJUSTED MANUALLY IF THE  |
#| SCRIPT IS RUN ON A DIFFERENT MACHINE!           |
#|                                                 |
#\___________________IMPORTANT_____________________/

import math, clr, System.GC
from DWSIM.Thermodynamics import *
from System import Array
from System.IO import File, StreamReader

clr.AddReference('DWSIM.MathOps.DotNumerics')
from DotNumerics.ODE import *

#Import of Excel .net framework
clr.AddReferenceByName('Microsoft.Office.Interop.Excel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c')
from Microsoft.Office.Interop import Excel
ex = Excel.ApplicationClass()
ex.Visible = False
ex.DisplayAlerts = True

datasheet = ex.Workbooks.Open(SystemPath + 'Output\\CrystallizationOutput.xlsx')
Res1 = datasheet.Worksheets[1]

#Reads a .json file with input parameters
#Values are stored as dictionary "parsed_data"
jsonstring = open(SystemPath + 'Input.json').read()
parsed_data = eval(jsonstring)

#Initialize input streams
feed1 = [0]
P1 = [0]
massflow1 = [0]
molefrac1 = [0]
moleflow1 = [0]
enthalpy1 = [0]
T1 = [0]

feed1[0] = ims1
P1 = feed1[0].GetProp("pressure", "Overall", None, "", "")
massflow1 = feed1[0].GetProp("totalFlow", "Overall" , None, "", "mass")
moleflow1 = feed1[0].GetProp("totalFlow", "Overall", None, "", "mole")
volflow1 = feed1[0].GetProp("totalFlow", "Overall", None, "", "volume")
enthalpy1 = feed1[0].GetProp("enthalpy", "Overall", None, "Mixture", "mass")
molefrac1 = feed1[0].GetProp("fraction", "Overall", None, "", "mole")
T1 = feed1[0].GetProp("temperature", "Overall", None, "", "")
massfrac1 = feed1[0].GetProp("fraction", "Overall", None, "", "mass")
comp1 = len(molefrac1) #total number of components/elements

def ReturnFluidDensity(strComp, fltTemp):
    """
    Returns the fluid density of a component at the given Temperature [K].
    !!!! The component already has to be part of the DWSIM simulation file !!!!
    """
    Comps = [strComp]
    Props = ["densityofliquid"]
    FlDensity = ims1.GetTDependentProperty(Props, fltTemp, Comps, None)
    return FlDensity[0]

def ReturnFluidViscosity(strComp, fltTemp):
    """
    Returns the fluid viscosity of a component at the given Temperature [K].
    !!!! The component already has to be part of the DWSIM simulation file !!!!
    """
    Comps = [strComp]
    Props = ["viscosityofliquid"]
    FlVisco = ims1.GetTDependentProperty(Props, fltTemp, Comps, None)
    return FlVisco[0]

#Generate a new output Excel sheet
outputsheet = ex.Workbooks.Add()
outputsheet.Worksheets.Add()
outputsheet.Worksheets.Add()
Out1 = outputsheet.Worksheets[1]
Out1.Name = "Results"

#Exported parameters from the main loop
Out1.UsedRange.Cells[1, 1].Value2 = "Time [s]"
Out1.UsedRange.Cells[1, 2].Value2 = "Filtrate Volume [mL]"
Out1.UsedRange.Cells[1, 3].Value2 = "Filtration speed"
Out1.UsedRange.Cells[1, 4].Value2 = "t/Filtrate [s/mL]"
Out1.UsedRange.Cells[1, 5].Value2 = "Moisture [g_L/g_S]"
Out1.UsedRange.Cells[1, 6].Value2 = "Moisture [g_L/(g_L+g_S)]"
Out1.UsedRange.Cells[1, 7].Value2 = "Saturation [-]"
Out1.UsedRange.Cells[1, 8].Value2 = "Underlying kinetics"

t_Process = int(parsed_data["FiltrationTime"])
delta = int(parsed_data["Delta"])
t_Crystallization = int(parsed_data["CycleTime"] * parsed_data["CrystallizationModules"])
rho_Cryst = float(parsed_data["CrystalDensity"])
Area = parsed_data["CrystallizerLength"] * parsed_data["CrystallizerWidth"]
VolFactor = parsed_data["ShapeFactor"]
DeltaP = parsed_data["DeltaP_Filt"] * 10**5
yIntercept = parsed_data["yIntercept"]
Slope = parsed_data["Slope"]
Temperature = parsed_data["T_Filt"]
rho_MothLiq = ReturnFluidDensity(parsed_data["MotherLiquor"], Temperature)
FlowRate = parsed_data["FlowRate_Wash"]
SeedMass = parsed_data["SeedMass"]
MassMotherLiquor = parsed_data["MassMothLiq"]


DiffCoeff = parsed_data["DiffusionCoefficient"] #%%%%%%%%%%
DeltaP_Wash = parsed_data["DeltaP_Wash"] * 10**5


#%%%%%---------- Required for Washing calculation ----------%%%%%#
#Dictionary of arrays required for calculation of fractional removal
FractionalRemoval = {
    0:[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    1: [0.059, 0.068, 0.075, 0.093, 0.098, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    2: [0.074, 0.1, 0.118, 0.169, 0.187, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
    3: [0.085, 0.123, 0.15, 0.229, 0.262, 0.298, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
    4: [0.094, 0.143, 0.176, 0.28, 0.327, 0.391, 0.399, 0.4, 0.4, 0.4, 0.4, 0.4],
    5: [0.102, 0.159, 0.199, 0.323, 0.382, 0.476, 0.496, 0.5, 0.5, 0.5, 0.5, 0.5],
    6: [0.110, 0.175, 0.220, 0.361, 0.430, 0.552, 0.586, 0.6, 0.6, 0.6, 0.6, 0.6],
    7: [0.116, 0.188, 0.238, 0.395, 0.472, 0.618, 0.668, 0.698, 0.7, 0.7, 0.7, 0.7],
    8: [0.122, 0.201, 0.255, 0.426, 0.51, 0.675, 0.793, 0.79, 0.797, 0.8, 0.8, 0.8],
    9: [0.128, 0.213, 0.27, 0.454, 0.544, 0.723, 0.799, 0.868, 0.882, 0.897, 0.898, 0.898],
    10: [0.134, 0.224, 0.285, 0.479, 0.575, 0.764, 0.85, 0.929, 0.947, 0.972, 0.975, 0.977],
    11: [0.139, 0.234, 0.299, 0.502, 0.602, 0.8, 0.891, 0.971, 0.988, 1, 1, 1],
    12: [0.144, 0.244, 0.311, 0.524, 0.628, 0.83, 0.923, 0.998, 1, 1, 1, 1],
    13: [0.149, 0.253, 0.323, 0.544, 0.651, 0.854, 0.949, 1, 1, 1, 1, 1],
    14: [0.153, 0.262, 0.335, 0.562, 0.672, 0.875, 0.969, 1, 1, 1, 1, 1],
    15: [0.158, 0.27, 0.346, 0.58, 0.691, 0.892, 0.984, 1, 1, 1, 1, 1],
    16: [0.162, 0.279, 0.356, 0.596, 0.709, 0.907, 0.996, 1, 1, 1, 1, 1],
    17: [0.166, 0.286, 0.366, 0.611, 0.725, 0.919, 1, 1, 1, 1, 1, 1],
    18: [0.169, 0.294, 0.376, 0.626, 0.741, 0.930, 1, 1, 1, 1, 1, 1],
    19: [0.173, 0.301, 0.385, 0.639, 0.755, 0.938, 1, 1, 1, 1, 1, 1],
    20: [0.177, 0.308, 0.394, 0.652, 0.768, 0.946, 1, 1, 1, 1, 1, 1],
    21: [0.18, 0.315, 0.403, 0.664, 0.781, 0.953, 1, 1, 1, 1, 1, 1],
    22: [0.184, 0.322, 0.412, 0.676, 0.792, 0.959, 1, 1, 1, 1, 1, 1],
    23: [0.187, 0.328, 0.42, 0.687, 0.803, 0.963, 1, 1, 1, 1, 1, 1],
    24: [0.19, 0.334, 0.428, 0.698, 0.813, 0.967, 1, 1 ,1, 1, 1, 1],
    25: [0.193, 0.34, 0.435, 0.708, 0.823, 0.971, 1, 1, 1, 1, 1, 1],
    26: [0.196, 0.346, 0.443, 0.718, 0.832, 0.974, 1, 1, 1, 1, 1, 1],
    27: [0.199, 0.352, 0.45, 0.727, 0.84, 0.976, 1, 1, 1, 1, 1, 1],
    28: [0.202, 0.357, 0.458, 0.736, 0.848, 0.978, 1, 1, 1, 1, 1, 1],
    29: [0.205, 0.363, 0.465, 0.744, 0.856, 0.98, 1, 1, 1, 1, 1, 1],
    30: [0.208, 0.368, 0.472, 0.752, 0.863, 0.982, 1, 1, 1, 1, 1, 1],
    31: [0.211, 0.374, 0.478, 0.76, 0.87, 0.983, 1, 1, 1, 1, 1, 1],
    32: [0.214, 0.379, 0.485, 0.768, 0.876, 0.984, 1, 1, 1, 1, 1, 1],
    33: [0.217, 0.384, 0.492, 0.776, 0.882, 0.985, 1, 1, 1, 1, 1, 1],
    34: [0.22, 0.389, 0.498, 0.783, 0.888, 0.986, 1, 1, 1, 1, 1, 1],
    35: [0.222, 0.394, 0.505, 0.79, 0.894, 0.986, 1, 1, 1, 1, 1, 1],
    36: [0.225, 0.399, 0.511, 0.797, 0.9, 0.987, 1, 1, 1, 1, 1, 1],
    37: [0.228, 0.404, 0.517, 0.804, 0.905, 0.987, 1, 1, 1, 1, 1, 1],
    38: [0.231, 0.409, 0.524, 0.811, 0.91 ,0.988, 1, 1, 1, 1, 1, 1],
    39: [0.233, 0.413, 0.53, 0.818, 0.915, 0.988, 1, 1, 1, 1, 1, 1],
    40: [0.236, 0.418, 0.536, 0.824, 0.92, 0.988, 1, 1, 1, 1, 1, 1],
}
#%%%%%---------- Required for Washing calculation ----------%%%%%#
#Literature functions for W vs Phi* correlations
def WPhi_001(fltWashRatio):
    if 0 <= fltWashRatio < 1:
        return 1
    elif fltWashRatio >= 1:
        return 0.0524 * (fltWashRatio*10**(-1))**(-0.5311)
def WPhi_005(fltWashRatio):
    if 0 <= fltWashRatio < 1:
        return 1
    elif fltWashRatio >= 1:
        return 0.1036 * (fltWashRatio*10**(-1))**(-0.5848)
def WPhi_01(fltWashRatio):
    if 0 <= fltWashRatio < 1:
        return 1
    elif fltWashRatio >= 1:
        return 0.1364 * (fltWashRatio*10**(-1))**(-0.6037)
def WPhi_05(fltWashRatio):
    if 0 <= fltWashRatio < 1:
        return 1
    elif 1 <= fltWashRatio < 16:
        return 1.0754 - 2.609 * (fltWashRatio*10**(-1)) + 3.5187 * (fltWashRatio*10**(-1))**2 - 2.3065 * (fltWashRatio*10**(-1))**3 + 0.5687 * (fltWashRatio*10**(-1))**4
    elif fltWashRatio >= 16:
        return 0.2481 * (fltWashRatio*10**(-1))**(-0.995)
def WPhi_1(fltWashRatio):
    if 0 <= fltWashRatio < 1:
        return 1
    elif 1 <= fltWashRatio < 17:
        return 1.1433 - 1.9882 * (fltWashRatio*10**(-1)) + 1.8761 * (fltWashRatio*10**(-1))**2 - 0.9206 * (fltWashRatio*10**(-1))**3 + 0.1798 * (fltWashRatio*10**(-1))**4
    elif fltWashRatio >= 17:
        return 0.3515 * (fltWashRatio*10**(-1))**(-1.4654)
def WPhi_5(fltWashRatio):
    if 0 <= fltWashRatio <= 1:
        return 1
    elif 1 < fltWashRatio < 20:
        return 1.0583 + 0.0795 * (fltWashRatio*10**(-1)) - 1.7285 * (fltWashRatio*10**(-1))**2 + 1.241 * (fltWashRatio*10**(-1))**3 - 0.2603 * (fltWashRatio*10**(-1))**4
    elif 20 <= fltWashRatio < 42:
        return 2.1739 * math.exp(-1.7383 * (fltWashRatio*10**(-1)))
    elif fltWashRatio >= 42:
        return 0
def WPhi_10(fltWashRatio):
    if 0 <= fltWashRatio <= 2:
        return 1
    elif 2 < fltWashRatio < 17:
        return 0.663 + 2.3569 * (fltWashRatio*10**(-1)) - 4.9493 * (fltWashRatio*10**(-1))**2 + 2.9684 * (fltWashRatio*10**(-1))**3 - 0.5826 * (fltWashRatio*10**(-1))**4
    elif 17 <= fltWashRatio < 33:
        return 11.5698 * math.exp(-2.9575 * (fltWashRatio*10**(-1)))
    elif fltWashRatio >= 33:
        return 0
def WPhi_50(fltWashRatio):
    if 0 <= fltWashRatio <= 5:
        return 1
    elif 5 < fltWashRatio < 14:
        return -5.3263 + 26.272 * (fltWashRatio*10**(-1)) - 37.56 * (fltWashRatio*10**(-1))**2 + 21.47 * (fltWashRatio*10**(-1))**3 - 4.3437 * (fltWashRatio*10**(-1))**4
    elif 14 <= fltWashRatio < 24:
        return 44.08 * math.exp(-4.667 * (fltWashRatio*10**(-1)))
    elif fltWashRatio >= 24:
        return 0
def WPhi_100(fltWashRatio):
    if 0 <= fltWashRatio <= 6:
        return 1
    elif 6 < fltWashRatio < 11:
        return -10.01 + 39.21 * (fltWashRatio*10**(-1)) - 46.46 * (fltWashRatio*10**(-1))**2 + 19.9 * (fltWashRatio*10**(-1))**3 - 2.122 * (fltWashRatio*10**(-1))**4
    elif 11 <= fltWashRatio < 22:
        return 0.5789 * (fltWashRatio*10**(-1))**(-8.0948)
    elif fltWashRatio >= 22:
        return 0
def WPhi_500(fltWashRatio):
    if 0 <= fltWashRatio <= 8:
        return 1
    elif 8 < fltWashRatio < 11:
        return -16.77 + 53.01 * (fltWashRatio*10**(-1)) - 49.87 * (fltWashRatio*10**(-1))**2 + 14.23 * (fltWashRatio*10**(-1))**3
    elif 11 <= fltWashRatio < 21:
        return 0.3095 * (fltWashRatio*10**(-1))**(-7.5097)
    elif fltWashRatio >= 21:
        return 0
def WPhi_1000(fltWashRatio):
    if 0 <= fltWashRatio <= 8:
        return 1
    elif 8 < fltWashRatio < 11:
        return 1.0583 + 0.0795 * (fltWashRatio*10**(-1)) - 1.7285 * (fltWashRatio*10**(-1))**2 + 1.241 * (fltWashRatio*10**(-1))**3
    elif 11 <= fltWashRatio < 18:
        return 94.13 * math.exp(6.9979 * (fltWashRatio*10**(-1)))
    elif fltWashRatio >= 18:
        return 0
def WPhi_10000(fltWashRatio):
    if 0 <= fltWashRatio <= 8:
        return 1
    elif 8 < fltWashRatio < 11:
        return -9.7886 + 26.83 * (fltWashRatio*10**(-1)) - 17.72 * (fltWashRatio*10**(-1))**2 + 1.3069 * (fltWashRatio*10**(-1))**3
    elif 11 <= fltWashRatio <= 14:
        return 0.0427 * (fltWashRatio*10**(-1))**(-7.9662)
    elif fltWashRatio > 14:
        return 0
DispersionLit = [0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000, 10000]
Functions = [WPhi_001, WPhi_005, WPhi_01, WPhi_05, WPhi_1, WPhi_5, WPhi_10, WPhi_50, WPhi_100, WPhi_500, WPhi_1000, WPhi_10000]

def Interpolate(intIndex, fltDispersionNum, fltWashRatio):
    return (Functions[intIndex](fltWashRatio) - Functions[intIndex-1](fltWashRatio))/(DispersionLit[intIndex] - DispersionLit[intIndex-1]) * (fltDispersionNum - DispersionLit[intIndex-1]) + Functions[intIndex-1](fltWashRatio)

def InterpolateRemoval(intIndex, fltDispersionNum, fltWashRatio):
    return (FractionalRemoval[fltWashRatio][intIndex] - FractionalRemoval[fltWashRatio][intIndex - 1])/(DispersionLit[intIndex] - DispersionLit[intIndex - 1]) *  (fltDispersionNum - DispersionLit[intIndex - 1]) + FractionalRemoval[fltWashRatio][intIndex - 1]

Viscosity = ReturnFluidViscosity(parsed_data["WashFluid"], Temperature)



ConcFinal = Res1.UsedRange.Cells[3, t_Crystallization//delta + 1].Value2
MassFinal = Res1.UsedRange.Cells[5, t_Crystallization//delta + 1].Value2
rho_Susp = (ConcFinal/rho_Cryst + (1-ConcFinal)/rho_MothLiq)**(-1)

SolutionMass = SeedMass + MassMotherLiquor - MassFinal

#Define universal constants
#Universal constants are called from the DWSIM database using the CAPE-OPEN compliant function "GetUniversalConstant"
UniversalConstants = ims1.GetUniversalConstant(["standardaccelerationofgravity", "avogadroconstant", "boltzmannconstant", "molargasconstant"])
R = UniversalConstants[3]
Gravity = UniversalConstants[0]

#Import of CSD from previous process step for the estimation of the porosity of the filter cake
Length = parsed_data["Length"]
CSD = [0] * 30
Width = parsed_data["ClassWidth"]
for i in range(30):
    CSD[i] = float(Res1.UsedRange.Cells[i+8, t_Crystallization//delta + 1].Value2)

def Solubility(fltTemp):
    """
    Returns the solubility in g Sucrose * g Solution**-1 at fltTemp [°C].
    Needs to be adjusted for new substance systems
    """
    return (64.47+0.08222*fltTemp+0.0016169*fltTemp**2-1.558*10**(-6)*fltTemp**3-4.63*10**(-8)*fltTemp**4)/100

def ConvertDistro(lstCSD, lstLen, lstWdt):
    """
    Converts the initial number density distribution to a volume density function.
    The final distribution is not based on the class widths. Instead it only gives the volume percentage per class.
    """
    Sum = 0
    VolDens = [0] * 30
    for i in range(0, len(lstCSD)):
        Sum = Sum + lstCSD[i] * lstWdt[i] * lstLen[i]**3
    for j in range(0, len(lstCSD)):
        VolDens[j] = (lstCSD[j] * lstWdt[j] * lstLen[j]**3)/Sum
    return VolDens

def CalculatePorosity(LstCSD, LstLen, FltXmono, LstWdt):
    """
    Calculates the porosity based on the previous CSD and Lengths. FltXmono refers to
    the porosity of a monodisperse bulk. A value of 0.36 may be assumed here.
    Based on VDI Wärmeatlas 2013, Chapters D6 and M7
    """
    VolumeDistro = ConvertDistro(LstCSD, LstLen, LstWdt)
    QiDi2 = 0
    QiDi = 0
    for i in range(0, len(LstCSD)):
        QiDi2 = QiDi2 + ((VolumeDistro[i])/(LstLen[i]**2))
        QiDi = QiDi + ((VolumeDistro[i])/LstLen[i])
    Zeta = (QiDi2/(QiDi**2) - 1)**0.5
    return FltXmono*(-0.112 * Zeta**3 + 0.017 * Zeta**2 - 0.254 * Zeta+1)

def ViscosityCalc(fltTemp, fltComp):
    """
    Outputs the Viscosity of the system at fltTemp [°C] for fltComp.
    Needs to be adjusted for new substance systems.
    Calculation based on Schneider et al.; formulas taken from Dissertation Pot.
    Validity for fltTemp = 0 - 80°C and fltComp = 0 - 0.86. StdDev = 2.18%
    """
    MolRatio = fltComp/(1 - fltComp) * 18.01528/342.3
    ViscoA = -2.038 - 13.627 * MolRatio - 17.912 * MolRatio**2 + 56.426 * MolRatio**3
    ViscoB = 513.367 + 10740.329 * MolRatio - 16781.21 * MolRatio**2 + 14142.897 * MolRatio**3
    ViscoC = 16.993 + 34.442 * MolRatio + 3915.947 * MolRatio**2 - 6839.469 * MolRatio**3
    eta = 10**(ViscoA + ViscoB/(fltTemp + 273.15) + ViscoC/(fltTemp + 273.15 - 230)) * 10**(-3)
    return eta

def DetermineConstants(fltYInter, fltSlope, fltVisco):
    """
    Determines the required constants for calculation based on experiments.
    The slope and y-Intercept can be determined using VDI Guideline 2762 Part 2.
    """
    beta = DeltaP * Area * fltYInter / fltVisco
    alphaHi = fltSlope * 2 * Area**2 * DeltaP / fltVisco
    return [beta, alphaHi] #beta: Medium resistance [m-1], alphaHi: concentration constant [-] * filter cake res [m-2] 

def EstimateResistance(lstCSD, lstLength, lstWidth, fltPorosity, fltDensity, fltVolFac):
    """
    Estimates the resistance of a given filter cake. The calculation is based on Bourcier et al. (2016).
    For each size class a resistance is determined via the Leva-Equation and added together based on the occurance given by the volumetric distribution function.
    """
    VolDistro = ConvertDistro(lstCSD, lstLength, lstWidth)
    Resistance = 0
    for i in range(0, len(CSD)):
        alpha_0 = 180 * (1 - fltPorosity)/(fltPorosity**3) * 1/(fltVolFac**2 * fltDensity * (lstLength[i] * 10**(-6))**2)
        Resistance = Resistance + alpha_0 * VolDistro[i]
    return Resistance

def EstimateSurfTension(fltConc):
    """
    Estimates the surface tension of a sucrose water solution. Based on Sucrose (Mathlouti, Reiser, 1995) with data from Landt (1934).
    The function was fitted using excel with an R2 = 99.87%. In practice there are deviations possible since data above 65 g/100g Solution are purely extrapolated.
    Input: Concentration [g Sucrose/g Solution]
    Output: Surface tension [N/m]
    """
    return (0.117 * fltConc * 100 + 72.411) * 10**(-3)

def SetTimer(intTime, Variable):
    """
    Used to initialize the deliquoring kinetics. These require information on when deliquoring has started in order to calulate the right runtime.
    This auxiliary function ensures that the starting time for deliquoring is only set on first execution of the loop.
    """
    if not Variable:
        return intTime
    else:
        return Variable

#Calculation of relevant constant parameters
Viscosity = ViscosityCalc(Temperature, ConcFinal)
Constants = DetermineConstants(yIntercept, Slope, Viscosity)
Porosity = CalculatePorosity(CSD, Length, 0.36, Width)

m_SucSusp = Solubility(Temperature) * 100 #Assumption: 100g of Solution enter the filtration
m_WatSusp = 100 - m_SucSusp
CakeHeight = MassFinal / ((1-Porosity) * rho_Cryst * Area) #Basic assumption: The cake is formed in the time used to shift modules
CakeRes = EstimateResistance(CSD, Length, Width, Porosity, rho_Cryst, VolFactor)


#Calculation of parameters for the deliquoring section (Wakeman and Tarleton, Principles of industrial filtration, 2005)
#Threshold pressure:
x_mean = 13.4 * math.sqrt((1 - Porosity)/(CakeRes * rho_Cryst * Porosity**3))
p_threshold = (4.6 * (1 - Porosity) * EstimateSurfTension(ConcFinal))/(Porosity * x_mean)

#Capillary number -> irreducible pressure
CapNum = (Porosity**3 * x_mean**2 * (rho_MothLiq * Gravity * CakeHeight + DeltaP))/((1 - Porosity)**2 * CakeHeight * EstimateSurfTension(ConcFinal))

#Irreducible pressure
S_inf = 0.155 * (1 + 0.031 * CapNum**(-0.49))

#Cake permeability
Perm_av = 1*(CakeRes * rho_Cryst * (1 - Porosity))**(-1)

#Dimensionless pressure
p_star = (1.01325 * 10**5)/p_threshold

#Main loop for the calculation of the filtration process
#Filtration part is based on Stieß, Mechanische Verfahrenstechnik 2, 1994
#Deliquoring part is based on Wakeman, Tarleton, Principles of industrial filtration, 2005
FiltrateVol = 0
LoopDeliqVariable = None
VolDeliqVariable = None
MoistDeliqVariable = None

for t in range(0, t_Process + 1):
    if SolutionMass/rho_Susp - FiltrateVol > Porosity/(1-Porosity) * MassFinal/rho_Cryst:
        Out1.UsedRange.Cells[t+2, 8].Value2 = "Filtration"
        FiltrateVol = (math.sqrt((Constants[0] * Area/(Constants[1]))**2 + 2 * Area**2 * DeltaP * t*(Viscosity * Constants[1])**(-1)) - Constants[0] * Area/Constants[1])
        FiltrateSpeed = DeltaP/math.sqrt((Viscosity*Constants[0])**2 + 2*DeltaP*Viscosity*Constants[1]*t)
        Moisture_Content = ((SolutionMass - (FiltrateVol * rho_Susp))/MassFinal)
        Moisture = (SolutionMass - (FiltrateVol * rho_Susp))/(MassFinal + SolutionMass - (FiltrateVol * rho_Susp))
        Darcy = [FiltrateVol, Moisture_Content]

    else: #Application of deliquoring process from Wakeman and Tarleton, 2005
        #Dimensionless deliquoring time
        StartDeliq = SetTimer(t, LoopDeliqVariable)
        LoopDeliqVariable = StartDeliq

        Out1.UsedRange.Cells[t+2, 8].Value2 = "Deliquoring"
        t_Deliq = (Perm_av * p_threshold)/(Viscosity * Porosity * (1 - S_inf) * CakeHeight**2) * (t - StartDeliq)
        
        #if 0.096 <= t_Deliq * p_star <= 1.915:
        if t_Deliq * p_star <= 1.915:
            S_R = 1*(1 + 1.08 * (t_Deliq * p_star)**0.88)**(-1)
            S_Rminus = S_R
        elif 1.915 < t_Deliq * p_star <= 204:
            S_R = 1*(1 + 1.46 * (t_Deliq * p_star)**0.48)**(-1)
            S_Rminus = S_R
        else:
            Flowsheet.WriteMessage("Deliquoring kinetics could not be calculated")
            S_R = S_Rminus

        S = S_R * (1 - S_inf) + S_inf
        Moisture_Content = (S * Porosity/(1 - Porosity) * rho_Susp/rho_Cryst) #m_Liquid/m_Solid

        MoistDeliqStart = SetTimer(Moisture_Content, MoistDeliqVariable)
        MoistDeliqVariable = MoistDeliqStart
        MoistRange = Darcy[1]/MoistDeliqStart
        Moisture_Content = Moisture_Content * MoistRange
        
        Moisture = Moisture_Content/(1 + Moisture_Content) #m_Liquid/(m_Solid + m_Liquid)

        #Calculation of filtrate amount
        FiltrateVol_t1 = ((SolutionMass - Moisture_Content * MassFinal)/rho_Susp)#**2 / Darcy[0]

        VolDeliqStart = SetTimer(FiltrateVol, VolDeliqVariable)
        VolDeliqVariable = VolDeliqStart
        VolRange = Darcy[0]/VolDeliqStart
        FiltrateVol_t1 = FiltrateVol_t1 * VolRange

        FiltrateSpeed = (FiltrateVol_t1 - FiltrateVol)/Area
        FiltrateVol = FiltrateVol_t1

    Saturation = (SolutionMass/rho_Susp - FiltrateVol)/(Porosity/(1 - Porosity) * MassFinal/rho_Cryst)


    #Write results for each timestep to output Excel file:
    Out1.UsedRange.Cells[t+2, 1].Value2 = t
    Out1.UsedRange.Cells[t+2, 2].Value2 = FiltrateVol * 10**6
    Out1.UsedRange.Cells[t+2, 3].Value2 = FiltrateSpeed
    Out1.UsedRange.Cells[t+2, 4].Value2 = t*(FiltrateVol * 10**6 + 10**(-10))**(-1)
    Out1.UsedRange.Cells[t+2, 5].Value2 = Moisture_Content
    Out1.UsedRange.Cells[t+2, 6].Value2 = Moisture
    Out1.UsedRange.Cells[t+2, 7].Value2 = Saturation

#Export of additional calculated parameters
Out2 = outputsheet.Worksheets[2]
Out2.Name = "Calculated Parameters"
Out2.UsedRange.Cells[1, 1].Value2 = "Suspension density [kg m-3]"
Out2.UsedRange.Cells[1, 2].Value2 = rho_Susp
Out2.UsedRange.Cells[2, 1].Value2 = "Suspension viscosity [Pa s]"
Out2.UsedRange.Cells[2, 2].Value2 = Viscosity
Out2.UsedRange.Cells[3, 1].Value2 = "Cake porosity [-]"
Out2.UsedRange.Cells[3, 2].Value2 = Porosity
Out2.UsedRange.Cells[4, 1].Value2 = "Cake height [m]"
Out2.UsedRange.Cells[4, 2].Value2 = CakeHeight
Out2.UsedRange.Cells[5, 1].Value2 = "Mean diameter [m]"
Out2.UsedRange.Cells[5, 2].Value2 = x_mean
Out2.UsedRange.Cells[6, 1].Value2 = "Threshold pressure [Pa]"
Out2.UsedRange.Cells[6, 2].Value2 = p_threshold
Out2.UsedRange.Cells[7, 1].Value2 = "Capillary number [-]"
Out2.UsedRange.Cells[7, 2].Value2 = CapNum
Out2.UsedRange.Cells[8, 1].Value2 = "Irreducible saturation [-]"
Out2.UsedRange.Cells[8, 2].Value2 = S_inf
Out2.UsedRange.Cells[9, 1].Value2 = "Cake permeability [m2]"
Out2.UsedRange.Cells[9, 2].Value2 = Perm_av
Out2.UsedRange.Cells[10 ,1].Value2 = "Average Cake resistance [m kg-1]"
Out2.UsedRange.Cells[10, 2].Value2 = CakeRes
Out2.UsedRange.Cells[11, 1].Value2 = "Medium Resistance [m-1]"
Out2.UsedRange.Cells[11, 2].Value2 = Constants[0]
Out2.UsedRange.Cells[12, 1].Value2 = "Final Saturation"
Out2.UsedRange.Cells[12, 2].Value2 = Saturation
SaturationInit = Saturation

Out3 = outputsheet.Worksheets[3]
Out3.Name = "WashingResults"

Out3.UsedRange.Cells[1, 1].Value2 = "Washing ratio [-]"
Out3.UsedRange.Cells[1, 2].Value2 = "Phi* [-]"
Out3.UsedRange.Cells[1, 3].Value2 = "Washing time [s]"
Out3.UsedRange.Cells[1, 4].Value2 = "Corrected washing ratio [-]"
Out3.UsedRange.Cells[1, 5].Value2 = "Corrected washing time [s]"
Out3.UsedRange.Cells[1, 5].Value2 = "Corrected process time [s]"
Out3.UsedRange.Cells[1, 6].Value2 = "Fractional removal [-]"
Out3.UsedRange.Cells[1, 7].Value2 = "Remaining fraction [-]"

#Start of Washing Calculation
v_Superficial = DeltaP_Wash * ((Viscosity * (CakeRes * rho_Cryst * (1 - Porosity) * CakeHeight + Constants[0]))**(-1))
v_Pore = v_Superficial * Porosity**(-1)
ReSc = v_Pore * x_mean * DiffCoeff**(-1)

X_0 = CakeHeight * Area * Porosity * Solubility(Temperature) * rho_Susp / MassFinal######################################################



#Determination of the dispersion number for Washing calculation
#Including calculation of D_L/D
if ReSc < 1:
    DisperseCoeff = 1 * (math.sqrt(2))**(-1)
elif ReSc >= 1 and CakeHeight <= 0.1:
    DisperseCoeff = 0.707 + 1.75 * ReSc
else:
    DisperseCoeff = 0.707 + 55.5 * ReSc**0.96
DispersionNum = ReSc * CakeHeight * x_mean**(-1) * DisperseCoeff**(-1)

Correlation = None
for j in range(1, len(DispersionLit)):
    if DispersionNum > DispersionLit[len(DispersionLit)-1] or DispersionNum < DispersionLit[0]:
        Flowsheet.WriteMessage("Dispersion number out of range")
        break
    elif DispersionLit[j] == DispersionNum:
        Correlation = j
        break
    elif DispersionLit[j] > DispersionNum and DispersionLit[j-1] < DispersionNum:
        InterpolationIndex = j
        break 

if not Correlation: 
    for W in range(0, 41):
        Phi_out = Interpolate(InterpolationIndex, DispersionNum, W)
        W_corr = W*10**(-1) + 15.1 * (1 - SaturationInit) * math.exp(-1.56 * Phi_out) - 7.4 * (1 - SaturationInit**2) * math.exp(-1.72 * Phi_out)
        Removal = InterpolateRemoval(InterpolationIndex, DispersionNum, W)
        Out3.UsedRange.Cells[W+2, 1].Value2 = W*10**(-1)
        Out3.UsedRange.Cells[W+2, 2].Value2 = Phi_out
        #Out1.UsedRange.Cells[W+2, 3].Value2 = W*10**(-1) * Porosity * Area * CakeHeight*t_Process**(-1) * 10**6
        WashingTime = W*10**(-1) * Porosity * Area * CakeHeight * FlowRate**(-1) * 10**6 * 60
        CorrWashingTime = W_corr * Porosity * Area * CakeHeight * FlowRate**(-1) * 10**6 * 60
        Out3.UsedRange.Cells[W+2, 3].Value2 = WashingTime + t #WashingTime
        Out3.UsedRange.Cells[W+2, 4].Value2 = W_corr
        #Out1.UsedRange.Cells[W+2, 5].Value2 = W_corr * Porosity * Area * CakeHeight*t_Process**(-1) * 10**6
        Out3.UsedRange.Cells[W+2, 5].Value2 = CorrWashingTime + t #"Corrected" washing time
        Out3.UsedRange.Cells[W+2, 6].Value2 = Removal
        Out3.UsedRange.Cells[W+2, 7].Value2 = 1 - Removal
        Out3.UsedRange.Cells[W+2, 8].Value2 = "Washing"

        WashVol = ((0.35 * Removal + 0.2) + X_0 * MassFinal / ConcFinal) * rho_Susp**(-1) * 10**6
        FiltrateVol = WashVol + FiltrateVol
        Out1.UsedRange.Cells[W + t + 2, 1].Value2 = WashingTime
        Out1.UsedRange.Cells[W + t + 2, 2].Value2 = FiltrateVol
        Out1.UsedRange.Cells[W + t + 2, 5].Value2 = ((SolutionMass - (FiltrateVol * rho_Susp))/MassFinal)
        Out1.UsedRange.Cells[W + t + 2, 6].Value2 = Moisture_Content/(1 + Moisture_Content)



        
else:
    for W in range(0, 41):
        Phi_out = Functions[Correlation](W)
        W_corr = W*10**(-1) + 15.1 * (1 - SaturationInit) * math.exp(-1.56 * Phi_out) - 7.4 * (1 - SaturationInit**2) * math.exp(-1.72 * Phi_out)
        Removal = FractionalRemoval[W][Correlation]
        WashingTime = W*10**(-1) * Porosity * Area * CakeHeight * FlowRate**(-1) * 10**6 * 60
        CorrWashingTime = W_corr * Porosity * Area * CakeHeight * FlowRate**(-1) * 10**6 * 60
        Out3.UsedRange.Cells[W+2, 1].Value2 = W*10**(-1)
        Out3.UsedRange.Cells[W+2, 2].Value2 = Phi_out
        Out3.UsedRange.Cells[W+2, 3].Value2 = WashingTime
        Out3.UsedRange.Cells[W+2, 4].Value2 = W_corr
        Out3.UsedRange.Cells[W+2, 5].Value2 = CorrWashingTime
        Out3.UsedRange.Cells[W+2, 6].Value2 = Removal
        Out3.UsedRange.Cells[W+2, 7].Value2 = 1 - Removal

        WashVol = ((0.35 * Removal + 0.2) + X_0) * rho_Susp**(-1) * 10**6
        FiltrateVol = WashVol + FiltrateVol
        Out1.UsedRange.Cells[W + t + 2, 1].Value2 = WashingTime
        Out1.UsedRange.Cells[W + t + 2, 2].Value2 = FiltrateVol
        Out1.UsedRange.Cells[W + t + 2, 5].Value2 = ((SolutionMass- (FiltrateVol * rho_Susp))/MassFinal)
        Out1.UsedRange.Cells[W + t + 2, 6].Value2 = Moisture_Content/(1 + Moisture_Content)

#Save the output file
Out1.SaveAs(SystemPath + 'Output\\FiltrationOutput.xlsx')
outputsheet.Close(True, SystemPath + 'Output\\FiltrationOutput.xlsx')
ex.Quit()

#Kill all remaining Excel processes to avoid "Ghost" processes that can only be closed using task manager
System.Runtime.InteropServices.Marshal.ReleaseComObject(outputsheet)
System.Runtime.InteropServices.Marshal.ReleaseComObject(datasheet)
System.Runtime.InteropServices.Marshal.ReleaseComObject(ex)

out1 = [0]
out1[0] = oms1
out1[0].Clear()
out1[0].SetProp("totalFlow" ,"Overall", None, "", "mole",moleflow1)
out1[0].SetProp("totalFlow" ,"Overall", None, "", "mass",massflow1)
out1[0].SetProp("temperature" ,"Overall", None, "", "",T1)
out1[0].SetProp("pressure", "Overall", None, "", "",P1)

out2 = [0]
out2[0] = oms1
out2[0].Clear()
out1[0].SetProp("totalFlow" ,"Overall", None, "", "mole",moleflow1)
out1[0].SetProp("totalFlow" ,"Overall", None, "", "mass",massflow1)
out1[0].SetProp("temperature" ,"Overall", None, "", "",T1)
out1[0].SetProp("pressure", "Overall", None, "", "",P1)