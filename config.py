import numpy as np

# Physics constants
g = 9.81                  # gravity (m/s²)
rho = 1.225               # air density (kg/m³)
R = 0.036                 # cricket ball radius (m)
A = np.pi * R**2          # cross-sectional area (m²)
m = 0.156                 # mass of ball (kg)
Cd = 0.5                  # drag coefficient
Cl_seam_max = 0.25        # max swing lift coefficient
swing_axis = np.array([0, 0, 1])  # swing in Z direction (sideways)

# Simulation settings
dt = 0.001                # time step (s)
t_max = 2.0               # max simulation time (s)
initial_height = 2.0      # release height (m)
initial_z = 0.75          # initial lateral position (m)
pitch_length = 20.12      # cricket pitch length (m)
pitch_width = 3.0         # cricket pitch width (m)
pitch_margin = 0