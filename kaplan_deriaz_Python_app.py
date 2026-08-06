import sys
import struct
import numpy as np

import matplotlib
# Use the Qt5Agg backend for better integration with PyQt5
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QLabel, QComboBox, QDoubleSpinBox,
    QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QHeaderView, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


def evaluate_interpolation(interp_type, t):
    """
    Calculates the Beta angle distribution law according to the chosen scheme.
    """
    if interp_type == 'Cubic (Standard)':
        return 3 * (t**2) - 2 * (t**3)
    elif interp_type == 'Linear (Uniform)':
        return t
    elif interp_type == 'Cosine (Smooth)':
        return 0.5 * (1 - np.cos(np.pi * t))
    elif interp_type == 'Inlet Loaded (Attack)':
        return 1 - (1 - t)**2
    elif interp_type == 'Outlet Loaded (Discharge)':
        return t**2
    else:
        return 3 * (t**2) - 2 * (t**3)


def export_surface_stl_binary(filename, X, Y, Z):
    """
    Exports the blade as an open SURFACE (zero thickness) to a binary STL file.
    """
    Rows, Cols = X.shape 
    
    verts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    faces = []
    
    # Generate triangle faces from the grid
    for r in range(Rows - 1):
        for c in range(Cols - 1):
            idx1 = r * Cols + c
            idx2 = r * Cols + (c + 1)
            idx3 = (r + 1) * Cols + (c + 1)
            idx4 = (r + 1) * Cols + c
            
            faces.append([idx1, idx2, idx3])
            faces.append([idx1, idx3, idx4])

    faces = np.array(faces, dtype=np.uint32)

    # Write binary STL format
    with open(filename, 'wb') as f:
        f.write(b'\x00' * 80) # 80-byte header
        f.write(struct.pack('<I', len(faces))) # Number of triangles

        for tri in faces:
            p1, p2, p3 = verts[tri[0]], verts[tri[1]], verts[tri[2]]
            
            v1 = p2 - p1
            v2 = p3 - p1
            fnorm = np.cross(v1, v2)
            fnorm_len = np.linalg.norm(fnorm)
            # Normalize the normal vector
            fnorm = fnorm / fnorm_len if fnorm_len > 0 else np.array([0.0, 0.0, 0.0])

            # Write normal vector and vertices
            f.write(struct.pack(
                '<ffffffffffffH',
                fnorm[0], fnorm[1], fnorm[2],
                p1[0], p1[1], p1[2],
                p2[0], p2[1], p2[2],
                p3[0], p3[1], p3[2],
                0 # Attribute byte count
            ))


class KaplanDeriaz3DApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Kaplan & Deriaz Hydro Turbine Designer v1.6")
        self.resize(1240, 850)

        # Store blade coordinates for STL export
        self.X_blade = None
        self.Y_blade = None
        self.Z_blade = None
        self.is_computed = False

        self.init_ui()
        self.on_turbine_type_change()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # =====================================================================
        # LEFT PANEL: DESIGN PARAMETERS
        # =====================================================================
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(490)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(6)

        # Basic Parameters Group
        param_group = QGroupBox(" Design Parameters ")
        grid = QGridLayout(param_group)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        normal_font = QFont("Segoe UI", 9, QFont.Normal)

        row = 0

        # Turbine Type
        tt_type = (
            "Runner Kinematics:\n"
            "• Kaplan: Pure axial flow (ideal for low heads and large flow rates).\n"
            "• Deriaz: Diagonal/spherical flow (ideal for medium heads and high operational flexibility)."
        )
        lbl_type = QLabel("Turbine Type:")
        lbl_type.setFont(normal_font)
        lbl_type.setToolTip(tt_type)
        grid.addWidget(lbl_type, row, 0)
        
        self.combo_type = QComboBox()
        self.combo_type.addItems(['Kaplan (Axial)', 'Deriaz (Diagonal)'])
        self.combo_type.setToolTip(tt_type)
        self.combo_type.currentIndexChanged.connect(self.on_turbine_type_change)
        grid.addWidget(self.combo_type, row, 1)

        # RPM
        row += 1
        tt_rpm = (
            "Runner rotational speed in RPM (n).\n"
            "• Higher speeds reduce the required runner diameter but increase the risk of cavitation due to lower local static pressures on the suction side (extrados)."
        )
        lbl_rpm = QLabel("Rotational Speed (RPM):")
        lbl_rpm.setFont(normal_font)
        lbl_rpm.setToolTip(tt_rpm)
        grid.addWidget(lbl_rpm, row, 0)
        
        self.spin_rpm = QDoubleSpinBox()
        self.spin_rpm.setRange(1, 10000)
        self.spin_rpm.setValue(450)
        self.spin_rpm.setToolTip(tt_rpm)
        grid.addWidget(self.spin_rpm, row, 1)

        # Rotation Direction
        row += 1
        tt_rot = (
            "Runner rotation direction viewed from above (+Z axis looking down):\n"
            "• Counter-Clockwise (CCW): Hydroelectric standard convention.\n"
            "• Clockwise (CW): Adapted for specific mechanical drive couplings."
        )
        lbl_rot = QLabel("Rotation Direction:")
        lbl_rot.setFont(normal_font)
        lbl_rot.setToolTip(tt_rot)
        grid.addWidget(lbl_rot, row, 0)
        
        self.combo_rot = QComboBox()
        self.combo_rot.addItems(['Counter-Clockwise (Standard)', 'Clockwise'])
        self.combo_rot.setToolTip(tt_rot)
        grid.addWidget(self.combo_rot, row, 1)

        # Flow Rate Q0
        row += 1
        tt_q0 = (
            "Nominal design volumetric flow rate (m³/s).\n"
            "Determines the fluid meridional velocity (Vz or Vm) and the cross-sectional passage area required to prevent flow choking."
        )
        lbl_q0 = QLabel("Flow Rate Q0 (m³/s):")
        lbl_q0.setFont(normal_font)
        lbl_q0.setToolTip(tt_q0)
        grid.addWidget(lbl_q0, row, 0)
        
        self.spin_q0 = QDoubleSpinBox()
        self.spin_q0.setRange(0.01, 10000)
        self.spin_q0.setValue(12)
        self.spin_q0.setToolTip(tt_q0)
        grid.addWidget(self.spin_q0, row, 1)

        # Net Head Hn
        row += 1
        tt_hn = (
            "Net hydraulic head available at the installation (m).\n"
            "Sets the total available specific energy (g*Hn) that the blades must convert into shaft mechanical torque."
        )
        lbl_hn = QLabel("Net Head Hn (m):")
        lbl_hn.setFont(normal_font)
        lbl_hn.setToolTip(tt_hn)
        grid.addWidget(lbl_hn, row, 0)
        
        self.spin_hn = QDoubleSpinBox()
        self.spin_hn.setRange(0.1, 2000)
        self.spin_hn.setValue(15)
        self.spin_hn.setToolTip(tt_hn)
        grid.addWidget(self.spin_hn, row, 1)

        # Gravity g
        row += 1
        tt_g = (
            "Local acceleration of gravity (m/s²).\n"
            "Standard value: 9.81 m/s²."
        )
        lbl_g = QLabel("Gravity g (m/s²):")
        lbl_g.setFont(normal_font)
        lbl_g.setToolTip(tt_g)
        grid.addWidget(lbl_g, row, 0)
        
        self.spin_g = QDoubleSpinBox()
        self.spin_g.setRange(1.0, 20.0)
        self.spin_g.setValue(9.81)
        self.spin_g.setToolTip(tt_g)
        grid.addWidget(self.spin_g, row, 1)

        # Hydraulic Efficiency
        row += 1
        tt_etah = (
            "Hydraulic efficiency (eta_h = H_inf / Hn).\n"
            "Accounts for fluid energy losses due to viscous friction and boundary layer separation along the blade profile."
        )
        lbl_etah = QLabel("Hydraulic Eff. (eta_h):")
        lbl_etah.setFont(normal_font)
        lbl_etah.setToolTip(tt_etah)
        grid.addWidget(lbl_etah, row, 0)
        
        self.spin_eta_h = QDoubleSpinBox()
        self.spin_eta_h.setRange(0.1, 1.0)
        self.spin_eta_h.setSingleStep(0.01)
        self.spin_eta_h.setValue(0.90)
        self.spin_eta_h.setToolTip(tt_etah)
        grid.addWidget(self.spin_eta_h, row, 1)

        # Volumetric Efficiency
        row += 1
        tt_etav = (
            "Volumetric efficiency (eta_v = Q_real / Q0).\n"
            "Accounts for internal flow leakage losses through the tip clearance gap between the blade tip and the outer discharge ring."
        )
        lbl_etav = QLabel("Volumetric Eff. (eta_v):")
        lbl_etav.setFont(normal_font)
        lbl_etav.setToolTip(tt_etav)
        grid.addWidget(lbl_etav, row, 0)
        
        self.spin_eta_v = QDoubleSpinBox()
        self.spin_eta_v.setRange(0.1, 1.0)
        self.spin_eta_v.setSingleStep(0.01)
        self.spin_eta_v.setValue(0.96)
        self.spin_eta_v.setToolTip(tt_etav)
        grid.addWidget(self.spin_eta_v, row, 1)

        # Mechanical Efficiency
        row += 1
        tt_etam = (
            "Mechanical efficiency (eta_m).\n"
            "Accounts for power losses caused by shaft bearing friction, dynamic shaft seals, and hub disk friction."
        )
        lbl_etam = QLabel("Mechanical Eff. (eta_m):")
        lbl_etam.setFont(normal_font)
        lbl_etam.setToolTip(tt_etam)
        grid.addWidget(lbl_etam, row, 0)
        
        self.spin_eta_m = QDoubleSpinBox()
        self.spin_eta_m.setRange(0.1, 1.0)
        self.spin_eta_m.setSingleStep(0.01)
        self.spin_eta_m.setValue(0.98)
        self.spin_eta_m.setToolTip(tt_etam)
        grid.addWidget(self.spin_eta_m, row, 1)

        # Solidity
        row += 1
        tt_sigma = (
            "Solidity Ratio (sigma = Chord / Pitch):\n"
            "• Controls the number of runner blades (Z):\n"
            "  - High Solidity (sigma > 1.4): Increases blade count (e.g., 6 to 8 blades). Reduces hydraulic load per blade and mitigates cavitation, but increases skin friction losses.\n"
            "  - Low Solidity (sigma < 1.0): Reduces blade count (e.g., 3 to 4 blades). Minimizes runner mass and surface friction, but requires longer chord lengths or higher lift coefficients."
        )
        lbl_sigma = QLabel("Solidity (sigma):")
        lbl_sigma.setFont(normal_font)
        lbl_sigma.setToolTip(tt_sigma)
        grid.addWidget(lbl_sigma, row, 0)
        
        self.spin_sigma = QDoubleSpinBox()
        self.spin_sigma.setRange(0.5, 3.0)
        self.spin_sigma.setSingleStep(0.05)
        self.spin_sigma.setValue(1.25)
        self.spin_sigma.setToolTip(tt_sigma)
        grid.addWidget(self.spin_sigma, row, 1)

        # Interpolation Scheme (Beta Angle)
        row += 1
        tt_interp = (
            "Beta Angle Distribution Law (Pressure distribution along chord):\n"
            "• Cubic (Standard): Smooth distribution. Peak hydrodynamic pressure located around 30-40% of chord length.\n"
            "• Linear (Uniform): Constant angle gradient. Pressure is distributed uniformly along the profile.\n"
            "• Cosine (Smooth): Ultra-smooth transition near leading/trailing edges. Minimizes localized cavitation spikes.\n"
            "• Inlet Loaded: Steeper deflection at the entry. MAXIMUM PRESSURE ZONE AT LEADING EDGE (ideal for clean, shock-free flow entry).\n"
            "• Outlet Loaded: Steeper curvature towards the exit. MAXIMUM PRESSURE ZONE AT TRAILING EDGE (maximizes energy transfer before discharge)."
        )
        lbl_interp = QLabel("Interpolation Scheme:")
        lbl_interp.setFont(normal_font)
        lbl_interp.setToolTip(tt_interp)
        grid.addWidget(lbl_interp, row, 0)
        
        self.combo_interp = QComboBox()
        self.combo_interp.addItems([
            'Cubic (Standard)', 'Linear (Uniform)',
            'Cosine (Smooth)', 'Inlet Loaded (Attack)', 'Outlet Loaded (Discharge)'
        ])
        self.combo_interp.setToolTip(tt_interp)
        grid.addWidget(self.combo_interp, row, 1)

        left_layout.addWidget(param_group)

        # =====================================================================
        # KAPLAN SUB-PANEL
        # =====================================================================
        self.group_kaplan = QGroupBox("Kaplan Geometry")
        kg = QGridLayout(self.group_kaplan)
        
        tt_rcubo = "Hub inner radius (R_hub): Connects the blade root to the main rotating shaft (in meters)."
        lbl_rcubo = QLabel("Hub Radius R_hub (m):")
        lbl_rcubo.setFont(normal_font)
        lbl_rcubo.setToolTip(tt_rcubo)
        
        self.spin_rcubo = QDoubleSpinBox()
        self.spin_rcubo.setValue(0.30)
        self.spin_rcubo.setToolTip(tt_rcubo)
        
        tt_rpunta = "Tip outer radius (R_tip): Outer bound adjacent to the discharge ring shroud (in meters)."
        lbl_rpunta = QLabel("Tip Radius R_tip (m):")
        lbl_rpunta.setFont(normal_font)
        lbl_rpunta.setToolTip(tt_rpunta)
        
        self.spin_rpunta = QDoubleSpinBox()
        self.spin_rpunta.setValue(0.65)
        self.spin_rpunta.setToolTip(tt_rpunta)
        
        tt_lz = "Axial length (L_z): Total depth of the runner along the Z axis (in meters)."
        lbl_lz = QLabel("Axial Length L_z (m):")
        lbl_lz.setFont(normal_font)
        lbl_lz.setToolTip(tt_lz)
        
        self.spin_lz = QDoubleSpinBox()
        self.spin_lz.setValue(0.35)
        self.spin_lz.setToolTip(tt_lz)
        
        kg.addWidget(lbl_rcubo, 0, 0); kg.addWidget(self.spin_rcubo, 0, 1)
        kg.addWidget(lbl_rpunta, 1, 0); kg.addWidget(self.spin_rpunta, 1, 1)
        kg.addWidget(lbl_lz, 2, 0); kg.addWidget(self.spin_lz, 2, 1)
        left_layout.addWidget(self.group_kaplan)

        # =====================================================================
        # DERIAZ SUB-PANEL
        # =====================================================================
        self.group_deriaz = QGroupBox("Deriaz Geometry")
        dg = QGridLayout(self.group_deriaz)
        
        tt_reint = "Inner spherical hub radius (Re_int) in meters."
        lbl_reint = QLabel("Inner Sph. Rad. Re_int:")
        lbl_reint.setFont(normal_font)
        lbl_reint.setToolTip(tt_reint)
        
        self.spin_re_int = QDoubleSpinBox()
        self.spin_re_int.setValue(2.00)
        self.spin_re_int.setToolTip(tt_reint)
        
        tt_reext = "Outer spherical shroud radius (Re_ext) in meters."
        lbl_reext = QLabel("Outer Sph. Rad. Re_ext:")
        lbl_reext.setFont(normal_font)
        lbl_reext.setToolTip(tt_reext)
        
        self.spin_re_ext = QDoubleSpinBox()
        self.spin_re_ext.setValue(2.60)
        self.spin_re_ext.setToolTip(tt_reext)
        
        tt_gamma1 = "Inlet cone/meridional slope angle (gamma1) in degrees."
        lbl_gamma1 = QLabel("Inlet Angle gamma1 (°):")
        lbl_gamma1.setFont(normal_font)
        lbl_gamma1.setToolTip(tt_gamma1)
        
        self.spin_gamma1 = QDoubleSpinBox()
        self.spin_gamma1.setValue(30.0)
        self.spin_gamma1.setToolTip(tt_gamma1)
        
        tt_gamma2 = "Outlet cone/meridional slope angle (gamma2) in degrees."
        lbl_gamma2 = QLabel("Outlet Angle gamma2 (°):")
        lbl_gamma2.setFont(normal_font)
        lbl_gamma2.setToolTip(tt_gamma2)
        
        self.spin_gamma2 = QDoubleSpinBox()
        self.spin_gamma2.setValue(60.0)
        self.spin_gamma2.setToolTip(tt_gamma2)
        
        dg.addWidget(lbl_reint, 0, 0); dg.addWidget(self.spin_re_int, 0, 1)
        dg.addWidget(lbl_reext, 1, 0); dg.addWidget(self.spin_re_ext, 1, 1)
        dg.addWidget(lbl_gamma1, 2, 0); dg.addWidget(self.spin_gamma1, 2, 1)
        dg.addWidget(lbl_gamma2, 3, 0); dg.addWidget(self.spin_gamma2, 3, 1)
        left_layout.addWidget(self.group_deriaz)

        # =====================================================================
        # ADVANCED OPTIONS
        # =====================================================================
        group_adv = QGroupBox("Advanced Options (Mesh Resolution)")
        ag = QGridLayout(group_adv)
        
        tt_nradios = "Number of radial streamlines discretized from hub to tip."
        lbl_nradios = QLabel("Streamlines (N_radii):")
        lbl_nradios.setFont(normal_font)
        lbl_nradios.setToolTip(tt_nradios)
        
        self.spin_nradios = QSpinBox()
        self.spin_nradios.setRange(5, 200)
        self.spin_nradios.setValue(25)
        self.spin_nradios.setToolTip(tt_nradios)
        
        tt_ncuerda = "Number of stations along the blade chord line."
        lbl_ncuerda = QLabel("Chord Stations (dz/ds):")
        lbl_ncuerda.setFont(normal_font)
        lbl_ncuerda.setToolTip(tt_ncuerda)
        
        self.spin_ncuerda = QSpinBox()
        self.spin_ncuerda.setRange(10, 500)
        self.spin_ncuerda.setValue(40)
        self.spin_ncuerda.setToolTip(tt_ncuerda)
        
        ag.addWidget(lbl_nradios, 0, 0); ag.addWidget(self.spin_nradios, 0, 1)
        ag.addWidget(lbl_ncuerda, 1, 0); ag.addWidget(self.spin_ncuerda, 1, 1)
        left_layout.addWidget(group_adv)

        # =====================================================================
        # BUTTONS
        # =====================================================================
        self.btn_compute = QPushButton(" COMPUTE 3D DESIGN")
        self.btn_compute.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_compute.setStyleSheet("background-color: #1F87E6; color: white; padding: 8px;")
       
        self.btn_compute.clicked.connect(self.compute_turbine)
        left_layout.addWidget(self.btn_compute)

        self.btn_export = QPushButton(" Export Blade to Surface STL")
        self.btn_export.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("background-color: #33B34D; color: white; padding: 8px;")

        self.btn_export.clicked.connect(self.export_stl)
        left_layout.addWidget(self.btn_export)

        left_layout.addStretch()
        scroll_area.setWidget(left_container)
        main_layout.addWidget(scroll_area)

        # =====================================================================
        # RIGHT PANEL: 3D RENDER & RESULTS TABLE
        # =====================================================================
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        self.fig = Figure(figsize=(6, 6))
        self.canvas = FigureCanvas(self.fig)
        self.ax3d = self.fig.add_subplot(111, projection='3d')
        
        right_layout.addWidget(self.canvas, stretch=3)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['Analyzed Parameter', 'Computed Value'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.table.setMinimumHeight(280)
        self.table.setMaximumHeight(320)
        
        right_layout.addWidget(self.table, stretch=1)

        main_layout.addWidget(right_container)

    def on_turbine_type_change(self):
        """Toggles the UI panels depending on the chosen turbine type."""
        is_kaplan = (self.combo_type.currentText() == 'Kaplan (Axial)')
        if is_kaplan:
            self.group_kaplan.setVisible(True)
            self.group_deriaz.setVisible(False)
            self.spin_rpm.setValue(450)
            self.spin_q0.setValue(12)
            self.spin_hn.setValue(15)
            self.spin_eta_h.setValue(0.90)
            self.spin_eta_v.setValue(0.96)
            self.spin_eta_m.setValue(0.98)
            self.spin_sigma.setValue(1.25)
            self.spin_nradios.setValue(25)
            self.spin_ncuerda.setValue(40)
        else:
            self.group_kaplan.setVisible(False)
            self.group_deriaz.setVisible(True)
            self.spin_rpm.setValue(150)
            self.spin_q0.setValue(110)
            self.spin_hn.setValue(60)
            self.spin_eta_h.setValue(0.91)
            self.spin_eta_v.setValue(0.97)
            self.spin_eta_m.setValue(0.98)
            self.spin_sigma.setValue(1.40)
            self.spin_nradios.setValue(30)
            self.spin_ncuerda.setValue(50)

    def compute_turbine(self):
        """
        Main calculation core. Generates the 3D geometry of the blades based
        on hydrodynamic equations. Core logic remains untouched as requested.
        """
        RPM = self.spin_rpm.value()
        Q0 = self.spin_q0.value()
        Hn = self.spin_hn.value()
        g = self.spin_g.value()
        eta_h = self.spin_eta_h.value()
        eta_v = self.spin_eta_v.value()
        eta_o = self.spin_eta_m.value()
        sigma_target = self.spin_sigma.value()
        interpType = self.combo_interp.currentText()

        rotSign = 1.0 if 'Counter-Clockwise' in self.combo_rot.currentText() else -1.0
        N_radios = self.spin_nradios.value()
        N_cuerda = self.spin_ncuerda.value()

        eta_t = eta_h * eta_v * eta_o
        omega = (2 * np.pi * RPM) / 60.0
        Q_real = Q0 * eta_v
        W_n = 1000.0 * g * Q0 * Hn
        W_t = W_n * eta_t
        H_inf = Hn * eta_h
        nq = RPM * np.sqrt(Q0) / ((g * Hn) ** (3.0 / 4.0))

        is_kaplan = (self.combo_type.currentText() == 'Kaplan (Axial)')

        if is_kaplan:
            R_cubo = self.spin_rcubo.value()
            R_punta = self.spin_rpunta.value()
            L_z = self.spin_lz.value()

            if R_cubo >= R_punta:
                QMessageBox.critical(self, "Geometric Error", "Hub radius R_hub must be smaller than tip radius R_tip.")
                return

            R_m = np.sqrt((R_punta**2 + R_cubo**2) / 2.0)
            X = np.zeros((N_cuerda, N_radios))
            Y = np.zeros((N_cuerda, N_radios))
            Z = np.zeros((N_cuerda, N_radios))

            z_vec = np.linspace(0, -L_z, N_cuerda)
            r_vec = np.linspace(R_cubo, R_punta, N_radios)
            Area_paso = np.pi * (R_punta**2 - R_cubo**2)
            V_z = Q_real / Area_paso

            for i in range(N_radios):
                r = r_vec[i]
                U = omega * r
                V_theta1 = (g * H_inf) / (omega * r)

                if V_theta1 >= U:
                    QMessageBox.critical(self, "Physical Limit Error",
                                         f"Physical boundary instability at r={r:.2f}m: V_theta1 ({V_theta1:.2f} m/s) >= U ({U:.2f} m/s).")
                    return

                beta1 = np.arctan2(V_z, (U - V_theta1))
                beta2 = np.arctan2(V_z, U)

                t_dim = np.abs(z_vec) / L_z
                polinomio = evaluate_interpolation(interpType, t_dim)
                beta_z = beta1 + (beta2 - beta1) * polinomio

                theta_rel = 0.0
                for j in range(N_cuerda):
                    if j > 0:
                        dz = np.abs(z_vec[j] - z_vec[j - 1])
                        d_theta_rel = ((1.0 / np.tan(beta_z[j])) / r) * dz
                        theta_rel -= rotSign * d_theta_rel

                    X[j, i] = r * np.cos(theta_rel)
                    Y[j, i] = r * np.sin(theta_rel)
                    Z[j, i] = z_vec[j]

            idx_Rm = np.argmin(np.abs(r_vec - R_m))
            dx = np.diff(X[:, idx_Rm])
            dy = np.diff(Y[:, idx_Rm])
            dz = np.diff(Z[:, idx_Rm])
            L_cuerda_real = np.sum(np.sqrt(dx**2 + dy**2 + dz**2))

            paso_req = L_cuerda_real / sigma_target
            Z_optimo = int(max(3, min(round((2 * np.pi * r_vec[idx_Rm]) / paso_req), 12)))

            rm_label = 'Mean Hydraulic Radius (R_m)'
            rm_val = f'{R_m:.3f} m'

        else:  # Deriaz
            Re_int = self.spin_re_int.value()
            Re_ext = self.spin_re_ext.value()
            gamma1_deg = self.spin_gamma1.value()
            gamma2_deg = self.spin_gamma2.value()

            if Re_int >= Re_ext or gamma1_deg >= gamma2_deg:
                QMessageBox.critical(self, "Geometric Error", "Please check spherical radii or slope angle bounds.")
                return

            gamma1 = np.radians(gamma1_deg)
            gamma2 = np.radians(gamma2_deg)
            Re_medio = (Re_ext - Re_int) / np.log(Re_ext / Re_int)

            Re_vec = np.linspace(Re_int, Re_ext, N_radios)
            gamma_vec = np.linspace(gamma1, gamma2, N_cuerda)

            X = np.zeros((N_cuerda, N_radios))
            Y = np.zeros((N_cuerda, N_radios))
            Z = np.zeros((N_cuerda, N_radios))
            RC = np.zeros((N_cuerda, N_radios))

            for i in range(N_radios):
                Re = Re_vec[i]
                rc1 = Re * np.cos(gamma1)
                U1 = omega * rc1
                Vm1 = Q_real / (2 * np.pi * Re * np.cos(gamma1) * (Re_ext - Re_int))
                Vtheta1 = (g * H_inf) / U1

                if Vtheta1 >= U1:
                    QMessageBox.critical(self, "Physical Limit Error",
                                         f"Physical boundary instability at Re={Re:.2f}m: V_theta1 ({Vtheta1:.2f} m/s) >= U1 ({U1:.2f} m/s).")
                    return

                beta1 = np.arctan2(Vm1, (U1 - Vtheta1))

                rc2 = Re * np.cos(gamma2)
                U2 = omega * rc2
                Vm2 = Q_real / (2 * np.pi * Re * np.cos(gamma2) * (Re_ext - Re_int))
                beta2 = np.arctan2(Vm2, U2)

                t = (gamma_vec - gamma1) / (gamma2 - gamma1)
                polinomio = evaluate_interpolation(interpType, t)
                beta_gamma = beta1 + (beta2 - beta1) * polinomio

                theta_rel = 0.0
                for j in range(N_cuerda):
                    gamma_actual = gamma_vec[j]
                    if j > 0:
                        d_gamma = gamma_vec[j] - gamma_vec[j - 1]
                        gamma_mid = (gamma_vec[j] + gamma_vec[j - 1]) / 2.0
                        beta_mid = (beta_gamma[j] + beta_gamma[j - 1]) / 2.0
                        d_theta_rel = ((1.0 / np.tan(beta_mid)) / np.cos(gamma_mid)) * d_gamma
                        theta_rel -= rotSign * d_theta_rel

                    rc_local = Re * np.cos(gamma_actual)
                    z_local = -Re * np.sin(gamma_actual)
                    X[j, i] = rc_local * np.cos(theta_rel)
                    Y[j, i] = rc_local * np.sin(theta_rel)
                    Z[j, i] = z_local
                    RC[j, i] = rc_local

            idx_Rmedio = np.argmin(np.abs(Re_vec - Re_medio))
            dx = np.diff(X[:, idx_Rmedio])
            dy = np.diff(Y[:, idx_Rmedio])
            dz = np.diff(Z[:, idx_Rmedio])
            L_cuerda_real = np.sum(np.sqrt(dx**2 + dy**2 + dz**2))

            rc_promedio_medio = np.mean(RC[:, idx_Rmedio])
            paso_req = L_cuerda_real / sigma_target
            Z_optimo = int(max(4, min(round((2 * np.pi * rc_promedio_medio) / paso_req), 12)))

            rm_label = 'Mean Spherical Radius (Re_mean)'
            rm_val = f'{Re_medio:.3f} m'

        # Store arrays for STL generation
        self.X_blade = X
        self.Y_blade = Y
        self.Z_blade = Z
        self.is_computed = True
        self.btn_export.setEnabled(True)

        # =====================================================================
        # 3D GRAPHIC RENDER
        # =====================================================================
        self.ax3d.clear()
        delta_angle = (2 * np.pi) / Z_optimo
        
        if is_kaplan:
            theta_c = np.linspace(0, 2 * np.pi, 50)
            z_c = np.linspace(0, -L_z, 2)
            Theta_c, Z_c = np.meshgrid(theta_c, z_c)
            
            # Hub surface
            Xc = R_cubo * np.cos(Theta_c)
            Yc = R_cubo * np.sin(Theta_c)
            self.ax3d.plot_surface(Xc, Yc, Z_c, color='gray', alpha=0.85, 
                                   rstride=1, cstride=5, antialiased=False)

            # Tip wireframe
            Xp = R_punta * np.cos(Theta_c)
            Yp = R_punta * np.sin(Theta_c)
            self.ax3d.plot_wireframe(Xp, Yp, Z_c, color='gray', alpha=0.15)

            # Plot each blade
            for k in range(Z_optimo):
                ang = k * delta_angle
                Xr = X * np.cos(ang) - Y * np.sin(ang)
                Yr = X * np.sin(ang) + Y * np.cos(ang)
                self.ax3d.plot_surface(Xr, Yr, Z, cmap='viridis', edgecolor='none',
                                       rstride=2, cstride=2, antialiased=False)

            self.ax3d.set_title(f'Computed Kaplan Axial Runner ({Z_optimo} Blades)')
            
        else: # Deriaz
            tg, gg = np.meshgrid(np.linspace(0, 2 * np.pi, 50), np.linspace(gamma1, gamma2, 25))
            
            # Inner sphere surface
            Xc = Re_int * np.cos(gg) * np.cos(tg)
            Yc = Re_int * np.cos(gg) * np.sin(tg)
            Zc = -Re_int * np.sin(gg)
            self.ax3d.plot_surface(Xc, Yc, Zc, color='gray', alpha=0.85,
                                   rstride=2, cstride=5, antialiased=False)

            # Outer sphere wireframe
            Xca = Re_ext * np.cos(gg) * np.cos(tg)
            Yca = Re_ext * np.cos(gg) * np.sin(tg)
            Zca = -Re_ext * np.sin(gg)
            self.ax3d.plot_wireframe(Xca, Yca, Zca, color='skyblue', alpha=0.15,
                                     rstride=4, cstride=4)

            # Plot each blade
            for k in range(Z_optimo):
                ang = k * delta_angle
                Xr = X * np.cos(ang) - Y * np.sin(ang)
                Yr = X * np.sin(ang) + Y * np.cos(ang)
                self.ax3d.plot_surface(Xr, Yr, Z, cmap='viridis', edgecolor='none',
                                       rstride=2, cstride=2, antialiased=False)

            self.ax3d.set_title(f'Computed Deriaz Diagonal Runner ({Z_optimo} Blades)')
            
        self.ax3d.set_xlabel('X Axis (m)')
        self.ax3d.set_ylabel('Y Axis (m)')
        self.ax3d.set_zlabel('Z Axis (m)')
    
        # ==========================================================
        # TRUE PROPORTIONS FIX
        # ==========================================================
        R_max = R_punta if is_kaplan else Re_ext
        
        xy_limit = R_max + 0.1
        z_min_real = np.min(Z)
        z_max_real = np.max(Z)
        z_lim_min = z_min_real - 0.1
        z_lim_max = z_max_real + 0.1
        
        self.ax3d.set_xlim(-xy_limit, xy_limit)
        self.ax3d.set_ylim(-xy_limit, xy_limit)
        self.ax3d.set_zlim(z_lim_min, z_lim_max)
        
        x_ext = xy_limit * 2
        y_ext = xy_limit * 2
        z_ext = z_lim_max - z_lim_min
        
        self.ax3d.set_box_aspect((x_ext, y_ext, z_ext))
    
        self.ax3d.view_init(elev=30, azim=-35)
        self.fig.tight_layout(pad=0.0)
        self.canvas.draw()
        
        # =====================================================================
        # RESULTS TABLE
        # =====================================================================
        results_data = [
            ('Total Efficiency (eta_t)', f'{eta_t * 100:.2f} %'),
            ('Adimensional Specific Speed (nq)', f'{nq:.2f} RPM'),
            ('Effective Flow Rate (Q_real)', f'{Q_real:.2f} m³/s'),
            ('Useful Shaft Power (Wt)', f'{W_t / 1000.0:.2f} kW'),
            ('Integrated 3D Chord (L_chord)', f'{L_cuerda_real:.3f} m'),
            ('Number of Blades (Z)', f'{Z_optimo}'),
            (rm_label, rm_val)
        ]

        self.table.setRowCount(len(results_data))
        for r_idx, (param, val) in enumerate(results_data):
            self.table.setItem(r_idx, 0, QTableWidgetItem(param))
            self.table.setItem(r_idx, 1, QTableWidgetItem(val))

    def export_stl(self):
        """Exports the generated mathematical surfaces to a CAD-friendly STL."""
        if not self.is_computed:
            QMessageBox.warning(self, "Attention", "Please compute the design first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save 3D Blade STL", "KaplanDeriaz_Blade.stl", "STL Files (*.stl)")
        if not file_path:
            return

        try:
            export_surface_stl_binary(file_path, self.X_blade, self.Y_blade, self.Z_blade)
            QMessageBox.information(self, "Export Successful", f"Surface STL file exported successfully!\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting STL file: {str(e)}")


if __name__ == '__main__':
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    window = KaplanDeriaz3DApp()
    window.show()
    if not QApplication.instance().property("is_interactive"):
        sys.exit(app.exec_())