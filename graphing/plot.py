import matplotlib.pyplot as plt
from datetime import datetime
from config.settings import SLASHING_WINDOW

def plot_missed_blocks(history, output_path="missed_blocks.png"):
    """
    Generate a plot of missed blocks within the slashing window over time.
    Args:
        history: Dict with 'missed_blocks' and 'timestamps' lists or deques.
        output_path: Where to save the plot (default: 'missed_blocks.png').
    Returns:
        Path to the saved plot.
    """
    timestamps = [datetime.fromtimestamp(ts) for ts in history["timestamps"]]
    missed_blocks = list(history["missed_blocks"])

    if not timestamps or not missed_blocks:
        print("No data available to plot.")
        return None

    # Set dark theme
    plt.style.use("dark_background")
    plt.figure(figsize=(10, 6), facecolor="black")
    ax = plt.gca()
    ax.set_facecolor("black")

    # Plot missed blocks with orange line
    plt.plot(timestamps, missed_blocks, label="Missed Blocks", color="orange", marker="o", linewidth=2)
    plt.axhline(y=SLASHING_WINDOW * 0.20, color="white", linestyle="--", label="20% Slashing Threshold")

    # Customize text and grid
    plt.title("Missed Blocks Over Time (Slashing Window)", color="white")
    plt.xlabel("Time", color="white")
    plt.ylabel(f"Missed Blocks (Window: {SLASHING_WINDOW})", color="white")
    plt.legend(facecolor="black", edgecolor="white", labelcolor="white")
    plt.grid(True, color="gray", linestyle="--", alpha=0.3)
    plt.xticks(rotation=45, color="white")
    plt.yticks(color="white")

    plt.tight_layout()
    plt.savefig(output_path, facecolor="black")
    plt.close()
    return output_path
