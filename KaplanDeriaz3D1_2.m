classdef KaplanDeriaz3D1_2 < handle
    properties
        UIFigure
        MainGrid
        LeftScrollPanel
        LeftGrid
        RightGrid
        Axes3D
        
        % Common Controls
        TurbineTypeDropDown
        RPMEdit
        RotationDropDown
        Q0Edit
        HnEdit
        gEdit
        EtaHEdit
        EtaVEdit
        EtaOEdit
        SigmaEdit
        InterpDropDown
        
        % Kaplan Controls
        KaplanPanel
        RCuboEdit
        RPuntaEdit
        LzEdit
        
        % Deriaz Controls
        DeriazPanel
        ReIntEdit
        ReExtEdit
        Gamma1Edit
        Gamma2Edit
        
        % Advanced Options
        AdvPanel
        NRadiosEdit
        NCuerdaEdit
        
        % Buttons and State
        ComputeBtn
        ExportSTLBtn
        ResultsTable   
        
        % Blade Geometry Data
        X_blade
        Y_blade
        Z_blade
        IsComputed = false
    end
    
    methods
        function app = KaplanDeriaz3D1_2()
            app.createUI();
            app.onTurbineTypeChange();
        end
        
        function createUI(app)
            %% 1. MAIN APPLICATION WINDOW
            screenSize = get(0, 'ScreenSize');
            figWidth  = min(1200, screenSize(3) * 0.88);
            figHeight = min(840,  screenSize(4) * 0.92);
            posX = max(10, (screenSize(3) - figWidth) / 2);
            posY = max(30, (screenSize(4) - figHeight) / 2);
            
            app.UIFigure = uifigure('Name', '3D Kaplan & Deriaz Hydro Turbine Designer v1.2', ...
                'Position', [posX, posY, figWidth, figHeight]);
            
            app.MainGrid = uigridlayout(app.UIFigure, [1, 2]);
            app.MainGrid.ColumnWidth = {440, '1x'};
            
            %% 2. LEFT PANEL: INPUT PARAMETERS
            app.LeftScrollPanel = uipanel(app.MainGrid, 'Title', ' Design Parameters ', ...
                'FontWeight', 'bold', 'FontSize', 11, 'Scrollable', 'off');
            
            app.LeftGrid = uigridlayout(app.LeftScrollPanel, [15, 2]);
            app.LeftGrid.RowSpacing = 3;
            app.LeftGrid.Padding = [8 8 10 8];
            app.LeftGrid.RowHeight = {22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 110, 75, 32, 32};
            app.LeftGrid.ColumnWidth = {170, '1x'};
            
            %% CONTROLS WITH EXTENDED TOOLTIPS
            
            % 1. Turbine Type
            r = 1;
            tip = sprintf('Runner Kinematics:\n• Kaplan: Pure axial flow (ideal for low heads and large flow rates).\n• Deriaz: Diagonal/spherical flow (ideal for medium heads and high operational flexibility).');
            lbl = uilabel(app.LeftGrid, 'Text', 'Turbine Type:', 'FontWeight', 'bold', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.TurbineTypeDropDown = uidropdown(app.LeftGrid, 'Items', {'Kaplan (Axial)', 'Deriaz (Diagonal)'}, 'ValueChangedFcn', @(~,~) app.onTurbineTypeChange(), 'Tooltip', tip);
            app.TurbineTypeDropDown.Layout.Row = r; app.TurbineTypeDropDown.Layout.Column = 2;
            
            % 2. Rotational Speed
            r = 2;
            tip = sprintf('Runner rotational speed in RPM (n).\n• Higher speeds reduce the required runner diameter but increase the risk of cavitation due to lower local static pressures on the suction side (extrados).');
            lbl = uilabel(app.LeftGrid, 'Text', 'Rotational Speed (RPM):', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.RPMEdit = uieditfield(app.LeftGrid, 'numeric', 'Value', 450, 'Tooltip', tip); app.RPMEdit.Layout.Row = r; app.RPMEdit.Layout.Column = 2;
            
            % 3. Rotation Direction
            r = 3;
            tip = sprintf('Runner rotation direction viewed from above (+Z axis looking down):\n• Counter-Clockwise (CCW): Hydroelectric standard convention.\n• Clockwise (CW): Adapted for specific mechanical drive couplings.');
            lbl = uilabel(app.LeftGrid, 'Text', 'Rotation Direction:', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.RotationDropDown = uidropdown(app.LeftGrid, 'Items', {'Counter-Clockwise (Standard)', 'Clockwise'}, 'Tooltip', tip);
            app.RotationDropDown.Layout.Row = r; app.RotationDropDown.Layout.Column = 2;
            
            % 4. Flow Rate Q0
            r = 4;
            tip = sprintf('Nominal design volumetric flow rate (m³/s).\nDetermines the fluid meridional velocity (Vz or Vm) and the cross-sectional passage area required to prevent flow choking.');
            lbl = uilabel(app.LeftGrid, 'Text', 'Flow Rate Q0 (m³/s):', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.Q0Edit = uieditfield(app.LeftGrid, 'numeric', 'Value', 12, 'Tooltip', tip); app.Q0Edit.Layout.Row = r; app.Q0Edit.Layout.Column = 2;
            
            % 5. Net Head Hn
            r = 5;
            tip = sprintf('Net hydraulic head available at the installation (m).\nSets the total available specific energy (g*Hn) that the blades must convert into shaft mechanical torque.');
            lbl = uilabel(app.LeftGrid, 'Text', 'Net Head Hn (m):', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.HnEdit = uieditfield(app.LeftGrid, 'numeric', 'Value', 15, 'Tooltip', tip); app.HnEdit.Layout.Row = r; app.HnEdit.Layout.Column = 2;
            
            % 6. Gravity g
            r = 6;
            tip = sprintf('Local acceleration of gravity (m/s²).\nStandard value: 9.81 m/s².');
            lbl = uilabel(app.LeftGrid, 'Text', 'Gravity g (m/s²):', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.gEdit = uieditfield(app.LeftGrid, 'numeric', 'Value', 9.81, 'Tooltip', tip); app.gEdit.Layout.Row = r; app.gEdit.Layout.Column = 2;
            
            % 7. Hydraulic Efficiency
            r = 7;
            tip = sprintf('Hydraulic efficiency (eta_h = H_inf / Hn).\nAccounts for fluid energy losses due to viscous friction and boundary layer separation along the blade profile.');
            lbl = uilabel(app.LeftGrid, 'Text', 'Hydraulic Eff. (eta_h):', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.EtaHEdit = uieditfield(app.LeftGrid, 'numeric', 'Value', 0.90, 'Limits', [0.1 1], 'Tooltip', tip); app.EtaHEdit.Layout.Row = r; app.EtaHEdit.Layout.Column = 2;
            
            % 8. Volumetric Efficiency
            r = 8;
            tip = sprintf('Volumetric efficiency (eta_v = Q_real / Q0).\nAccounts for internal flow leakage losses through the tip clearance gap between the blade tip and the outer discharge ring.');
            lbl = uilabel(app.LeftGrid, 'Text', 'Volumetric Eff. (eta_v):', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.EtaVEdit = uieditfield(app.LeftGrid, 'numeric', 'Value', 0.96, 'Limits', [0.1 1], 'Tooltip', tip); app.EtaVEdit.Layout.Row = r; app.EtaVEdit.Layout.Column = 2;
            
            % 9. Mechanical Efficiency
            r = 9;
            tip = sprintf('Mechanical efficiency (eta_m).\nAccounts for power losses caused by shaft bearing friction, dynamic shaft seals, and hub disk friction.');
            lbl = uilabel(app.LeftGrid, 'Text', 'Mechanical Eff. (eta_m):', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.EtaOEdit = uieditfield(app.LeftGrid, 'numeric', 'Value', 0.98, 'Limits', [0.1 1], 'Tooltip', tip); app.EtaOEdit.Layout.Row = r; app.EtaOEdit.Layout.Column = 2;
            
            % 10. Solidity (SIGMA)
            r = 10;
            tip = sprintf(['Solidity Ratio (sigma = Chord / Pitch):\n' ...
                '• Controls the number of runner blades (Z):\n' ...
                '  - High Solidity (sigma > 1.4): Increases blade count (e.g., 6 to 8 blades). Reduces hydraulic load per blade and mitigates cavitation, but increases skin friction losses.\n' ...
                '  - Low Solidity (sigma < 1.0): Reduces blade count (e.g., 3 to 4 blades). Minimizes runner mass and surface friction, but requires longer chord lengths or higher lift coefficients.']);
            lbl = uilabel(app.LeftGrid, 'Text', 'Solidity (sigma):', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.SigmaEdit = uieditfield(app.LeftGrid, 'numeric', 'Value', 1.25, 'Limits', [0.5 3], 'Tooltip', tip); app.SigmaEdit.Layout.Row = r; app.SigmaEdit.Layout.Column = 2;
            
            % 11. Interpolation Scheme
            r = 11;
            tip = sprintf(['Beta Angle Distribution Law (Pressure distribution along chord):\n' ...
                '• Cubic (Standard): Smooth distribution. Peak hydrodynamic pressure located around 30-40%% of chord length.\n' ...
                '• Linear (Uniform): Constant angle gradient. Pressure is distributed uniformly along the profile.\n' ...
                '• Cosine (Smooth): Ultra-smooth transition near leading/trailing edges. Minimizes localized cavitation spikes.\n' ...
                '• Inlet Loaded: Steeper deflection at the entry. MAXIMUM PRESSURE ZONE AT LEADING EDGE (ideal for clean, shock-free flow entry).\n' ...
                '• Outlet Loaded: Steeper curvature towards the exit. MAXIMUM PRESSURE ZONE AT TRAILING EDGE (maximizes energy transfer before discharge).']);
            lbl = uilabel(app.LeftGrid, 'Text', 'Interpolation Scheme:', 'Tooltip', tip); lbl.Layout.Row = r; lbl.Layout.Column = 1;
            app.InterpDropDown = uidropdown(app.LeftGrid, 'Items', {'Cubic (Standard)', 'Linear (Uniform)', 'Cosine (Smooth)', 'Inlet Loaded (Attack)', 'Outlet Loaded (Discharge)'}, 'Tooltip', tip);
            app.InterpDropDown.Layout.Row = r; app.InterpDropDown.Layout.Column = 2;
            
            % Sub-Panels: Kaplan
            r = 12;
            app.KaplanPanel = uipanel(app.LeftGrid, 'Title', 'Kaplan Geometry', 'FontWeight', 'bold');
            app.KaplanPanel.Layout.Row = r; app.KaplanPanel.Layout.Column = [1 2];
            kg = uigridlayout(app.KaplanPanel, [3, 2]); kg.RowSpacing = 3; kg.Padding = [5 3 5 3]; kg.RowHeight = {22, 22, 22}; kg.ColumnWidth = {145, '1x'};
            
            tip = 'Hub inner radius (R_hub): Connects the blade root to the main rotating shaft (in meters).';
            l1 = uilabel(kg, 'Text', 'Hub Radius R_hub (m):', 'Tooltip', tip); l1.Layout.Row = 1; l1.Layout.Column = 1;
            app.RCuboEdit = uieditfield(kg, 'numeric', 'Value', 0.30, 'Tooltip', tip); app.RCuboEdit.Layout.Row = 1; app.RCuboEdit.Layout.Column = 2;
            
            tip = 'Tip outer radius (R_tip): Outer bound adjacent to the discharge ring shroud (in meters).';
            l2 = uilabel(kg, 'Text', 'Tip Radius R_tip (m):', 'Tooltip', tip); l2.Layout.Row = 2; l2.Layout.Column = 1;
            app.RPuntaEdit = uieditfield(kg, 'numeric', 'Value', 0.65, 'Tooltip', tip); app.RPuntaEdit.Layout.Row = 2; app.RPuntaEdit.Layout.Column = 2;
            
            tip = 'Axial length (L_z): Total depth of the runner along the Z axis (in meters).';
            l3 = uilabel(kg, 'Text', 'Axial Length L_z (m):', 'Tooltip', tip); l3.Layout.Row = 3; l3.Layout.Column = 1;
            app.LzEdit = uieditfield(kg, 'numeric', 'Value', 0.35, 'Tooltip', tip); app.LzEdit.Layout.Row = 3; app.LzEdit.Layout.Column = 2;
            
            % Sub-Panels: Deriaz
            app.DeriazPanel = uipanel(app.LeftGrid, 'Title', 'Deriaz Geometry', 'FontWeight', 'bold', 'Visible', 'off');
            app.DeriazPanel.Layout.Row = r; app.DeriazPanel.Layout.Column = [1 2];
            dg = uigridlayout(app.DeriazPanel, [4, 2]); dg.RowSpacing = 2; dg.Padding = [5 3 5 3]; dg.RowHeight = {20, 20, 20, 20}; dg.ColumnWidth = {145, '1x'};
            
            tip = 'Inner spherical hub radius (Re_int) in meters.';
            l1 = uilabel(dg, 'Text', 'Inner Sph. Rad. Re_int:', 'Tooltip', tip); l1.Layout.Row = 1; l1.Layout.Column = 1;
            app.ReIntEdit = uieditfield(dg, 'numeric', 'Value', 2.00, 'Tooltip', tip); app.ReIntEdit.Layout.Row = 1; app.ReIntEdit.Layout.Column = 2;
            
            tip = 'Outer spherical shroud radius (Re_ext) in meters.';
            l2 = uilabel(dg, 'Text', 'Outer Sph. Rad. Re_ext:', 'Tooltip', tip); l2.Layout.Row = 2; l2.Layout.Column = 1;
            app.ReExtEdit = uieditfield(dg, 'numeric', 'Value', 2.60, 'Tooltip', tip); app.ReExtEdit.Layout.Row = 2; app.ReExtEdit.Layout.Column = 2;
            
            tip = 'Inlet cone/meridional slope angle (gamma1) in degrees.';
            l3 = uilabel(dg, 'Text', 'Inlet Angle gamma1 (°):', 'Tooltip', tip); l3.Layout.Row = 3; l3.Layout.Column = 1;
            app.Gamma1Edit = uieditfield(dg, 'numeric', 'Value', 30.0, 'Tooltip', tip); app.Gamma1Edit.Layout.Row = 3; app.Gamma1Edit.Layout.Column = 2;
            
            tip = 'Outlet cone/meridional slope angle (gamma2) in degrees.';
            l4 = uilabel(dg, 'Text', 'Outlet Angle gamma2 (°):', 'Tooltip', tip); l4.Layout.Row = 4; l4.Layout.Column = 1;
            app.Gamma2Edit = uieditfield(dg, 'numeric', 'Value', 60.0, 'Tooltip', tip); app.Gamma2Edit.Layout.Row = 4; app.Gamma2Edit.Layout.Column = 2;
            
            % Advanced Options (Mesh Resolution)
            r = 13;
            app.AdvPanel = uipanel(app.LeftGrid, 'Title', 'Advanced Options (Mesh Resolution)', 'FontWeight', 'bold');
            app.AdvPanel.Layout.Row = r; app.AdvPanel.Layout.Column = [1 2];
            ag = uigridlayout(app.AdvPanel, [2, 2]); ag.RowSpacing = 3; ag.Padding = [5 3 5 3]; ag.RowHeight = {22, 22}; ag.ColumnWidth = {165, '1x'};
            
            tip = 'Number of radial streamlines discretized from hub to tip.';
            l1 = uilabel(ag, 'Text', 'Streamlines (N_radii):', 'Tooltip', tip); l1.Layout.Row = 1; l1.Layout.Column = 1;
            app.NRadiosEdit = uieditfield(ag, 'numeric', 'Value', 25, 'Limits', [5 200], 'RoundFractionalValues', 'on', 'Tooltip', tip); app.NRadiosEdit.Layout.Row = 1; app.NRadiosEdit.Layout.Column = 2;
            
            tip = 'Number of stations along the blade chord line.';
            l2 = uilabel(ag, 'Text', 'Chord Stations (dz/ds):', 'Tooltip', tip); l2.Layout.Row = 2; l2.Layout.Column = 1;
            app.NCuerdaEdit = uieditfield(ag, 'numeric', 'Value', 40, 'Limits', [10 500], 'RoundFractionalValues', 'on', 'Tooltip', tip); app.NCuerdaEdit.Layout.Row = 2; app.NCuerdaEdit.Layout.Column = 2;
            
            % Buttons
            r = 14;
            app.ComputeBtn = uibutton(app.LeftGrid, 'push', 'Text', ' COMPUTE 3D DESIGN', 'FontWeight', 'bold', 'FontSize', 11, ...
                'BackgroundColor', [0.12 0.53 0.90], 'FontColor', [1 1 1], 'ButtonPushedFcn', @(~,~) app.computeTurbine(), ...
                'Tooltip', 'Computes the complete 3D geometry and generates the interactive visualization.');
            app.ComputeBtn.Layout.Row = r; app.ComputeBtn.Layout.Column = [1 2];
            
            r = 15;
            app.ExportSTLBtn = uibutton(app.LeftGrid, 'push', 'Text', ' Export Blade to STL', 'FontWeight', 'bold', 'Enable', 'off', ...
                'BackgroundColor', [0.2 0.7 0.3], 'FontColor', [1 1 1], 'ButtonPushedFcn', @(~,~) app.exportSTL(), ...
                'Tooltip', 'Exports the 3D surface mesh of a single blade into a binary .STL file ready for 3D printing or CFD.');
            app.ExportSTLBtn.Layout.Row = r; app.ExportSTLBtn.Layout.Column = [1 2];
            
            %% 3. RIGHT PANEL: 3D RENDER & RESULTS TABLE
            app.RightGrid = uigridlayout(app.MainGrid, [2, 1]);
            app.RightGrid.RowHeight = {'1x', 190};
            
            app.Axes3D = uiaxes(app.RightGrid);
            title(app.Axes3D, '3D Runner Render'); xlabel(app.Axes3D, 'X Axis (m)'); ylabel(app.Axes3D, 'Y Axis (m)'); zlabel(app.Axes3D, 'Z Axis (m)');
            grid(app.Axes3D, 'on'); view(app.Axes3D, -35, 30);
            
            app.ResultsTable = uitable(app.RightGrid, 'ColumnName', {'Analyzed Parameter', 'Computed Value'}, ...
                'RowName', {}, 'ColumnWidth', {240, '1x'}, 'FontName', 'Segoe UI', 'FontSize', 11, ...
                'BackgroundColor', [1 1 1; 0.96 0.96 0.98], ...
                'Tooltip', sprintf('Kinematic Specific Speed Formula:\nnq = (n * sqrt(Q0)) / ((g * Hn)^(3/4))'));
        end
        
        function onTurbineTypeChange(app)
            isKaplan = strcmp(app.TurbineTypeDropDown.Value, 'Kaplan (Axial)');
            if isKaplan
                app.KaplanPanel.Visible = 'on'; app.DeriazPanel.Visible = 'off';
                app.RPMEdit.Value = 450; app.Q0Edit.Value = 12; app.HnEdit.Value = 15;
                app.EtaHEdit.Value = 0.90; app.EtaVEdit.Value = 0.96; app.EtaOEdit.Value = 0.98; app.SigmaEdit.Value = 1.25;
                app.NRadiosEdit.Value = 25; app.NCuerdaEdit.Value = 40;
            else
                app.KaplanPanel.Visible = 'off'; app.DeriazPanel.Visible = 'on';
                app.RPMEdit.Value = 150; app.Q0Edit.Value = 110; app.HnEdit.Value = 60;
                app.EtaHEdit.Value = 0.91; app.EtaVEdit.Value = 0.97; app.EtaOEdit.Value = 0.98; app.SigmaEdit.Value = 1.40;
                app.NRadiosEdit.Value = 30; app.NCuerdaEdit.Value = 50;
            end
        end
        
        function p = evaluateInterpolation(~, typeStr, t)
            switch typeStr
                case 'Cubic (Standard)'; p = 3*(t.^2) - 2*(t.^3);
                case 'Linear (Uniform)'; p = t;
                case 'Cosine (Smooth)'; p = 0.5 * (1 - cos(pi * t));
                case 'Inlet Loaded (Attack)'; p = 1 - (1 - t).^2;
                case 'Outlet Loaded (Discharge)'; p = t.^2;
                otherwise; p = 3*(t.^2) - 2*(t.^3);
            end
        end
        
        function computeTurbine(app)
            RPM = app.RPMEdit.Value;
            Q0 = app.Q0Edit.Value;
            Hn = app.HnEdit.Value;
            g = app.gEdit.Value;
            eta_h = app.EtaHEdit.Value;
            eta_v = app.EtaVEdit.Value;
            eta_o = app.EtaOEdit.Value;
            sigma_target = app.SigmaEdit.Value;
            interpType = app.InterpDropDown.Value;
            
            isCCW = strcmp(app.RotationDropDown.Value, 'Counter-Clockwise (Standard)');
            if isCCW
                rotSign = 1;
            else
                rotSign = -1;
            end
            
            N_radios = app.NRadiosEdit.Value;
            N_cuerda = app.NCuerdaEdit.Value;
            
            eta_t = eta_h * eta_v * eta_o;
            omega = (2 * pi * RPM) / 60;
            Q_real = Q0 * eta_v;
            W_n = 1000 * g * Q0 * Hn;
            W_t = W_n * eta_t;
            H_inf = Hn * eta_h;
            
            nq = RPM * sqrt(Q0) / ((g*Hn)^(3/4));
            
            isKaplan = strcmp(app.TurbineTypeDropDown.Value, 'Kaplan (Axial)');
            
            if isKaplan
                R_cubo = app.RCuboEdit.Value; R_punta = app.RPuntaEdit.Value; L_z = app.LzEdit.Value;
                if R_cubo >= R_punta
                    uialert(app.UIFigure, 'Hub radius R_hub must be smaller than tip radius R_tip.', 'Geometric Error'); return;
                end
                
                R_m = sqrt((R_punta^2 + R_cubo^2) / 2);
                X = zeros(N_cuerda, N_radios); Y = zeros(N_cuerda, N_radios); Z = zeros(N_cuerda, N_radios);
                
                z_vec = linspace(0, -L_z, N_cuerda); r_vec = linspace(R_cubo, R_punta, N_radios);
                Area_paso = pi * (R_punta^2 - R_cubo^2); V_z = Q_real / Area_paso;
                
                for i = 1:N_radios
                    r = r_vec(i); U = omega * r;
                    V_theta1 = (g * H_inf) / (omega * r);
                    
                    if V_theta1 >= U
                        uialert(app.UIFigure, sprintf('Physical boundary instability at r=%.2fm: V_theta1 (%.2f m/s) >= U (%.2f m/s). Increase RPM or decrease head.', r, V_theta1, U), 'Physical Limit Error');
                        return;
                    end
                    
                    beta1 = atan2(V_z, (U - V_theta1)); beta2 = atan2(V_z, U);
                    
                    t_dim = abs(z_vec) / L_z;
                    polinomio = app.evaluateInterpolation(interpType, t_dim);
                    beta_z = beta1 + (beta2 - beta1) .* polinomio;
                    
                    theta_rel = 0;
                    for j = 1:N_cuerda
                        if j > 1
                            dz = abs(z_vec(j) - z_vec(j-1)); 
                            d_theta_rel = (cot(beta_z(j)) / r) * dz; 
                            theta_rel = theta_rel - rotSign * d_theta_rel;
                        end
                        X(j, i) = r * cos(theta_rel); Y(j, i) = r * sin(theta_rel); Z(j, i) = z_vec(j);
                    end
                end
                
                [~, idx_Rm] = min(abs(r_vec - R_m));
                dx = diff(X(:, idx_Rm)); dy = diff(Y(:, idx_Rm)); dz = diff(Z(:, idx_Rm));
                L_cuerda_real = sum(sqrt(dx.^2 + dy.^2 + dz.^2));
                
                paso_req = L_cuerda_real / sigma_target;
                Z_optimo = max(3, min(round((2 * pi * r_vec(idx_Rm)) / paso_req), 12));
                
                rm_label = 'Mean Hydraulic Radius (R_m)'; rm_val = sprintf('%.3f m', R_m);
                
            else
                Re_int = app.ReIntEdit.Value; Re_ext = app.ReExtEdit.Value;
                gamma1_deg = app.Gamma1Edit.Value; gamma2_deg = app.Gamma2Edit.Value;
                
                if Re_int >= Re_ext || gamma1_deg >= gamma2_deg
                    uialert(app.UIFigure, 'Please check spherical radii or slope angle bounds.', 'Geometric Error'); return;
                end
                
                gamma1 = deg2rad(gamma1_deg); gamma2 = deg2rad(gamma2_deg);
                Re_medio = (Re_ext - Re_int) / log(Re_ext / Re_int);
                
                Re_vec = linspace(Re_int, Re_ext, N_radios); gamma_vec = linspace(gamma1, gamma2, N_cuerda);
                
                X = zeros(N_cuerda, N_radios); Y = zeros(N_cuerda, N_radios); Z = zeros(N_cuerda, N_radios); RC = zeros(N_cuerda, N_radios);
                
                for i = 1:N_radios
                    Re = Re_vec(i); rc1 = Re * cos(gamma1); U1 = omega * rc1;
                    Vm1 = Q_real / (2 * pi * Re * cos(gamma1) * (Re_ext - Re_int));
                    Vtheta1 = (g * H_inf) / U1;
                    
                    if Vtheta1 >= U1
                        uialert(app.UIFigure, sprintf('Physical boundary instability at Re=%.2fm: V_theta1 (%.2f m/s) >= U1 (%.2f m/s). Increase RPM or decrease head.', Re, Vtheta1, U1), 'Physical Limit Error');
                        return;
                    end
                    beta1 = atan2(Vm1, (U1 - Vtheta1));
                    
                    rc2 = Re * cos(gamma2); U2 = omega * rc2;
                    Vm2 = Q_real / (2 * pi * Re * cos(gamma2) * (Re_ext - Re_int));
                    beta2 = atan2(Vm2, U2);
                    
                    t = (gamma_vec - gamma1) / (gamma2 - gamma1);
                    polinomio = app.evaluateInterpolation(interpType, t);
                    beta_gamma = beta1 + (beta2 - beta1) .* polinomio;
                    
                    theta_rel = 0;
                    for j = 1:N_cuerda
                        gamma_actual = gamma_vec(j);
                        if j > 1
                            d_gamma = gamma_vec(j) - gamma_vec(j-1);
                            gamma_mid = (gamma_vec(j) + gamma_vec(j-1)) / 2;
                            beta_mid  = (beta_gamma(j) + beta_gamma(j-1)) / 2;
                            d_theta_rel = (cot(beta_mid) / cos(gamma_mid)) * d_gamma;
                            theta_rel = theta_rel - rotSign * d_theta_rel;
                        end
                        rc_local = Re * cos(gamma_actual); z_local = -Re * sin(gamma_actual);
                        X(j, i) = rc_local * cos(theta_rel); Y(j, i) = rc_local * sin(theta_rel); Z(j, i) = z_local; RC(j, i) = rc_local;
                    end
                end
                
                [~, idx_Rmedio] = min(abs(Re_vec - Re_medio));
                dx = diff(X(:, idx_Rmedio)); dy = diff(Y(:, idx_Rmedio)); dz = diff(Z(:, idx_Rmedio));
                L_cuerda_real = sum(sqrt(dx.^2 + dy.^2 + dz.^2));
                
                rc_promedio_medio = mean(RC(:, idx_Rmedio));
                paso_req = L_cuerda_real / sigma_target;
                Z_optimo = max(4, min(round((2 * pi * rc_promedio_medio) / paso_req), 12));
                
                rm_label = 'Mean Spherical Radius (Re_mean)'; rm_val = sprintf('%.3f m', Re_medio);
            end
            
            app.X_blade = X; app.Y_blade = Y; app.Z_blade = Z;
            app.IsComputed = true; app.ExportSTLBtn.Enable = 'on';
            
            %% 3D GRAPHICAL RENDER
            cla(app.Axes3D); hold(app.Axes3D, 'on');
            delta_angle = (2 * pi) / Z_optimo;
            
            if isKaplan
                [Xc, Yc, Zc] = cylinder(app.Axes3D, R_cubo, 50); Zc = Zc * (-L_z);
                surf(app.Axes3D, Xc, Yc, Zc, 'FaceColor', [0.4 0.4 0.4], 'EdgeColor', 'none', 'FaceAlpha', 0.85);
                
                [Xp, Yp, Zp] = cylinder(app.Axes3D, R_punta, 50); Zp = Zp * (-L_z);
                mesh(app.Axes3D, Xp, Yp, Zp, 'FaceColor', [0.3 0.6 0.9], 'FaceAlpha', 0.10, 'EdgeColor', [0.6 0.6 0.6], 'EdgeAlpha', 0.1);
                
                [R_grid, ~] = meshgrid(r_vec, z_vec);
                for k = 1:Z_optimo
                    ang = (k - 1) * delta_angle; Xr = X * cos(ang) - Y * sin(ang); Yr = X * sin(ang) + Y * cos(ang);
                    surf(app.Axes3D, Xr, Yr, Z, R_grid, 'FaceColor', 'interp', 'EdgeColor', 'none');
                end
                
                clim(app.Axes3D, [R_cubo, R_punta]); 
                title(app.Axes3D, sprintf('Computed Kaplan Axial Runner (%d Blades)', Z_optimo));
                
            else
                [tg, gg] = meshgrid(linspace(0, 2*pi, 50), linspace(gamma1, gamma2, 25));
                Xc = Re_int * cos(gg) .* cos(tg); Yc = Re_int * cos(gg) .* sin(tg); Zc = -Re_int * sin(gg);
                surf(app.Axes3D, Xc, Yc, Zc, 'FaceColor', [0.4 0.4 0.4], 'EdgeColor', 'none', 'FaceAlpha', 0.85);
                
                Xca = Re_ext * cos(gg) .* cos(tg); Yca = Re_ext * cos(gg) .* sin(tg); Zca = -Re_ext * sin(gg);
                mesh(app.Axes3D, Xca, Yca, Zca, 'FaceColor', [0.2 0.5 0.8], 'FaceAlpha', 0.10, 'EdgeColor', [0.3 0.7 0.9], 'EdgeAlpha', 0.15);
                
                for k = 1:Z_optimo
                    ang = (k - 1) * delta_angle; Xr = X * cos(ang) - Y * sin(ang); Yr = X * sin(ang) + Y * cos(ang);
                    surf(app.Axes3D, Xr, Yr, Z, RC, 'FaceColor', 'interp', 'EdgeColor', 'none');
                end
                clim(app.Axes3D, [min(RC(:)), max(RC(:))]); 
                title(app.Axes3D, sprintf('Computed Deriaz Diagonal Runner (%d Blades)', Z_optimo));
            end
            
            colormap(app.Axes3D, parula(256)); axis(app.Axes3D, 'equal'); grid(app.Axes3D, 'on'); view(app.Axes3D, -35, 30);
            lighting(app.Axes3D, 'none'); 
            delete(findobj(app.Axes3D, 'Type', 'light'));
            app.Axes3D.Colormap = parula(256) * 0.90; 
            
            hold(app.Axes3D, 'off');
            
            %% POPULATE RESULTS TABLE
            tableData = {
                'Total Efficiency (eta_t)', sprintf('%.2f %%', eta_t * 100);
                'Specific Speed (nq)', sprintf('%.2f', nq);
                'Effective Flow Rate (Q_real)', sprintf('%.2f m³/s', Q_real);
                'Useful Shaft Power (Wt)', sprintf('%.2f kW', W_t / 1000);
                'Integrated 3D Chord (L_chord)', sprintf('%.3f m', L_cuerda_real);
                'Number of Blades (Z)', sprintf('%d', Z_optimo);
                rm_label, rm_val
            };
            
            app.ResultsTable.Data = tableData;
        end
        
        function exportSTL(app)
            if ~app.IsComputed
                uialert(app.UIFigure, 'Please compute the design first.', 'Attention'); return;
            end
            
            [file, path] = uiputfile('*.stl', 'Save 3D Blade STL', 'KaplanDeriaz_Blade.stl');
            if isequal(file, 0) || isequal(path, 0)
                return;
            end
            
            fullPath = fullfile(path, file);
            
            try
                X = app.X_blade; Y = app.Y_blade; Z = app.Z_blade; [M, N] = size(X);
                vertices = [X(:), Y(:), Z(:)]; faces = [];
                for i = 1:(N-1)
                    for j = 1:(M-1)
                        idx1 = (i-1)*M + j; idx2 = (i-1)*M + j + 1;
                        idx3 = i*M + j + 1; idx4 = i*M + j;
                        faces = [faces; idx1, idx2, idx3; idx1, idx3, idx4]; %#ok<AGROW>
                    end
                end
                
                TR = triangulation(faces, vertices); stlwrite(TR, fullPath);
                uialert(app.UIFigure, sprintf('STL file exported successfully!\n%s', fullPath), 'Export Successful', 'Icon', 'success');
            catch ME
                uialert(app.UIFigure, sprintf('Error exporting STL file: %s', ME.message), 'Export Error', 'Icon', 'error');
            end
        end
    end
end