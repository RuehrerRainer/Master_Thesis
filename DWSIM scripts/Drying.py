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

from DWSIM.Thermodynamics import *
import math, clr, System.GC
from System import Array
from System.IO import File, StreamReader
clr.AddReference('DWSIM.MathOps.DotNumerics')
from DotNumerics.ODE import *

#Initialize sending data to Excel
clr.AddReferenceByName('Microsoft.Office.Interop.Excel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c')
from Microsoft.Office.Interop import Excel
ex = Excel.ApplicationClass()

#Open data from the general input json file
#Important note: Due to incompatibilities using the json-package is not an option
jsonstring = open(SystemPath + "Input.json").read()
parsed_data = eval(jsonstring)

#Import data from the previously read JSON file
t_Process = parsed_data["CycleTime"]
#t_Process = 10
t_Filtration = parsed_data["FiltrationTime"]
t_Crystallization = int(t_Process * parsed_data["CrystallizationModules"])
rho_Cryst = parsed_data["CrystalDensity"]
rho_Gas = parsed_data["GasDensity"]
LoadingGas = 0
AreaFilt = parsed_data["CrystallizerLength"] * parsed_data["CrystallizerWidth"]
DeltaP = parsed_data["DeltaP_Dry"]
GasTemp = parsed_data["T_Dry"]
delta = parsed_data["Delta"]
Zeta = 1 #Channeling parameter
ShapeFactor = parsed_data["ShapeFactor"]
FiltrationTime = parsed_data["FiltrationTime"]
WashingTime = parsed_data["WashingTime"]
DryingTime = t_Process - FiltrationTime - WashingTime

#Initialize taking the input from the previous Unit Ops
outputfilt = ex.Workbooks.Open(SystemPath + 'Output\\FiltrationOutput.xlsx')
FiltOut1 = outputfilt.Worksheets[1]
FiltOut2 = outputfilt.Worksheets[2]

outputcryst = ex.Workbooks.Open(SystemPath + "Output\\CrystallizationOutput.xlsx")
CrystOut1 = outputcryst.Worksheets[1]

#Get Data from previously initialized Worksheet
Porosity = FiltOut2.UsedRange.Cells[3, 2].Value2
rho_sus = FiltOut2.UsedRange.Cells[1, 2].Value2
CakeHeight = FiltOut2.UsedRange.Cells[4, 2].Value2
w_Cake = FiltOut1.UsedRange.Cells[FiltOut1.UsedRange.Row + FiltOut1.UsedRange.Rows.Count - 1 , 5].Value2 #Might change this later
                                                    #Currently it reads the value from the very last column. It might make sense to
                                                    #evaluate the first value at which the maximum is removed instead.
                                                    #Will maybe tackle that later
Saturation = FiltOut2.UsedRange.Cells[12, 2].Value2
MassFinal = CrystOut1.UsedRange.Cells[5, t_Crystallization//delta + 1].Value2


#Generate a new output workbook
outputsheet = ex.Workbooks.Add()
outputsheet.Worksheets.Add()
Out1 = outputsheet.Worksheets[1]
Out1.Name = "Results"
Out2 = outputsheet.Worksheets[2]
Out2.Name = "Calculated values"
Out1.UsedRange.Cells[1, 1].Value2 = "Time [s]"
Out1.UsedRange.Cells[1, 2].Value2 = "Volumetric Drying Rate [kg m-3 s-1]"
Out1.UsedRange.Cells[1, 3].Value2 = "Cake loading [kg liquid kg-1 dry matter]"
Out1.UsedRange.Cells[1, 4].Value2 = "Cake Temperature"#"Initial loading gas [kg liquid kg-1 gas]"
Out1.UsedRange.Cells[1, 5].Value2 = "Cake Saturation"
Out1.UsedRange.Cells[1, 6].Value2 = "Air loading"
Out1.UsedRange.Cells[1, 6+11].Value2 = "Air temperature"

#Initialize input streams
feed1, feed2 = [0], [0]
P1, P2 = [0], [0]
massflow1, massflow2 = [0], [0]
molefrac1, molefrac2 = [0], [0]
moleflow1, moleflow2 = [0], [0]
enthalpy1, enthalpy2 = [0], [0]
T1, T2 = [0], [0]

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

feed2[0] = ims2
P2 = feed2[0].GetProp("pressure", "Overall", None, "", "")
massflow2 = feed2[0].GetProp("totalFlow", "Overall" , None, "", "mass")
moleflow2 = feed2[0].GetProp("totalFlow", "Overall", None, "", "mole")
volflow2 = feed2[0].GetProp("totalFlow", "Overall", None, "", "volume")
enthalpy2 = feed2[0].GetProp("enthalpy", "Overall", None, "Mixture", "mass")
molefrac2 = feed2[0].GetProp("fraction", "Overall", None, "", "mole")
T2 = feed2[0].GetProp("temperature", "Overall", None, "", "")
massfrac2 = feed2[0].GetProp("fraction", "Overall", None, "", "mass")
comp2 = len(molefrac2) #total number of components/elements

def ReturnFluidDensity(strComp, fltTemp):
    """
    Returns the fluid density of a component at the given Temperature [K].
    !!!! The component already has to be part of the DWSIM simulation file !!!!
    """
    Comps = [strComp]
    Props = ["densityofliquid"]
    FlDensity = ims1.GetTDependentProperty(Props, fltTemp, Comps, None)
    return FlDensity[0]



#Get universal constants from the DWSIM database
#Called by the CAPE-OPEN compliant function "GetUniversalConstant"
UniversalConstants = ims1.GetUniversalConstant(["standardaccelerationofgravity", "avogadroconstant", "boltzmannconstant", "molargasconstant"])
Gravity = UniversalConstants[0]
R = UniversalConstants[3]

dictSucrose = [272.06, 277.18, 281.15, 282.3, 286.06, 287.42, 291.18, 292.54, 296.31, 297.66, 301.42, 302.78, 306.54, 307.9, 311.66, 313.01, 316.78, 321.9, 326.8, 331.92, 337.03, 342.15]
HeatCapaSucrose = [46.232, 47.159, 47.880, 48.097, 48.782, 49.023, 49.732, 49.973, 50.682, 50.935, 51.657, 51.921, 52.643, 52.908, 53.653, 53.906, 54.651, 55.674, 56.648, 57.706, 58.753, 59.811]

#Get substance data from the DWSIM database
#Data is only called for substances for which the DWSIM database provides a reasonable basis.
#In this case this involves air and water
#For sucrose, the database has been shown to be unreliant
#Data is called via the CAPE-OPEN compliant functions "GetCompoundConstant" and "GetTDependentProperty"
GasComps = [parsed_data["DryingGas"]]
LiqComps = [parsed_data["MotherLiquor"]]

GasProps = ["viscosityofvapor", "idealgasheatcapacity", "thermalconductivityofvapor"]
ConstProps = ["molecularweight"]

LiqProps = ["heatcapacityofliquid", "heatofvaporization", "vaporpressure"]

GasConst = ims1.GetCompoundConstant(ConstProps, GasComps)
LiqConst = ims1.GetCompoundConstant(ConstProps, LiqComps)
GasData = ims1.GetTDependentProperty(GasProps, GasTemp + 273.15, GasComps, None)
LiqData = ims1.GetTDependentProperty(LiqProps, GasTemp + 273.15, LiqComps, None)

ViscosityGas, HeatCapaGas, ThermCondGas = GasData[0], GasData[1] / GasConst[0], GasData[2]
HeatCapaLiq, HeatVapLiq, VapPresLiq = LiqData[0], LiqData[1] / LiqConst[0], LiqData[2]
PrandtlGas = HeatCapaGas * 10**3 * ViscosityGas / ThermCondGas
#Import last known CSD
CSD = [0] * 30 #Delta Q3 distribution -> Volume/mass per class divided by total volume/mass
Length = parsed_data["Length"]
Width = parsed_data["ClassWidth"]
Volume, Area = 0, 0
for i in range(30):
    CSD[i] = float(CrystOut1.UsedRange.Cells[9 + i, (t_Crystallization//delta)+1].Value2)

    Volume = Volume + CSD[i] * MassFinal / rho_Cryst

    #Volume = Volume + CSD[i] * ShapeFactor * (Length[i] * 10**(-6))**3
    #Area = Area + CSD[i] * Length[i]**2
    #Area = Area + math.pi * CSD[i] * MassFinal / (ShapeFactor * rho_Cryst * (Length[i] * 10**(-6))**3) * (Length[i] * 10**(-6))**2

    Area = Area + (CSD[i] * MassFinal) / (ShapeFactor * Length[i] * 10**(-6) * rho_Cryst) * math.pi
Flowsheet.WriteMessage(str(Area))

d_Sauter = Volume/Area
Flowsheet.WriteMessage(str(d_Sauter))
d_heattrans = math.sqrt(Area / math.pi)
Flowsheet.WriteMessage(str(d_heattrans))

def Effectiveness(fltWCake):
    if fltWCake <= 0.0174:
        return 0
    elif fltWCake >= 0.23287:
        return 1
    else:
        return 18.544 * fltWCake**2 - 0.00562

def Solubility(T):
    """
    Outputs the solubility of Sucrose at a given Temperature in g/g Solution
    """
    return (64.47+0.08222*T+0.0016169*T**2-1.558*10**(-6)*T**3-4.63*10**(-8)*T**4)/100

def CalcCoeff(lstdict, lstvals, fltTemp, strUnit):
    """
    Returns the interpolated heat capacity from a given dictionary of values at the temperature fltTemp [°C]. Only valid in the given temperature interval.
    """
    if strUnit == "K":
        fltTemp = fltTemp + 273.15
    for c in range(len(lstdict)):
        if lstdict[c] == fltTemp:
            return lstvals[c]
        elif lstdict[c] > fltTemp:
            return (lstvals[c+1]-lstvals[c])/(lstdict[c+1] - lstdict[c]) * (fltTemp - lstdict[c]) + lstvals[c]
            break

def HeatCapaSuc(fltTemp):
    """
    Approximates the heat capacity [J/kg K] of a sucrose solution at a given liquid loading and a given Temperature.
    Assumption for this calculation is that the liquid is fully saturated at the given temperature. (Will prolly change later).
    0.3423 is the molar mass of sucrose in kg*mol-1
    """
    return CalcCoeff(dictSucrose, HeatCapaSucrose, fltTemp, "K") * R/0.3423 * Solubility(fltTemp) + (1 - Solubility(fltTemp)) * HeatCapaLiq * 1000

GasVelo = Porosity**3 * DeltaP * 10**5/ (5 * ViscosityGas * (6/(d_Sauter))**2  * (1 - Porosity)**2 * CakeHeight) #Carmen-Kozeny equation, Wakeman-Tarleton
#GasVelo = 2
Flowsheet.WriteMessage(str(GasVelo))
VolFlow = GasVelo * AreaFilt
Out2.UsedRange.Cells[1, 1].Value2 = "Gas velocity [m/s]"
Out2.UsedRange.Cells[1, 2].Value2 = GasVelo
Out2.UsedRange.Cells[2, 1].Value2 = "Volume flow [m3/s]"
Out2.UsedRange.Cells[2, 2].Value2 = VolFlow

#mass transfer constant
H_MassTrans = GasVelo * (math.pi / 6) / (6 * (1 - Porosity) * Zeta) #Tortuosity parameter is currently assumed as \zeta = 1
Out2.UsedRange.Cells[3, 1].Value2 = "Mass transfer coefficient [m/s]"
Out2.UsedRange.Cells[3, 2].Value2 = H_MassTrans

Reynolds_Bulk = GasVelo * d_heattrans * rho_Gas / (Porosity * ViscosityGas)
Flowsheet.WriteMessage(str(Reynolds_Bulk))
Out2.UsedRange.Cells[4, 1].Value2 = "Bulk Reynolds number [-]"
Out2.UsedRange.Cells[4, 2].Value2 = Reynolds_Bulk
Prandtl = PrandtlGas 
Peclet = Reynolds_Bulk * Prandtl
Flowsheet.WriteMessage(str(Peclet))
Out2.UsedRange.Cells[5, 1].Value2 = "Bulk Peclet number [-]"
Out2.UsedRange.Cells[5, 2].Value2 = Peclet

if Peclet >= 500: #Wärmeatlas
    Nusselt_lam = 0.664 * math.sqrt(Reynolds_Bulk) * Prandtl**(1/3)
    Nusselt_turb = (0.037 * Reynolds_Bulk**(0.8) * Prandtl) / (1 + 2.443 * Reynolds_Bulk**(-0.1) * (Prandtl**(2/3) - 1))
    Nusselt_single = 2 + math.sqrt(Nusselt_lam**2 + Nusselt_turb**2)
    Nusselt = Nusselt_single * (1 + 1.5 * (1 - Porosity))
elif 100 <= Peclet < 500: #Martin 1978
    if Reynolds_Bulk < 1000: #Gnielinski 1975
        Factor = 0.664
    else:
        Factor = 0.664 * math.sqrt(1 + ((0.0557 * (Reynolds_Bulk / Porosity)**0.3 * Prandtl**(2/3))/(1 + 2.44 * (Prandtl**(2/3 - 1) * (Reynolds_Bulk / Porosity)**(-0.1))))**2)
    Nusselt_single = 2 + Factor * math.sqrt(Peclet / Porosity)/(Prandtl**(1/6))
    Nusselt = (1 + 1.5 * (1 - Porosity)) * Nusselt_single
elif 1 < Peclet < 100: #Daizo, Mutuyuki, 1967
    Nusselt = (1 + 1.5 * (1 - Porosity)) / (6 * (1 - Porosity) * Zeta) * Peclet

Out2.UsedRange.Cells[6, 1].Value2 = "Bulk collective Nusselt number [-]"
Out2.UsedRange.Cells[6, 2].Value2 = Nusselt

H_HeatTrans = Nusselt * ThermCondGas * 10**(-3)/ d_heattrans
Out2.UsedRange.Cells[7, 1].Value2 = "Heat transfer coefficient [W m-2 K-1]"
Out2.UsedRange.Cells[7, 2].Value2 = H_HeatTrans

#ryingRate = (H_MassTrans * AreaFilt / (GasTemp * UniversalConstants[3] * GasConst[0] * 10**(-3)) * (VapPresLiq - 0)) / (CakeHeight * AreaFilt * (1 - Porosity)) #Assumption: dry air -> partial pressure = 0

DryingRate = (H_MassTrans * AreaFilt / ((GasTemp + 273.15) * R/(GasConst[0] * 10**(-3))) * VapPresLiq) / (CakeHeight * AreaFilt * (1 - Porosity))
LoadingCake = w_Cake
w_air = [0] * 6
dwdt_Air = [0] * 6

#T_air = [GasTemp, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
T_air = [GasTemp, 20, 20, 20, 20, 20]
dTdt_Air = [0] * 6

T_cake = [19]
T_cake_init = T_cake

#main loop
def ODE_CakeLoading(t, w_cake):
    dwdt_Cake = 0 - DryingRate * Effectiveness(w_Cake)/ rho_Cryst
    return Array[float]([dwdt_Cake])

def ODE_AirLoading(t, w_air):
    dwdt_Air[0] = 0
    for o in range(1, 6):
        #if Effectiveness(w_Cake) == 0:
        #    dwdt_Air[o] = 0
        #else:
        dwdt_Air[o] = (DryingRate * Effectiveness(w_Cake) - rho_Gas * GasVelo/Porosity * (w_air[o] - w_air[o-1])/(0.2*CakeHeight))/(rho_Gas*Porosity*(1-Saturation))
    return Array[float](dwdt_Air)

def ODE_AirTemp(t, T_air):
    dTdt_Air[0] = 0
    for p in range(1, 6):
        if T_air[p] < 60:
        #Added the absolute value to the logarithmic temperature difference. Not physically correct, but I had plenty of domain errors in the code prior to that :/
        #dTdt_Air[p] = 1 / (CakeHeight * Area * rho_sus * Porosity * (1 - Saturation) * HeatCapaSuc(GasTemp)) * (-1 * CakeHeight * Area * rho_Gas * GasVelo * HeatCapaGas * 1000 * (T_air[p] - T_air[p-1])/0.1 - H_HeatTrans * Area * (((T_cake[0] - T_air[0]) - (T_cake[0] - T_air[5]))/math.log(abs((T_cake[0] - T_air[0])/(T_cake[0] - T_air[5])))))
            dTdt_Air[p] = (1 / (1 - Porosity) * rho_Gas * HeatCapaGas * Porosity * (1 - Saturation))**(-1) * (- H_HeatTrans * AreaFilt / ((1 - Porosity) * AreaFilt * CakeHeight) * (T_air[0] - T_cake[0]) - DryingRate * Effectiveness(w_Cake) * HeatVapLiq - 1/(1 - Porosity) * rho_Gas * HeatCapaGas * GasVelo * (T_air[p] - T_air[p-1])/(0.2*CakeHeight))
        else:
            dTdt_Air[p] = 0

    return Array[float](dTdt_Air)

def ODE_CakeTemp(t, T_cake):
    #if T_cake[0] < 60:
    #    dTdt_Cake = -1*(1 / (1/(1 - Porosity) * rho_Cryst * CalcCoeff(dictSucrose,HeatCapaSucrose,GasTemp,"K")*UniversalConstants[3]/0.3423 *(1-Porosity) + rho_sus*HeatCapaSuc(GasTemp)*Porosity*Saturation)*((H_HeatTrans*Area)/((1-Porosity)*Area*CakeHeight)*(((T_cake[0] - T_air[0]) - (T_cake[0] - T_air[5]))/math.log(abs((T_cake[0] - T_air[0])/(T_cake[0] - T_air[5])))) - DryingRate * Effectiveness(w_Cake) * HeatVapLiq/1000))
    #else:
    #    dTdt_Cake = 0


    dTdt_Cake = (1/(1-Porosity) * rho_Cryst * CalcCoeff(dictSucrose,HeatCapaSucrose,GasTemp,"K") * (1 - Porosity) + rho_sus * HeatCapaSuc(GasTemp) * Porosity * Saturation)**(-1) * ((-1) * H_HeatTrans * Area / ((1-Porosity)*AreaFilt*CakeHeight) * (T_cake[0] - T_air[0]) - DryingRate * Effectiveness(w_Cake) * HeatVapLiq/1000)
    return Array[float]([dTdt_Cake])


DeltaPDE = 10
for t in range(DeltaPDE, int(DryingTime + DeltaPDE), DeltaPDE):
    
    func = OdeFunction(ODE_CakeLoading)
    init = OdeExplicitRungeKutta45(func, 1)
    init.InitializeODEs(func, 1)
    ans = init.Solve(Array[float]([LoadingCake]), t-DeltaPDE, DeltaPDE, t)
    
    if t < DryingTime//3:
        func2 = OdeFunction(ODE_AirLoading)
        init2 = OdeExplicitRungeKutta45(func2, 6)
        init2.InitializeODEs(func2, 6)
        ans2 = init2.Solve(Array[float](w_air), t-DeltaPDE, DeltaPDE, t)

    func3 = OdeFunction(ODE_AirTemp)
    init3 = OdeExplicitRungeKutta45(func3, 6)
    init3.InitializeODEs(func3, 6)
    ans3 = init3.Solve(Array[float](T_air), t-DeltaPDE, DeltaPDE, t)

    func4 = OdeFunction(ODE_CakeTemp)
    init4 = OdeExplicitRungeKutta45(func4, 1)
    init4.InitializeODEs(func4, 1)
    ans4 = init4.Solve(Array[float](T_cake), t-DeltaPDE, DeltaPDE, t)

    Out1.UsedRange.Cells[t//DeltaPDE+1, 1].Value2 = t
    Out1.UsedRange.Cells[t//DeltaPDE+1, 2].Value2 = DryingRate * Effectiveness(w_Cake)
    Out1.UsedRange.Cells[t//DeltaPDE+1, 3].Value2  = ans[1, 1]
    Out1.UsedRange.Cells[t//DeltaPDE+1, 4].Value2 = ans4[1, 1]
    LoadingCake = ans[1, 1]
    w_Cake = LoadingCake
    T_cake[0] = float(ans4[1, 1])
    Saturation = LoadingCake * rho_sus / rho_Cryst * (1 - Porosity)/Porosity
    Out1.UsedRange.Cells[t//DeltaPDE+1, 5].Value2  = Saturation
    for j in range(0, len(dwdt_Air)):
        if t < DryingTime//3:
            Out1.UsedRange.Cells[t//DeltaPDE+1, 6 + j].Value2 = ans2[1, j+1]
            w_air[j] = ans2[1, j+1]
        if ans3[1, j+1] <= GasTemp:
            Out1.UsedRange.Cells[t//DeltaPDE+1, 6 +len(dwdt_Air) + j] = ans3[1, j+1]
            T_air[j] = ans3[1, j+1]
        else:
            Out1.UsedRange.Cells[t//DeltaPDE+1, 6 +len(dwdt_Air) + j] = T_air[j] = GasTemp

Out1.SaveAs(SystemPath + 'Output\\DryingOutput.xlsx')
outputsheet.Close(True, SystemPath + 'Output\\DryingOutput.xlsx')
ex.Quit()
System.Runtime.InteropServices.Marshal.ReleaseComObject(outputsheet)
System.Runtime.InteropServices.Marshal.ReleaseComObject(outputcryst)
System.Runtime.InteropServices.Marshal.ReleaseComObject(outputfilt)
System.Runtime.InteropServices.Marshal.ReleaseComObject(ex)