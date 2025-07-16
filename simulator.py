# simulator.py (updated to ensure bounce happens at y=0)
import numpy as np
import pandas as pd
from config import *

def simulate_trajectory(
    v0=35.0,              # initial speed (m/s)
    angle_y=-7.5,          # vertical angle (degrees)
    angle_z=2.0,           # horizontal angle (degrees)
    seam_angle=20.0,       # seam angle (degrees)
    e=0.7,                # coefficient of restitution
    mu=0.8,               # friction factor
    output_file=None       # if provided, saves CSV
):
    """Simulate cricket ball trajectory with early termination conditions"""
    # Convert angles to radians
    angle_y = np.radians(angle_y)
    angle_z = np.radians(angle_z)
    seam_angle = np.radians(seam_angle)
    
    # Initial conditions
    vx = v0 * np.cos(angle_y) * np.cos(angle_z)
    vy = v0 * np.sin(angle_y)
    vz = v0 * np.cos(angle_y) * np.sin(angle_z)
    
    # Initialize arrays
    N = int(t_max / dt)
    x = np.zeros(N)
    y = np.zeros(N)
    z = np.zeros(N)
    vx_arr = np.zeros(N)
    vy_arr = np.zeros(N)
    vz_arr = np.zeros(N)
    
    x[0], y[0], z[0] = 0, initial_height, initial_z
    vx_arr[0], vy_arr[0], vz_arr[0] = vx, vy, vz
    
    bounced = False
    valid_trajectory = True
    last_idx = N - 1  # Default to full length
    
    # Simulation loop
    for i in range(N-1):
        v_vec = np.array([vx_arr[i], vy_arr[i], vz_arr[i]])
        v_mag = np.linalg.norm(v_vec)
        
        # Check if ball has exited pitch area
        if x[i] > pitch_length or abs(z[i]) > (pitch_width/2 + pitch_margin):
            # If ball exited laterally before reaching stumps, mark as invalid
            if x[i] < pitch_length and abs(z[i]) > (pitch_width/2 + pitch_margin):
                valid_trajectory = False
            last_idx = i + 1
            break
        
        # Bounce condition - only when crossing y=0 from above
        if not bounced and y[i] > 0 and (y[i] + vy_arr[i] * dt) <= 0:
            bounced = True
            # Calculate exact bounce time
            t_bounce = -y[i] / vy_arr[i]
            # Position at bounce (y=0)
            x_bounce = x[i] + vx_arr[i] * t_bounce
            z_bounce = z[i] + vz_arr[i] * t_bounce
            # Velocity after bounce
            vx_after = vx_arr[i] * mu
            vy_after = -vy_arr[i] * e
            vz_after = vz_arr[i] * mu
            
            # Update next position using remaining time
            remaining_time = dt - t_bounce
            x[i+1] = x_bounce + vx_after * remaining_time
            y[i+1] = 0 + vy_after * remaining_time
            z[i+1] = z_bounce + vz_after * remaining_time
            vx_arr[i+1] = vx_after
            vy_arr[i+1] = vy_after
            vz_arr[i+1] = vz_after
            
            if abs(vy_after) < 0.2:  # Stop if minimal bounce
                last_idx = i + 2
                break
            continue
        
        # Skip physics if we've already processed bounce this timestep
        if bounced and i == last_idx - 1:
            continue
            
        # Drag force
        Fd = 0.5 * Cd * rho * A * v_mag**2
        Fd_vec = -Fd * (v_vec / (v_mag + 1e-8))
        
        # Seam-based swing force
        Cl_swing = Cl_seam_max * np.sin(seam_angle)
        Fs_vec = 0.5 * Cl_swing * rho * A * v_mag**2 * swing_axis
        
        # Net force
        F_net = Fd_vec + Fs_vec + np.array([0, -m * g, 0])
        a = F_net / m
        
        # Update velocities and positions
        vx_arr[i+1] = vx_arr[i] + a[0] * dt
        vy_arr[i+1] = vy_arr[i] + a[1] * dt
        vz_arr[i+1] = vz_arr[i] + a[2] * dt
        
        x[i+1] = x[i] + vx_arr[i] * dt
        y[i+1] = y[i] + vy_arr[i] * dt
        z[i+1] = z[i] + vz_arr[i] * dt
        
        # Early termination if ball has clearly left the field
        if y[i] < -1 or x[i] > pitch_length + 5:
            last_idx = i + 1
            break
    
    # If trajectory is invalid (exited laterally early), return None
    if not valid_trajectory:
        return pd.DataFrame(columns=["time (s)", "x (m)", "y (m)", "z (m)", "vx (m/s)", "vy (m/s)", "vz (m/s)", "v (m/s)"])
    
    # Trim all arrays to the same length
    x = x[:last_idx]
    y = y[:last_idx]
    z = z[:last_idx]
    vx_arr = vx_arr[:last_idx]
    vy_arr = vy_arr[:last_idx]
    vz_arr = vz_arr[:last_idx]
    
    # Create time array
    time = np.linspace(0, last_idx * dt, last_idx)
    
    speed = np.sqrt(vx_arr**2 + vy_arr**2 + vz_arr**2)
    
    log_data = {
        "time (s)": time,
        "x (m)": x,
        "y (m)": y,
        "z (m)": z,
        "vx (m/s)": vx_arr,
        "vy (m/s)": vy_arr,
        "vz (m/s)": vz_arr,
        "v (m/s)": speed
    }
    
    df_log = pd.DataFrame(log_data)
    
    if output_file:
        with open(output_file, 'w') as f:
            params = f"# v0={v0}, angle_y={np.degrees(angle_y)}, angle_z={np.degrees(angle_z)}, "
            params += f"seam_angle={np.degrees(seam_angle)}, e={e}, mu={mu}\n"
            f.write(params)
            df_log.to_csv(f, index=False)
    
    return df_log