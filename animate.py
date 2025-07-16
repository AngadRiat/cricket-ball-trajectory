import argparse
from utils import load_simulation_data, create_animation

def main():
    parser = argparse.ArgumentParser(description="View cricket ball animation")
    parser.add_argument("sim_id", type=int, help="Simulation ID (0-999)")
    parser.add_argument("--output", help="HTML file to save animation")
    args = parser.parse_args()

    params, df = load_simulation_data(args.sim_id)
    fig = create_animation(df, params, args.output)
    fig.show()

if __name__ == "__main__":
    main()