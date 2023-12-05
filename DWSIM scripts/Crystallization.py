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

#initialize input stream
feed1 = [0]
P1 = [0]
massflow1 = [0]
molefrac1 = [0]
moleflow1 = [0]
enthalpy1 = [0]
T1 = [0]

#Evaluate input stream
feed1[0] = ims1
P1 = feed1[0].GetProp("pressure", "Overall", None, "", "")
massflow1 = feed1[0].GetProp("totalFlow", "Overall" , None, "", "mass")
moleflow1 = feed1[0].GetProp("totalFlow", "Overall", None, "", "mole")
volflow1 = feed1[0].GetProp("totalFlow", "Overall", None, "", "volume")
enthalpy1 = feed1[0].GetProp("enthalpy", "Overall", None, "Mixture", "mass")
molefrac1 = feed1[0].GetProp("fraction", "Overall", None, "", "mole")
T1 = feed1[0].GetProp("temperature", "Overall", None, "", "")
massfrac1 = feed1[0].GetProp("fraction", "Overall", None, "", "mass")
comp = len(molefrac1) #total number of components/elements


#Reads a .json file with input parameters
#Values are stored as dictionary "parsed_data"
jsonstring = open(SystemPath + 'Input.json').read()
parsed_data = eval(jsonstring)

def ReturnFluidDensity(strComp, fltTemp):
    """
    Returns the fluid density of a component at the given Temperature [K].
    !!!! The component already has to be part of the DWSIM simulation file !!!!
    """
    Comps = [strComp]
    Props = ["densityofliquid"]
    FlDensity = ims1.GetTDependentProperty(Props, fltTemp, Comps, None)
    return FlDensity[0]

#Read Process and Growth Data from Excel
#Stored in Datasheet Workbook 1
T_Start = float(parsed_data["T_Start"]) #°C
T_End = float(parsed_data["T_End"]) #°C
t_Process = int(parsed_data["CycleTime"]) * int(parsed_data["CrystallizationModules"]) #s
G_1 = parsed_data["GrowthConstant1"]
G_2 = parsed_data["GrowthConstant2"]
G_3 = parsed_data["GrowthConstant3"]
#Vol = parsed_data["Volume"]
m_MotherLiquor = parsed_data["MassMothLiq"] #kg
rho_MothLiq = ReturnFluidDensity(parsed_data["MotherLiquor"], T_Start+273.15) #kg m-3
rho_Cryst = parsed_data["CrystalDensity"] #kg m-3
Profile = parsed_data["Profile"]
if Profile == "Linear":
    TempProf = 1
elif Profile == "Progressive":
    TempProf = 2
elif Profile == "Alternating":
    TempProf = 3

A = float(parsed_data["A"])
B = float(parsed_data["B"])
C = float(parsed_data["C"])
D = float(parsed_data["D"])

Ripening = int(parsed_data["RipeningTime"]) #s
Preheating = int(parsed_data["PreheatingTime"]) #s

L_crit = parsed_data["AgglConstant1"] #µm
K_ag = parsed_data["AgglConstant2"]

B_1 = parsed_data["BirthConstant1"]
B_2 = parsed_data["BirthConstant2"]
B_3 = parsed_data["BirthConstant3"]

SeedMass = parsed_data["SeedMass"] #kg

#Assuming that particles can be considered spheres
f_Area = parsed_data["ShapeFactor"] #Standard -> Pi()/6

#timesteps per ODE solving step
delta = parsed_data["Delta"]

#Generate input distributions from input datasheet
#The CSD is based on a RRSB distribution with 30 entries
Length = parsed_data["Length"] #µm
CSD_init = parsed_data["CSD_init"] #Number per size interval


ClassWidth = parsed_data["ClassWidth"] #µm

#Calculation of number of crystals:
#HelpSum = 0
#for i in range(30):
#    HelpSum_i = ClassWidth[i] * CSD_init[i] * (Length[i]*10**(-6))**3
#    HelpSum = HelpSum + HelpSum_i
#Number = SeedMass / (rho_Cryst * f_Area * HelpSum) #siehe Quellen für MA



#Generate new output Excel Sheet
ex.Visible = False
ex.DisplayAlerts = True
workbook = ex.Workbooks.Add()
workbook.Worksheets.Add()
ws1 = workbook.Worksheets[1]
ws1.Name = "Results"
ws2 = workbook.Worksheets[2]
ws2.Name = "Inputs"

#Initialization of Result output
ws1.UsedRange.Cells[1, 1].Value2 = "Time"
ws1.UsedRange.Cells[2, 1].Value2 = "Temperature"
ws1.UsedRange.Cells[3, 1].Value2 = "Concentration"
ws1.UsedRange.Cells[4, 1].Value2 = "Supersaturation"
ws1.UsedRange.Cells[5, 1].Value2 = "Crystal mass"
ws1.UsedRange.Cells[6, 1].Value2 = "Yield"
ws1.UsedRange.Cells[7, 1].Value2 = "Calculated Solubility"
ws1.UsedRange.Cells[8, 1].Value2 = "Growth Rate"
ws1.UsedRange.Cells[9, 1].Value2 = "Crystal Size Distribution"

#Send inputs to Excel for retraceability
ws2.UsedRange.Cells[1, 1].Value2 = "Growth Constant 1"
ws2.UsedRange.Cells[1, 2].Value2 = G_1
ws2.UsedRange.Cells[2, 1].Value2 = "Growth Constant 2"
ws2.UsedRange.Cells[2, 2].Value2 = G_2
ws2.UsedRange.Cells[3, 1].Value2 ="Growth Constant 3"
ws2.UsedRange.Cells[3, 2].Value2 = G_3
ws2.UsedRange.Cells[4, 1].Value2 = "Critical Length"
ws2.Usedrange.Cells[4, 2].Value2 = L_crit
ws2.UsedRange.Cells[5, 1].Value2 = "Agglomeration Parameter"
ws2.UsedRange.Cells[5, 2].Value2 = K_ag
ws2.UsedRange.Cells[6, 1].Value2 = "Birth Parameter 1"
ws2.UsedRange.Cells[6, 2].Value2 = B_1
ws2.UsedRange.Cells[7, 1].Value2 = "Birth Parameter 2"
ws2.UsedRange.Cells[7, 2].Value2 = B_2
ws2.UsedRange.Cells[8, 1].Value2 = "Birth Parameter 3"
ws2.UsedRange.Cells[8, 2].Value2 = B_3

#Set natural constants
#Universal constants are called via the CAPE-OPEN compliant function "GetUniversalConstant"
UniversalConstants = ims1.GetUniversalConstant(["standardaccelerationofgravity", "avogadroconstant", "boltzmannconstant", "molargasconstant"])
R = UniversalConstants[3] #J mol-1 K-1
    
if Profile == "Linear":
    def Temp(t):
        if t < Preheating:
            return T_Start
        elif Preheating <= t < t_Process - Ripening:
            return T_Start - (T_Start - T_End) * (t - Preheating)*(t_Process - (Preheating + Ripening))**(-1)
        else:
            return T_End
elif Profile == "Progressive":
    def Temp(t):
        if t < Preheating:
            return T_Start
        elif Preheating <= t < t_Process - Ripening:
            return T_Start - (T_Start - T_End) * ((t - 600)*(t_Process - (Preheating + Ripening))**(-1))**3
        else:
            return T_End
elif Profile == "Alternating":
    def Temp(t):
        if t < Preheating:
            return T_Start
        elif Preheating <= t < t_Process - Ripening:
            return A * math.cos(B * (t - Preheating)*(t_Process - (Preheating + Ripening))**(-1)) - C * (t - Preheating)*(t_Process - (Preheating + Ripening))**(-1) + D
        else:
            return T_End 

#Define solubility function (for sucrose) and initial concentration
def Solubility(T):
    """
    Outputs the solubility of the given crystal in g g Solution-1. This function is not part of DWSIM and therefore has to be set manually.
    """
    return (64.447 + 0.0822*T + 1.619 * 0.001 * T**2 - 1.558 * 10**(-6) * T**3 - 4.63 * 10**(-8) * T**4)/100 #g g_Solution-1
#Calculation of initial concentration for main loop and calculation of excess crystal mass
Conc = Solubility(T_Start)
Conc_init = Solubility(T_Start)
#m_Water_init = Conc_init * m_MotherLiquor / ((1 + Conc_init) * Conc_init)
m_Water_init = (1 - Conc_init) * m_MotherLiquor
m_0 = Conc * m_MotherLiquor


#Initialize mass balancing and calculate seed mass
def rho_Susp(Conc):
    return (Conc/rho_Cryst + (1-Conc)/rho_MothLiq)**(-1)

#Calculate total volume in the crystallizer
Volume = m_MotherLiquor / rho_Susp(Conc_init) * 10**6 #cm^3

#Conversion of the number per size interval to number density distribution
for i in range(0, len(CSD_init)):
    CSD_init[i] = CSD_init[i] / (ClassWidth[i] * Volume)

#Initialization of the ODE system
dndt = [0]*len(CSD_init)

#Implementation of Agglomeration Kernel -> Faria et al. (2008)
def AggKernel(Input1, Input2):
    return K_ag * 10**(-15) * ((L_crit * Length[Input1] * Length[Input2])**2)/((0.5 * L_crit**3 + Length[Input1]**3)*(0.5 * L_crit**3 + Length[Input2]**3))* G * (Conc/f_Area * rho_Cryst/rho_Susp(Conc))

#Auxiliary function to ensure physical results
def Saturation(T):
    if (Conc/Solubility(T))-1 <= 0:
        return 0
    else:
        return (Conc/Solubility(T))-1
    
#Send initial parameters to Excel
ws1.UsedRange.Cells[1, 2].Value2 = 0
ws1.UsedRange.Cells[2, 2].Value2 = T_Start
ws1.UsedRange.Cells[3, 2].Value2 = Conc_init
ws1.UsedRange.Cells[4, 2].Value2 = 1
ws1.UsedRange.Cells[5, 2].Value2 = SeedMass
ws1.UsedRange.Cells[6, 2].Value2 = 0 * 100 / ((Solubility(T_Start) - Solubility(T_End)) * m_Water_init)
ws1.UsedRange.Cells[7, 2].Value2 = Solubility(T_Start)
ws1.UsedRange.Cells[8, 2].Value2 = 0

CSD_aux = [0] * 30
for d in range(30):
    for k in range(0, len(CSD_init)):
        CSD_aux[k] = CSD_init[k] * ClassWidth[k] * (Length[k]  * 10**(-6))**3
ws1.UsedRange.Cells[9 + d, 2].Value2 = CSD_aux[i] / sum(CSD_aux)

def DispersionFunction(intIn):
#Test für Wachstumsratendispersion
    if intIn <= 5:
        #return 3*math.tanh(5 - intIn) + 0.5
        return 1
    else:
        return 1



#Modelling loop for crystallization
#t = delta
for t in range(delta, t_Process + delta, delta):
    m_Cryst = 0
    T = Temp(t)
    SuperSat = Conc/Solubility(T)
    
    #Growth rate determination:
    if parsed_data["GrowthRate"] == "Exponential":
        G = G_1 * 10**6 * math.exp(-G_2 / (R * (T + 273.15))) * (Saturation(T))**G_3
    elif parsed_data["GrowthRate"] == "BCF":
        if SuperSat - 1 == 0:
            G = 0
        else:
            G = G_1 * (SuperSat - 1)**2 * math.tanh(G_2 / (SuperSat - 1))

    #Definition of the ODE system, according to central Upwind scheme
    #Agglomeration according to Faria et al. (2008)
    def ode(t,n):
        i = 0
        Birth = 0
        Death = 0
        Death2 = 0

        ConcPara = ((Conc - Conc_init) * m_MotherLiquor + SeedMass) / (Volume * 10**(-6))

        for i in range(len(Length)):
            if i == 0:
                dndt_Growth = DispersionFunction(i) * G * (- 0.5 * (n[1] + n[0]))

                
                #No Agglomeration into the class; just death of particles
                for k in range(i, len(Length)):
                    Death2_i = AggKernel(i, k) * n[k]
                    Death2 = Death2 + Death2_i
                dndt_Agglomeration = - n[i] * Death2


            elif i == 1:
                r_i = (n[i+1] - n[i] + 10**(-10))/(n[i] - n[i-1] + 10**(-10))
                Phi_r = max(0, min(2 * r_i, min(1/3 + 2/3 * r_i, 2)))
                dndt_Growth = G * (DispersionFunction(i) * 0.5 * (n[1] + n[0]) - DispersionFunction(i-1) * (n[1] + 0.5 * Phi_r * (n[1] - n[0])))
                dndt_Birth = 0
                #Agglomeration Kernel. Composition of two Death and two birth terms
                #Different since theres just one class below this one
                Birth_i = AggKernel(i-1, i-1) * n[i-1]
                Birth = Birth + Birth_i

                Death_i = 0.5 * AggKernel(i, i-1) * n[i-1]
                Death = Death + Death_i
                for k in range(i, len(Length)):
                    Death2_i = AggKernel(i, k) * n[k]
                    Death2 = Death2 + Death2_i
                Birth2 = AggKernel(i-1, i-1) * n[i-1]**2

                #Addition of all predefined Agglomeration terms
                dndt_Agglomeration = n[i-1] * Birth + 0.5 * Birth2 - n[i] * Death - n[i]*Death2
        
            elif i == (len(Length)-1):
                r_i = (n[i] - n[i-1] + 10**(-10))/(n[i-1] - n[i-2] + 10**(-10))
                Phi_r = max(0, min(2 * r_i, min(1/3 + 2/3 * r_i, 2)))
                dndt_Growth = G * (DispersionFunction(i) * (n[i-1] + 0.5 * Phi_r * (n[i-1] - n[i-2])) - DispersionFunction(i-1) * (n[i] + 0.5 * (n[i] - n[i-1])))
                dndt_Birth = 0

                #Agglomeration Kernel consisting of birth from agglomeration of classes 0 to i-1 (Birth), birth from aggl. of classes i-1 (Birth2)
                #Death with classes 1 to i-1 (Death) and death from classes i to N (Death2)
                for j in range(i-1):
                    Birth_i = 2**(j - i + 1) * AggKernel(i - 1, j) * n[j]
                    Birth = Birth + Birth_i

                    Death_i = 2**(j-i) * AggKernel(i, j) * n[j]
                    Death = Death + Death_i
                Birth2 = AggKernel(i-1, i-1) * n[i-1]**2
                dndt_Agglomeration = n[i-1] * Birth + 0.5 * Birth2 - n[i] * Death

            else:
                r_i = (n[i+1] - n[i] + 10**(-10))/(n[i] - n[i-1] + 10**(-10))
                Phi_r = max(0, min(2 * r_i, min(1/3 + 2/3 * r_i, 2)))
                dndt_Growth = G * (DispersionFunction(i) * (n[i-1] + 0.5 * Phi_r * (n[i-1] - n[i-2])) - DispersionFunction(i) * (n[i] + 0.5 * Phi_r * (n[i] - n[i-1])))
                dndt_Birth = 0

                #Agglomeration Kernel consisting of birth from agglomeration of classes 0 to i-1 (Birth), birth from aggl. of classes i-1 (Birth2)
                #Death with classes 1 to i-1 (Death) and death from classes i to N (Death2)
                for j in range(i-1):
                    Birth_i = 2**(j - i + 1) * AggKernel(i - 1, j) * n[j]
                    Birth = Birth + Birth_i

                    Death_i = 2**(j - i) * AggKernel(i, j) * n[j]
                    Death = Death + Death_i
                for k in range(i, len(Length)):
                    Death2_i = AggKernel(i, k) * n[k]
                    Death2 = Death2 + Death2_i
                Birth2 = AggKernel(i-1, i-1) * n[i-1]**2
                dndt_Agglomeration = n[i-1] * Birth + 0.5 * Birth2 - n[i] * Death - n[i]*Death2
            
            if i ==0:
                if SuperSat - 1 <= 0 or ConcPara <= 0:
                        dndt_Birth = 0
                else:
                    dndt_Birth = B_1 * (SuperSat - 1)**B_2 * ConcPara**B_3
                    #dndt_Birth = B_1 * (SuperSat - 1)**B_2 * ConcPara**B_3
            else:
                dndt_Birth = 0

            #if i <= 5:
            #    dndt_Growth = dndt_Growth * (3 * Length

            dndt[i] = 1/ClassWidth[i] * (dndt_Growth + dndt_Birth + dndt_Agglomeration)
            #dndt[i] = 0
            i+=1
        return Array[float](dndt)
    
    #Initialization of the ODE solver (Runge Kutta 4th order)
    func = OdeFunction(ode)
    init = OdeExplicitRungeKutta45(func,len(Length))
    init.InitializeODEs(func,len(Length))

    #Initialization of initial values
    x = Array[float](CSD_init)
    #Solve ODE
    ans = init.Solve(x, t-delta, 5, t)

    #Update mass balance, concentration and initial value list
    for i in range(0, len(Length)):
        #ws1.UsedRange.Cells[i+8, t//delta+1].Value2 = ans[1, i+1]
        if ans[1, i+1] <= 0:
            ws1.UsedRange.Cells[i+9, t//delta+2].Value2 = 0
            CSD_init[i] = 0
        else:

            CSD_init[i] = ans[1, i+1]


            #Convert the number density distribution used in calculations to a DELTA Q3 distribution for further use
            CSD_aux = [0] * 30
            Cumu = [0] * 30
            for k in range(0, len(CSD_init)):
                CSD_aux[k] = CSD_init[k] * ClassWidth[k] * (Length[k]  * 10**(-6))**3
            ws1.UsedRange.Cells[i+9, t//delta+2].Value2 = CSD_aux[i] / sum(CSD_aux)



        m_Cryst_i = CSD_init[i] * ClassWidth[i] * Volume * rho_Cryst * f_Area * (Length[i] * 10**(-6))**3
        m_Cryst = m_Cryst + m_Cryst_i
    Conc = (m_0 - (m_Cryst - SeedMass)) / (m_0 - (m_Cryst - SeedMass) + m_Water_init)

    #Export relevant data to Excel
    ws1.UsedRange.Cells[1, t//delta+2].Value2 = t
    ws1.UsedRange.Cells[2, t//delta+2].Value2 = T
    ws1.UsedRange.Cells[3, t//delta+2].Value2 = Conc
    ws1.UsedRange.Cells[4, t//delta+2].Value2 = SuperSat
    ws1.UsedRange.Cells[5, t//delta+2].Value2 = m_Cryst
    ws1.UsedRange.Cells[6, t//delta+2].Value2 = (m_Cryst - SeedMass) * 100 / ((Solubility(T_Start)/(1-Solubility(T_Start)) - Solubility(T_End)/(1-Solubility(T_End))) * m_Water_init)
    ws1.UsedRange.Cells[7, t//delta+2].Value2 = Solubility(T)
    ws1.UsedRange.Cells[8, t//delta+2].Value2 = G

#Saving the generated Excel File and killing the Excel process
#If this is not performed, each simulation will open a 'ghost' Excel process that can only be closed using Task Manager
ws1.SaveAs(SystemPath + 'Output\\CrystallizationOutput.xlsx')
workbook.Close(True, SystemPath + 'Output\\CrystallizationOutput.xlsx')
ex.Quit()
System.Runtime.InteropServices.Marshal.ReleaseComObject(workbook)
System.Runtime.InteropServices.Marshal.ReleaseComObject(ex)

#Set properties for output stream(s)
out1 = [0]
out1[0] = oms1
out1[0].Clear()
out1[0].SetProp("totalFlow" ,"Overall", None, "", "mole",moleflow1)
out1[0].SetProp("totalFlow" ,"Overall", None, "", "mass",massflow1)
out1[0].SetProp("temperature" ,"Overall", None, "", "",T1)
out1[0].SetProp("pressure", "Overall", None, "", "",P1)