# utils.py
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from config import *
from simulator import simulate_trajectory

def create_animation(df, params=None, output_file=None):
    """Generate HTML animation of trajectory with parameter display"""
    # Constants
    stump_height = 0.71  # Height of cricket stumps in meters
    stump_radius = 0.035  # Radius of stumps (about 3.5cm)
    bail_length = 0.114  # Length of bails (4.5 inches)
    
    # Create figure with larger size for better visibility
    fig = go.Figure(layout=dict(width=1000, height=800))

    # Calculate outcome metrics
    final_x = df['x (m)'].iloc[-1]
    final_z = df['z (m)'].iloc[-1]
    final_y = df['y (m)'].iloc[-1]
    
    # Calculate swing as difference between actual and no-swing trajectories
    swing_distance = 0
    if params:
        no_swing_params = params.copy()
        no_swing_params['seam_angle'] = 0  # Remove swing effect
        df_no_swing = simulate_trajectory(**no_swing_params)
        if df_no_swing is not None and not df_no_swing.empty:
            swing_distance = df['z (m)'].iloc[-1] - df_no_swing['z (m)'].iloc[-1]
    
    # Detect if ball hit stumps
    hit_stumps = False
    if abs(final_z) <= 0.22 and abs(final_x - pitch_length) <= 0.5 and final_y <= stump_height:
        hit_stumps = True
    
    # Improved bounce detection
    bounce_idx = None
    for i in range(1, len(df)):
        if df['y (m)'].iloc[i] < 0.05:  # near ground
            vy_prev = df['vy (m/s)'].iloc[i-1]
            vy_curr = df['vy (m/s)'].iloc[i]
            if vy_prev < 0 and vy_curr >= 0:
                bounce_idx = i
                break
            
    if bounce_idx is None:
        bounce_idx = len(df) // 2
    bounce_x = df['x (m)'].iloc[bounce_idx]
    bounce_z = df['z (m)'].iloc[bounce_idx]
    bounce_y = df['y (m)'].iloc[bounce_idx]
    
    if bounce_idx is not None:
        max_height = df['y (m)'].iloc[bounce_idx:].max()
    else:
        max_height = df['y (m)'].max() if not df.empty else 0
    
    # Create parallel no-swing simulation
    if params:
        no_swing_params = params.copy()
        no_swing_params['seam_angle'] = 0
        df_no_swing = simulate_trajectory(**no_swing_params)
        
        if df_no_swing is not None and not df_no_swing.empty:
            fig.add_trace(go.Scatter3d(
                x=df_no_swing['x (m)'], 
                y=df_no_swing['z (m)'], 
                z=df_no_swing['y (m)'],
                mode='lines',
                line=dict(
                    color='rgba(255,100,100,0.9)',
                    width=8,
                    dash='dot'
                ),
                name='No-Swing Trajectory',
                hovertemplate="x: %{x:.2f}m<br>z: %{y:.2f}m<br>y: %{z:.2f}m<extra></extra>"
            ))

    # Add parameter annotation
    if params:
        param_text = "<b>Simulation Parameters:</b><br>" + "<br>".join([
            f"• {k}: {v * 3.6:.1f} km/h" if k == 'v0' else
            f"• {k}: {v:.1f}°" if 'angle' in k or 'seam' in k else
            f"• {k}: {v:.2f}"
            for k, v in params.items()
        ])
        
        outcome_text = "<b>Outcome:</b><br>"
        if hit_stumps:
            outcome_text += "• Hit stumps!<br>"
        else:
            outcome_text += "• Missed stumps<br>"
        outcome_text += f"• Swing: {swing_distance:.2f}m<br>"
        outcome_text += f"• Bounce at: {bounce_x:.2f}m<br>"
        outcome_text += f"• Max height: {max_height:.2f}m"

        fig.add_annotation(
            x=0.05, y=0.95,
            xref="paper", yref="paper",
            text=param_text,
            showarrow=False,
            align="left",
            font=dict(size=12),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="black",
            borderwidth=1,
            borderpad=4
        )
        
        fig.add_annotation(
            x=0.05, y=0.65,
            xref="paper", yref="paper",
            text=outcome_text,
            showarrow=False,
            align="left",
            font=dict(size=12, color='red' if hit_stumps else 'black'),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="red" if hit_stumps else "black",
            borderwidth=2,
            borderpad=4
        )

    # Main trajectory
    fig.add_trace(go.Scatter3d(
        x=df['x (m)'], y=df['z (m)'], z=df['y (m)'],
        mode='lines+markers',
        marker=dict(
            size=4,
            color=df['time (s)'],
            colorscale='Viridis',
            colorbar=dict(title='Time (s)')
        ),
        line=dict(color='darkblue', width=4),
        name='Trajectory',
        hovertemplate=(
            "x: %{x:.2f}m<br>z: %{y:.2f}m<br>y: %{z:.2f}m<br>" +
            "Speed: %{customdata:.1f} km/h<extra></extra>"
        ),
        customdata=df['v (m/s)'] * 3.6
    ))

    # Bounce point marker
    fig.add_trace(go.Scatter3d(
        x=[bounce_x],
        y=[bounce_z],
        z=[bounce_y],
        mode='markers',
        marker=dict(
            size=8,
            color='orange',
            symbol='diamond'
        ),
        name='Bounce Point',
        hovertemplate=f"Bounce at x: {bounce_x:.2f}m<br>z: {bounce_z:.2f}m<br>y: {bounce_y:.2f}m<extra></extra>"
    ))

    # Final position marker
    fig.add_trace(go.Scatter3d(
        x=[final_x],
        y=[final_z],
        z=[final_y],
        mode='markers',
        marker=dict(
            size=8,
            color='red' if hit_stumps else 'green',
            symbol='x' if hit_stumps else 'circle'
        ),
        name='Final Position',
        hovertemplate=f"Final position<br>x: {final_x:.2f}m<br>z: {final_z:.2f}m<br>y: {final_y:.2f}m<extra></extra>"
    ))

    # Pitch surface
    fig.add_trace(go.Mesh3d(
        x=[0, pitch_length, pitch_length, 0],
        y=[-pitch_width/2, -pitch_width/2, pitch_width/2, pitch_width/2],
        z=[0, 0, 0, 0],
        color='lightgreen',
        opacity=0.6,
        name='Pitch',
        hoverinfo='none'
    ))

    # Pitch boundaries
    fig.add_trace(go.Scatter3d(
        x=[0, pitch_length, pitch_length, 0, 0],
        y=[-pitch_width/2, -pitch_width/2, pitch_width/2, pitch_width/2, -pitch_width/2],
        z=[0, 0, 0, 0, 0],
        mode='lines',
        line=dict(color='green', width=4),
        name='Pitch Boundaries',
        hoverinfo='none'
    ))

    # Creases (bowling and popping creases)
    crease_length = 2.64
    crease_width = 0.02
    
    # Bowling crease (back crease)
    fig.add_trace(go.Scatter3d(
        x=[0, 0, 0, 0, 0],
        y=[-crease_length/2, -crease_length/2, crease_length/2, crease_length/2, -crease_length/2],
        z=[0, crease_width, crease_width, 0, 0],
        mode='lines',
        line=dict(color='white', width=3),
        name='Bowling Crease',
        hoverinfo='none'
    ))
    
    # Popping crease (front crease, 1.22m from bowling crease)
    fig.add_trace(go.Scatter3d(
        x=[1.22, 1.22, 1.22, 1.22, 1.22],
        y=[-crease_length/2, -crease_length/2, crease_length/2, crease_length/2, -crease_length/2],
        z=[0, crease_width, crease_width, 0, 0],
        mode='lines',
        line=dict(color='white', width=3),
        name='Popping Crease',
        hoverinfo='none'
    ))
    
    # Repeat at batsman's end
    fig.add_trace(go.Scatter3d(
        x=[pitch_length, pitch_length, pitch_length, pitch_length, pitch_length],
        y=[-crease_length/2, -crease_length/2, crease_length/2, crease_length/2, -crease_length/2],
        z=[0, crease_width, crease_width, 0, 0],
        mode='lines',
        line=dict(color='white', width=3),
        name='Bowling Crease (Batsman)',
        hoverinfo='none'
    ))
    
    fig.add_trace(go.Scatter3d(
        x=[pitch_length-1.22, pitch_length-1.22, pitch_length-1.22, pitch_length-1.22, pitch_length-1.22],
        y=[-crease_length/2, -crease_length/2, crease_length/2, crease_length/2, -crease_length/2],
        z=[0, crease_width, crease_width, 0, 0],
        mode='lines',
        line=dict(color='white', width=3),
        name='Popping Crease (Batsman)',
        hoverinfo='none'
    ))

    # Stumps (with hit detection)
    for x_pos in [0, pitch_length]:
        for z_pos in [-0.2, 0, 0.2]:
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_pos],
                y=[z_pos, z_pos],
                z=[0, stump_height],
                mode='lines',
                line=dict(
                    color='red' if hit_stumps and abs(x_pos - final_x) < 0.5 and abs(z_pos - final_z) < 0.11 else 'brown',
                    width=6
                ),
                showlegend=False,
                hoverinfo='none'
            ))

    # Add bails on top of stumps
    for x_pos in [0, pitch_length]:
        # Center bail (connects all three stumps)
        fig.add_trace(go.Scatter3d(
            x=[x_pos, x_pos],
            y=[-0.2 - stump_radius, 0.2 + stump_radius],
            z=[stump_height, stump_height],
            mode='lines',
            line=dict(color='white', width=6),
            showlegend=False,
            hoverinfo='none'
        ))
        
        # Individual bails on each stump
        for z_pos in [-0.2, 0, 0.2]:
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_pos],
                y=[z_pos - bail_length/2, z_pos + bail_length/2],
                z=[stump_height + 0.01, stump_height + 0.01],
                mode='lines',
                line=dict(color='white', width=4),
                showlegend=False,
                hoverinfo='none'
            ))

    # Animation frames
    frames = [go.Frame(
        data=[
            go.Scatter3d(
                x=df['x (m)'][:i+1],
                y=df['z (m)'][:i+1],
                z=df['y (m)'][:i+1],
                customdata=(df['v (m/s)'][:i+1] * 3.6),
                hovertemplate=(
                    "x: %{x:.2f}m<br>z: %{y:.2f}m<br>y: %{z:.2f}m<br>" +
                    "Speed: %{customdata:.1f} km/h<extra></extra>"
                )
            ),
            go.Scatter3d(
                x=[df['x (m)'][i]],
                y=[df['z (m)'][i]],
                z=[df['y (m)'][i]],
                marker=dict(
                    size=8,
                    color='yellow',
                    symbol='circle'
                )
            )
        ],
        name=f"{df['time (s)'][i]:.2f}s"
    ) for i in range(0, len(df), max(1, len(df)//50))]

    fig.frames = frames

    # Camera presets and layout
    camera_presets = {
        "default": dict(eye=dict(x=1.5, y=1.5, z=0.8)),
        "side_view": dict(eye=dict(x=0.1, y=2.5, z=0.5)),
        "bowler_view": dict(eye=dict(x=-2, y=0, z=1.5)),
        "batsman_view": dict(eye=dict(x=3, y=0, z=1.5))
    }

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                buttons=[
                    dict(label="▶ Play", method="animate", args=[None, {
                        "frame": {"duration": 30, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 0}
                    }]),
                    dict(label="❚❚ Pause", method="animate", args=[[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate",
                        "transition": {"duration": 0}
                    }])
                ],
                x=0.1, y=0, xanchor='left', yanchor='bottom'
            ),
            dict(
                type="dropdown",
                buttons=[
                    dict(label="Default View", method="relayout", args=["scene.camera", camera_presets["default"]]),
                    dict(label="Side View", method="relayout", args=["scene.camera", camera_presets["side_view"]]),
                    dict(label="Bowler's View", method="relayout", args=["scene.camera", camera_presets["bowler_view"]]),
                    dict(label="Batsman's View", method="relayout", args=["scene.camera", camera_presets["batsman_view"]]),
                ],
                x=0.4, y=0, xanchor='left', yanchor='bottom'
            )
        ],
        scene=dict(
            xaxis_title="Down Pitch (m)",
            yaxis_title="Lateral (m)",
            zaxis_title="Height (m)",
            aspectratio=dict(x=2, y=0.3, z=0.15),
            xaxis=dict(range=[0, pitch_length + 5]),
            yaxis=dict(range=[-pitch_width, pitch_width]),
            zaxis=dict(range=[0, 3]),
            camera=camera_presets["default"]
        ),
        title=dict(
            text=f"<b>Cricket Ball Trajectory</b><br>Initial Speed: {params['v0']:.1f}m/s" if params else "Cricket Ball Trajectory",
            x=0.5,
            xanchor='center'
        ),
        margin=dict(l=0, r=0, b=0, t=80),
        height=700
    )

    if output_file:
        fig.write_html(output_file, auto_play=False)
    
    return fig

def load_simulation_data(sim_id):
    """Load simulation CSV with metadata"""
    try:
        with open(f"simulations/logs/sim_{sim_id:04d}.csv") as f:
            header = f.readline().strip()[2:]  # Remove '# '
            params = dict(item.split('=') for item in header.split(', '))
            params = {k: float(v) for k, v in params.items()}
            df = pd.read_csv(f)
        return params, df
    except FileNotFoundError:
        print(f"Error: Simulation file for ID {sim_id} not found")
        return {}, pd.DataFrame()
    except Exception as e:
        print(f"Error loading simulation data: {str(e)}")
        return {}, pd.DataFrame()