# Master_Thesis
This repository contains the finalized code used in the Master Thesis. Including the scripts used in DWSIM as well as the Program and all underlying scripts.

# Getting Started
Using the scripts requires an installation of DWSIM (https://dwsim.org/index.php/download/) and an installation of Python. For all simulations in the thesis, Python Version 3.9.16 and DWSIM version 8.5.1 were used.
The Python environment can be setup using the req.txt file by running the following command using conda:

$ conda create -n <environment-name> --file req.txt

# Repository Structure
- Supplementaries:
    Contains additional "nice-to-have" files. Includes gifs of both optimization algorithms and the template files for entering custom Crystal Size Distributions and for employing the fitting algorithm
- DWSIM scripts:
    Contains the pure Python versions of scripts used in DWSIM. Including scripts for crystallization, filtration (includes filtration and deliquoring kinetics), washing (includes filtration, deliquoring and washing kinetics) and drying
- Program:
    Contains all files concerning the GUI developed in this master thesis. The GUI can be started by executing "CrystallizerProgram2.py". If only the result window is to be opened, "ResultWindow.py" can be executed (Please keep in mind to activate line 41 while commenting out lines 36-39!).
    - Graphics includes all images used in the program (mainly consisting of formulae)
    - Windows includes any additional windows (Help dialogs)
    - DWSIM includes:
        - The scripts responsible for starting simulations
        - The input .json file
        - The fitting algorithms
        - The DWSIM simulation files
        - The folder for the output of log files (from crystallization fitting) and Excel files

# GUI structure
![ModelStructure](https://github.com/RuehrerRainer/Master_Thesis/assets/103190984/1a9cfaa5-190a-43f4-8635-30583460a00d)


