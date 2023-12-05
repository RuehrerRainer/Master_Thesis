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
    Comps = strComp
    Props = ["viscosityofliquid"]
    FlVisco = ims1.GetTDependentProperty(Props, fltTemp, Comps, None)
    return FlVisco[0]

#Generate a new output Excel sheet
outputsheet = ex.Workbooks.Add()
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
t_Crystallization = int(parsed_data["CycleTime"] * parsed_data["CrystallizationModules"])
rho_Cryst = float(parsed_data["CrystalDensity"])
Area = parsed_data["CrystallizerLength"] * parsed_data["CrystallizerWidth"]
VolFactor = parsed_data["ShapeFactor"]
DeltaP = parsed_data["DeltaP_Filt"] * 10**5
yIntercept = parsed_data["yIntercept"]
Slope = parsed_data["Slope"]
Temperature = parsed_data["T_Filt"]
rho_MothLiq = ReturnFluidDensity(parsed_data["MotherLiquor"], Temperature)
delta = parsed_data["Delta"]

#DiffCoeff = parsed_data["DiffusionCoefficient"] #%%%%%%%%%%
#DeltaP_Wash = parsed_data["DeltaP_Wash"] * 10**5

SeedMass = parsed_data["SeedMass"]
MassMotherLiquor = parsed_data["MassMothLiq"]

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
    CSD[i] = float(Res1.UsedRange.Cells[i+9, t_Crystallization//delta + 1].Value2)

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
        VolDens[i] = lstCSD[i] / lstWdt[i]
    #for i in range(0, len(lstCSD)):
    #    Sum = Sum + lstCSD[i] * lstWdt[i] * lstLen[i]**3
    #for j in range(0, len(lstCSD)):
    #    VolDens[j] = (lstCSD[j] * lstWdt[j] * lstLen[j]**3)/Sum
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
if parsed_data["Confidence"] == "Data":
    Constants = DetermineConstants(yIntercept, Slope, Viscosity)
Porosity = CalculatePorosity(CSD, Length, 0.36, Width)

#Calculation in the case that constants from experiments are partially unknown

if parsed_data["Confidence"] == "Est":
#Read known value:
    KnownX = parsed_data["KnownX"]
    KnownY = parsed_data["KnownY"]

    #Calculate potential pairs of values [Y-Intercept, Slope]
    ValuePair_1 = [KnownY - 1, 1 / (KnownX - 0)] #Highest possible Y-Intercept
    ValuePair_2 = [1, (KnownY - 1) / (KnownX - 0)] #Steepest curve possible

    YIntercept3 = (ValuePair_1[0] + ValuePair_2[0]) / 2
    ValuePair_3 = [YIntercept3, (KnownY - YIntercept3) / (KnownX - 0)] #Average of the first 2 points

    YIntercept4 = (ValuePair_1[0] + YIntercept3)/2
    ValuePair_4 = [YIntercept4, (KnownY - YIntercept4) / (KnownX - 0)] #Average of average and highest y-Intercept

    YIntercept5 = (YIntercept3 + ValuePair_2[0]) / 2
    ValuePair_5 = [YIntercept5, (KnownY - YIntercept5) / (KnownX - 0)] #Average of average and highest y-Intercept

    Constants_1 = DetermineConstants(ValuePair_1[0], ValuePair_1[1], Viscosity)
    Constants_2 = DetermineConstants(ValuePair_2[0], ValuePair_2[1], Viscosity)
    Constants_4 = DetermineConstants(ValuePair_4[0], ValuePair_4[1], Viscosity)
    Constants_5 = DetermineConstants(ValuePair_5[0], ValuePair_5[1], Viscosity)

    Constants = DetermineConstants(ValuePair_3[0], ValuePair_3[1], Viscosity)


m_SucSusp = Solubility(Temperature) * 100 #Assumption: 100g of Solution enter the filtration
m_WatSusp = 100 - m_SucSusp
CakeHeight = MassFinal / ((1-Porosity) * rho_Cryst * Area) #Basic assumption: The cake is formed in the time used to shift modules

#Calculation of parameters for the deliquoring section (Wakeman and Tarleton, Principles of industrial filtration, 2005)
#Threshold pressure:
x_mean = 13.4 * math.sqrt((1 - Porosity)/(EstimateResistance(CSD, Length, Width, Porosity, rho_Cryst, VolFactor) * rho_Cryst * Porosity**3))
p_threshold = (4.6 * (1 - Porosity) * EstimateSurfTension(ConcFinal))/(Porosity * x_mean)

#Capillary number -> irreducible pressure
CapNum = (Porosity**3 * x_mean**2 * (rho_MothLiq * Gravity * CakeHeight + DeltaP))/((1 - Porosity)**2 * CakeHeight * EstimateSurfTension(ConcFinal))

#Irreducible pressure
S_inf = 0.155 * (1 + 0.031 * CapNum**(-0.49))

#Cake permeability
Perm_av = 1*(EstimateResistance(CSD,Length,Width,Porosity,rho_Cryst,VolFactor) * rho_Cryst * (1 - Porosity))**(-1)

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
        FiltrateSpeed = DeltaP/math.sqrt((Viscosity * Constants[0])**2 + 2 * DeltaP * Viscosity * Constants[1] * t)
        Moisture_Content = ((SolutionMass - (FiltrateVol * rho_Susp))/MassFinal)
        Moisture = (SolutionMass - (FiltrateVol * rho_Susp))/(MassFinal + SolutionMass - (FiltrateVol * rho_Susp))
        Darcy = [FiltrateVol, Moisture_Content]

        #Calculation in the case that filtration parameters are unknown
        if parsed_data["Confidence"] == "Est":
            FiltrateVol_1 = (math.sqrt((Constants_1[0] * Area/(Constants_1[1]))**2 + 2 * Area**2 * DeltaP * t*(Viscosity * Constants_1[1])**(-1)) - Constants_1[0] * Area/Constants_1[1])
            FiltrateVol_2 = (math.sqrt((Constants_2[0] * Area/(Constants_2[1]))**2 + 2 * Area**2 * DeltaP * t*(Viscosity * Constants_2[1])**(-1)) - Constants_2[0] * Area/Constants_2[1])
            FiltrateVol_4 = (math.sqrt((Constants_4[0] * Area/(Constants_4[1]))**2 + 2 * Area**2 * DeltaP * t*(Viscosity * Constants_4[1])**(-1)) - Constants_4[0] * Area/Constants_4[1])
            FiltrateVol_5 = (math.sqrt((Constants_5[0] * Area/(Constants_5[1]))**2 + 2 * Area**2 * DeltaP * t*(Viscosity * Constants_5[1])**(-1)) - Constants_5[0] * Area/Constants_5[1])
            Out1.UsedRange.Cells[t+2, 9].Value2 = FiltrateVol_1 * 10**6
            Out1.UsedRange.Cells[t+2, 10].Value2 = FiltrateVol_2 * 10**6
            Out1.UsedRange.Cells[t+2, 11].Value2 = FiltrateVol_4 * 10**6
            Out1.UsedRange.Cells[t+2, 12].Value2 = FiltrateVol_5 * 10**6
            Moisture_Content_1 = ((SolutionMass - (FiltrateVol_1 * rho_Susp))/MassFinal)
            Moisture_Content_2 = ((SolutionMass - (FiltrateVol_2 * rho_Susp))/MassFinal)
            Moisture_Content_4 = ((SolutionMass - (FiltrateVol_4 * rho_Susp))/MassFinal)
            Moisture_Content_5 = ((SolutionMass - (FiltrateVol_5 * rho_Susp))/MassFinal)
            Out1.UsedRange.Cells[t+2, 13].Value2 = Moisture_Content_1
            Out1.UsedRange.Cells[t+2, 14].Value2 = Moisture_Content_2
            Out1.UsedRange.Cells[t+2, 15].Value2 = Moisture_Content_4
            Out1.UsedRange.Cells[t+2, 16].Value2 = Moisture_Content_5


    else: #Application of deliquoring process from Wakeman and Tarleton, 2005
        #Dimensionless deliquoring time
        StartDeliq = SetTimer(t, LoopDeliqVariable)
        LoopDeliqVariable = StartDeliq

        Out1.UsedRange.Cells[t+2, 8].Value2 = "Deliquoring"
        t_Deliq = (Perm_av * p_threshold)/(Viscosity * Porosity * (1 - S_inf) * CakeHeight**2) * (t - StartDeliq)
        
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
Out2.UsedRange.Cells[10, 2].Value2 = EstimateResistance(CSD, Length, Width, Porosity, rho_Cryst, VolFactor)
Out2.UsedRange.Cells[11, 1].Value2 = "Medium Resistance [m-1]"
Out2.UsedRange.Cells[11, 2].Value2 = Constants[0]
Out2.UsedRange.Cells[12, 1].Value2 = "Final Saturation"
Out2.UsedRange.Cells[12, 2].Value2 = Saturation

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