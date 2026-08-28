import os
import json
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    if not os.path.exists("results/benchmark_stats.json"):
        print("Error: results/benchmark_stats.json not found. Please run ./run.sh benchmark first.")
        return

    with open("results/benchmark_stats.json", "r") as f:
        results = json.load(f)

    sns.set_theme(style="whitegrid")
    
    # We will generate a plot for each test
    for test_name, timings in results.items():
        # Clean data: convert None (crashed) to a high number or skip, we'll plot it as 0 with an annotation
        labels = []
        values = []
        colors = []
        
        # Define strict colors
        color_map = {
            "PostgreSQL (Unindexed)": "#ff9999", # Light red
            "PostgreSQL (Indexed)": "#66b3ff",   # Blue
            "Memgraph": "#99ff99"                # Green
        }
        
        for sys_name, avg_time in timings.items():
            labels.append(sys_name)
            if avg_time is None:
                values.append(0)
            else:
                values.append(avg_time)
            colors.append(color_map.get(sys_name, "gray"))

        plt.figure(figsize=(10, 6))
        
        # Create barplot
        bars = plt.bar(labels, values, color=colors)
        
        # Add labels on top of the bars
        for bar, avg_time in zip(bars, values):
            height = bar.get_height()
            if avg_time == 0:
                plt.text(bar.get_x() + bar.get_width()/2., 10,
                        'CRASHED',
                        ha='center', va='bottom', color='red', fontweight='bold')
            else:
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{avg_time:.2f} ms',
                        ha='center', va='bottom', fontweight='bold')

        plt.title(f'Execution Time: {test_name}\n(Lower is better)', fontsize=14, pad=20)
        plt.ylabel('Average Execution Time (ms)')
        
        # If the values are huge, use log scale for readability if the difference is immense
        # but linear is better for straightforward comparison unless it completely dwarfs it.
        # Let's check if the max value is > 100x the min value (excluding 0)
        non_zero = [v for v in values if v > 0]
        if non_zero and max(non_zero) > 100 * min(non_zero):
            plt.yscale('log')
            plt.ylabel('Average Execution Time (ms) - LOG SCALE')

        plt.tight_layout()
        
        # Clean filename
        safe_name = test_name.replace(" ", "_").replace(":", "").replace("(", "").replace(")", "").lower()
        filepath = f"results/plot_{safe_name}.png"
        plt.savefig(filepath)
        plt.close()
        print(f"Generated plot: {filepath}")

if __name__ == "__main__":
    main()
