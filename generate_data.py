# generate_data.py (modified)
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from simulator import simulate_trajectory
from utils import create_animation
from config import *

# Create directories
os.makedirs("simulations/logs", exist_ok=True)
os.makedirs("simulations/animations", exist_ok=True)

# Parameter ranges
PARAM_RANGES = {
    'v0': (30, 42),          # m/s
    'angle_y': (-10, 0),     # degrees
    'angle_z': (-5, 5),      # degrees
    'seam_angle': (-90, 90),   # degrees
    'e': (0.5, 0.8),        # coefficient of restitution
    'mu': (0.5, 0.8)        # friction factor
}

def generate_random_params():
    return {param: np.random.uniform(low, high) for param, (low, high) in PARAM_RANGES.items()}

def create_analysis_plots(metadata_df):
    """Generate additional analysis plots from simulation metadata"""
    # Create output directory if it doesn't exist
    os.makedirs("simulations/analysis", exist_ok=True)
    
    # 1. Print number of times wicket was hit
    total_hits = metadata_df['hit_stumps'].sum()
    print(f"\nWicket Analysis:")
    print(f"• Total wickets hit: {total_hits} out of {len(metadata_df)} simulations")
    print(f"• Wicket hit percentage: {total_hits/len(metadata_df)*100:.1f}%")
    
    # 2. Create 2D stump plot showing final positions (y vs z)
    plt.figure(figsize=(10, 6))
    
    # Stump dimensions
    stump_width = 0.035  # Radius of stumps (3.5cm)
    stump_height = 0.71  # Height of stumps (71cm)
    bail_length = 0.114  # Length of bails (11.4cm)
    
    # Draw stumps at z positions -0.2m, 0m, 0.2m
    for z_pos in [-0.2, 0, 0.2]:
        plt.plot([z_pos-stump_width, z_pos+stump_width], [0, 0], 'brown', linewidth=6)  # Base
        plt.plot([z_pos, z_pos], [0, stump_height], 'brown', linewidth=4)  # Stump
    
    # Draw bails on top of stumps
    plt.plot([-0.2-stump_width, 0.2+stump_width], [stump_height, stump_height], 
             'white', linewidth=6)  # Main connecting bail
    for z_pos in [-0.2, 0, 0.2]:
        plt.plot([z_pos-bail_length/2, z_pos+bail_length/2], 
                 [stump_height+0.01, stump_height+0.01], 
                 'white', linewidth=4)  # Individual bails
    
    # Plot final positions
    hits = metadata_df[metadata_df['hit_stumps']]
    misses = metadata_df[~metadata_df['hit_stumps']]
    
    plt.scatter(misses['final_z_position_m'], misses['final_y_position_m'], 
                c='blue', alpha=0.5, label='Misses')
    plt.scatter(hits['final_z_position_m'], hits['final_y_position_m'], 
                c='red', s=80, marker='x', label='Hits')
    
    # Formatting
    plt.xlim(-2, 2)  # Lateral position range
    plt.ylim(-0.1, 2.5)  # Height range (from below ground to max height)
    plt.xlabel('Lateral Position (m)')
    plt.ylabel('Height (m)')
    plt.title('Final Ball Positions (Height vs Lateral Position)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Add lines marking the stumps zone
    plt.axvline(-0.22, color='brown', linestyle=':', alpha=0.5)
    plt.axvline(0.22, color='brown', linestyle=':', alpha=0.5)
    plt.axhline(stump_height, color='white', linestyle=':', alpha=0.5)
    
    # Save the plot
    plt.savefig('simulations/analysis/stump_positions_yz.png', bbox_inches='tight', dpi=150)
    plt.close()
    
    # [Rest of your existing code for KDE plot remains the same]
    # 3. Create KDE plot of final z-positions
    plt.figure(figsize=(10, 6))
    sns.kdeplot(data=metadata_df, x='final_z_position_m', fill=True, 
                color='blue', alpha=0.5, label='All Simulations')
    sns.kdeplot(data=hits, x='final_z_position_m', fill=True, 
                color='red', alpha=0.5, label='Wicket Hits')
    
    # Add vertical lines for stumps
    plt.axvline(-0.2, color='brown', linestyle='--', linewidth=2, alpha=0.7)
    plt.axvline(0, color='brown', linestyle='--', linewidth=2, alpha=0.7)
    plt.axvline(0.2, color='brown', linestyle='--', linewidth=2, alpha=0.7)
    
    # Formatting
    plt.xlabel('Lateral Position at Stumps (m)')
    plt.ylabel('Density')
    plt.title('Distribution of Final Lateral Positions')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save the plot
    plt.savefig('simulations/analysis/z_position_kde.png', bbox_inches='tight', dpi=150)
    plt.close()
    
    print("\nAnalysis plots saved to simulations/analysis/ directory")

def generate_dataset(num_simulations=1000):
    """Generate dataset of valid simulations that stay within pitch bounds"""
    metadata = []
    valid_simulations = 0
    attempts = 0
    max_attempts = num_simulations * 2  # Prevent infinite loops
    
    os.makedirs("simulations/logs", exist_ok=True)
    os.makedirs("simulations/animations", exist_ok=True)
    
    while valid_simulations < num_simulations and attempts < max_attempts:
        attempts += 1
        params = generate_random_params()
        log_file = f"simulations/logs/sim_{valid_simulations:04d}.csv"
        anim_file = f"simulations/animations/sim_{valid_simulations:04d}.html"
        
        # Run simulation
        df = simulate_trajectory(**params, output_file=log_file)
        
        # Skip invalid trajectories (exited laterally early or empty DataFrame)
        if df is None or df.empty:
            continue
            
        # Additional validation - must reach at least halfway down pitch
        if len(df) == 0 or df['x (m)'].iloc[-1] < pitch_length/2:
            continue
            
        # Save animation (optional - can comment out to speed up generation)
        create_animation(df, params, anim_file)
        
        # Calculate outcome metrics
        final_x = df['x (m)'].iloc[-1]
        final_z = df['z (m)'].iloc[-1]
        final_y = df['y (m)'].iloc[-1]
        
        # Detect if ball hit stumps
        hit_stumps = False
        if abs(final_z) <= 0.22 and abs(final_x - pitch_length) <= 0.5 and final_y <= 0.71:  # 0.71m is stump height
            hit_stumps = True
            
        # Calculate swing as difference between actual and no-swing trajectories
        no_swing_params = params.copy()
        no_swing_params['seam_angle'] = 0  # Remove swing effect
        df_no_swing = simulate_trajectory(**no_swing_params)
        swing_distance = 0
        if df_no_swing is not None and not df_no_swing.empty:  # Only calculate if we got valid data
            swing_distance = df['z (m)'].iloc[-1] - df_no_swing['z (m)'].iloc[-1]

        # Find bounce point
        bounce_idx = None
        for i in range(1, len(df)):
            if df['y (m)'].iloc[i] < 0.05:  # near ground
                vy_prev = df['vy (m/s)'].iloc[i-1]
                vy_curr = df['vy (m/s)'].iloc[i]
                if vy_prev < 0 and vy_curr >= 0:
                    bounce_idx = i
                    break
        
        if bounce_idx is not None:
            bounce_x = df['x (m)'].iloc[bounce_idx]
            max_height = df['y (m)'].iloc[bounce_idx:].max()
        else:
            bounce_x = -1  # indicates no bounce
            max_height = df['y (m)'].max()
        
        # Record all data
        metadata.append({
            # Input parameters
            'initial_speed_mps': params['v0'],
            'initial_vertical_angle_deg': params['angle_y'],
            'initial_horizontal_angle_deg': params['angle_z'],
            'seam_angle_deg': params['seam_angle'],
            'coefficient_of_restitution': params['e'],
            'friction_factor': params['mu'],
            
            # Output metrics
            'final_x_position_m': final_x,
            'final_z_position_m': final_z,
            'final_y_position_m': final_y,
            'bounce_x_position_m': bounce_x,
            'max_height_m': max_height,
            'swing_distance_m': swing_distance,
            'hit_stumps': hit_stumps,
            
            # File references
            'log_file': log_file,
            'animation_file': anim_file
        })
        
        valid_simulations += 1
        
        if valid_simulations % 50 == 0:
            print(f"Generated {valid_simulations}/{num_simulations} valid simulations")
    
    # Save metadata
    metadata_df = pd.DataFrame(metadata)
    metadata_df.to_csv("simulations/final_dataset.csv", index=False)
    
    # Print summary
    success_rate = (valid_simulations / attempts) * 100
    print(f"\nDataset generation complete!")
    print(f"• Valid simulations: {valid_simulations}")
    print(f"• Attempts: {attempts}")
    print(f"• Success rate: {success_rate:.1f}%")
    
    return metadata_df

if __name__ == "__main__":
    metadata_df = generate_dataset(1000)
    create_analysis_plots(metadata_df)