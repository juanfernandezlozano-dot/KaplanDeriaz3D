# KaplanDeriaz3D Hydro Turbine Designer

KaplanDeriaz3D Hydro Turbine Designer is an engineering software package developed in both MATLAB and Python for the parametric design, geometric reconstruction, and hydrodynamic analysis of axial-flow (Kaplan) and diagonal-flow (Deriaz) hydraulic turbines.

## Features

* Parametric design of Kaplan and Deriaz turbine runners.
* Automated blade geometry reconstruction from hydraulic design parameters.
* High-quality 3D visualization and surface rendering of turbine blades.
* Hydrodynamic calculations including rotational speed, flow velocity triangles, hydraulic efficiency, volumetric efficiency, solidity, and chord distributions.
* Multiple interpolation methods (Cubic, Spline, and Linear) for smooth blade generation.
* Export of generated blade geometries to STL format for CAD, CAM, CFD, and 3D printing applications.
* Available in both MATLAB and Python implementations.

This project was developed as part of a Master's Thesis (TFM) in Industrial Engineering at Universidad Carlos III de Madrid (UC3M).

KaplanDeriaz3D.mlappinstall and KaplanDeriaz3D1_2.m correspond to the MATLAB application installer and source code, respectively, for the KaplanDeriaz3D software. KaplanDeriaz3D.exe is a standalone executable version that can be run without requiring MATLAB or a MATLAB license. kaplan_deriaz_Python_app.py is the Python implementation (port) of the same application.

Kaplan Hydro Turbine Design (MATLAB App):

<img width="1460" height="971" alt="image" src="https://github.com/user-attachments/assets/45cbdffd-588a-43ad-8751-a3bb15e73bef" />

Interactive 3D visualization of an axial Kaplan runner generated within MATLAB App Designer, displaying optimized blade curvature and hydrodynamics.

Deriaz Hydro Turbine Design (MATLAB App):

<img width="1468" height="971" alt="image" src="https://github.com/user-attachments/assets/f006242b-062d-4368-9f07-4404847462a6" />

Full 3D rendering of a diagonal/spherical Deriaz turbine runner with spherical boundary envelopes and multi-blade assembly.

Kaplan Hydro Turbine Design (Python PyQt5):

<img width="1218" height="832" alt="image" src="https://github.com/user-attachments/assets/56a0492b-1f90-4755-828c-ff7e7dc5cce9" />

Code built with PyQt5 and Matplotlib, displaying the axial blade geometry and real-time performance metrics.

Deriaz Hydro Turbine Design (Python PyQt5):

<img width="1216" height="825" alt="image" src="https://github.com/user-attachments/assets/8b3d3eb7-a6d7-4b7f-a68b-0bc2737ba2a8" />

3D surface reconstruction of a Deriaz runner in Python, featuring spherical radius mesh computation and binary STL export capability.
