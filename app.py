# Add these at the top of app.py
import streamlit as st
import numpy as np
import pandas as pd
from simulator import simulate_trajectory
from utils import create_animation

# Configure page
st.set_page_config(layout="wide", page_title="Cricket Ball Simulator")
st.title("🏏 Cricket Ball Trajectory Simulator")

# Sidebar controls
with st.sidebar:
    st.header("Simulation Parameters")
    v0 = st.slider("Initial Speed (km/h)", 100, 150, 130) / 3.6  # Convert to m/s
    angle_y = st.slider("Vertical Angle (deg)", -15, 5, -5)
    angle_z = st.slider("Horizontal Angle (deg)", -5, 5, 0)
    seam_angle = st.slider("Seam Angle (deg)", -90, 90, 20)
    e = st.slider("Bounce Coefficient (e)", 0.1, 0.9, 0.7)
    mu = st.slider("Friction (μ)", 0.1, 1.0, 0.8)

# Run simulation
if st.button("Simulate Ball Trajectory"):
    params = {
        'v0': v0,
        'angle_y': angle_y,
        'angle_z': angle_z,
        'seam_angle': seam_angle,
        'e': e,
        'mu': mu
    }
    
    with st.spinner("Calculating trajectory..."):
        df = simulate_trajectory(**params)
    
    if df.empty:
        st.error("Invalid trajectory - ball exited pitch too early!")
    else:
        # Show metrics
        stump_cross = df[np.isclose(df['x (m)'], 20.12, atol=0.1)]

        if not stump_cross.empty:
            y_at_stumps = stump_cross['y (m)'].iloc[0]
            z_at_stumps = stump_cross['z (m)'].iloc[0]
            
            hit_stumps = (y_at_stumps <= 0.71) and (abs(z_at_stumps) <= 0.15)  # z within stump width
        else:
            hit_stumps = False
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Result", "🏏 Hit Stumps!" if hit_stumps else "❌ Missed")
        
        with col2:
            st.metric("Max Height", f"{df['y (m)'].max():.2f}m")
            st.metric("Bounce Location", f"{df[df['y (m)'] < 0.1]['x (m)'].iloc[0]:.2f}m")
        
        # Show animation
        fig = create_animation(df, params)
        st.plotly_chart(fig, use_container_width=True)

# Instructions
st.markdown("""
### How to Use:
1. Adjust parameters in the sidebar
2. Click "Simulate Ball Trajectory"
3. View results and 3D animation

**Tip:** Try seam angles between 20°-60° for noticeable swing!
""")