import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def clean_latency_column(df):
    # Convert column to numeric, force errors to NaN
    df['latency_ms'] = pd.to_numeric(df['latency_ms'], errors='coerce')
    # Drop rows where latency is NaN (original ERR values)
    df = df.dropna(subset=['latency_ms'])
    return df

def plot_latency_cdf(df, outfile):
    vals = np.sort(df['latency_ms'].values)
    p = np.arange(len(vals)) / float(len(vals))

    plt.figure(figsize=(7,5))
    plt.plot(vals, p)
    plt.xlabel("Latency (ms)")
    plt.ylabel("CDF")
    plt.title("Latency CDF")
    plt.grid(True)
    plt.savefig(outfile)
    plt.close()
    print(f"[+] Saved CDF plot: {outfile}")

def print_stats(df):
    ops = len(df)
    avg_lat = df['latency_ms'].mean()
    p95 = df['latency_ms'].quantile(0.95)
    p99 = df['latency_ms'].quantile(0.99)

    print(f"Ops: {ops}")
    print(f"Avg latency (ms): {avg_lat}")
    print(f"P95 (ms): {p95}")
    print(f"P99 (ms): {p99}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analysis/plot_results.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    df = pd.read_csv(csv_file)

    df = clean_latency_column(df)
    print_stats(df)
    plot_latency_cdf(df, outfile=csv_file.replace(".csv", "_latency_cdf.png"))
