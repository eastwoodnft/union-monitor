import matplotlib.pyplot as plt
import os
from datetime import datetime
from config.settings import SLASHING_WINDOW

def plot_missed_blocks(history, output_path="missed_blocks.png"):
    """
    Generate a plot of missed blocks within the slashing window over time.
    Args:
        history: Dict with 'missed_blocks' and 'timestamps' deques.
        output_path: Where to save the plot (default: 'missed_blocks.png').
    Returns:
        Path to the saved plot.
    """
    timestamps = [datetime.fromtimestamp(ts) for ts in history["timestamps"]]
    missed_blocks = list(history["missed_blocks"])

    if not timestamps or not missed_blocks:
        print("No data available to plot.")
        return None

    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, missed_blocks, label="Missed Blocks", color="red", marker="o")
    plt.axhline(y=SLASHING_WINDOW * 0.20, color="orange", linestyle="--", label="20% Slashing Threshold")
    plt.title("Missed Blocks Over Time (Slashing Window)")
    plt.xlabel("Time")
    plt.ylabel(f"Missed Blocks (Window: {SLASHING_WINDOW})")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot
    plt.savefig(output_path)
    plt.close()
    return output_path
