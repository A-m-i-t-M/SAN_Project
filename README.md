# dRAID: Disaggregated RAID with Predictive and Energy‑Aware Optimization

A lightweight simulator that demonstrates how disaggregation + smart scheduling can improve storage performance and efficiency. It includes a baseline RAID-like flow and two enhancements:

- Predictive hot‑stripe detection (ML‑flavored heuristic)
- Energy‑aware node selection for colder data paths

The goal: better latency consistency, solid throughput, and lower energy usage across storage operations.

---

## Project layout

```
SAN_Project/
├─ simulator/                 # Core simulator modules
│  ├─ run_experiment.py       # Entry point (module runnable)
│  ├─ controller.py           # Stripe placement, relocations
│  ├─ network.py              # Network timing & bandwidth model
│  ├─ node.py                 # Node I/O API (read/write chunks)
│  ├─ parity.py               # Parity helpers (k/p layout)
│  ├─ energy_manager.py       # Low‑power node selection heuristics
│  ├─ predictor.py            # Hot‑stripe predictor (window + threshold)
│  ├─ client.py               # Workload generator (Zipf, hot fraction)
│  └─ constants.py            # Shared constants
│
├─ analysis/
│  └─ plot_results.py         # Stats + latency CDF plotter
│
├─ experiments/               # CSV logs and workload traces
│  ├─ baseline_log.csv
│  ├─ draid_log.csv
│  ├─ draid_predict_energy_log.csv
│  └─ workloads.py            # (Optional) workload snippets
│
├─ data_nodes/                # Runtime data folders per node (generated/cleared)
├─ requirements.txt
├─ README.md
└─ .gitignore
```

---

## Quick start (Windows PowerShell)

1) Create and activate a virtual environment (optional but recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies:

```powershell
pip install -r requirements.txt
```

3) Run simulations from the project root using the module form (avoids import issues):

- Baseline RAID‑style flow
```powershell
python -m simulator.run_experiment --mode baseline --duration 20 --nodes 6 --stripes 200 --log .\experiments\baseline_log.csv
```

- dRAID (disaggregated)
```powershell
python -m simulator.run_experiment --mode draid --duration 20 --nodes 6 --stripes 200 --log .\experiments\draid_log.csv
```

- dRAID + Predictive Energy model
```powershell
python -m simulator.run_experiment --mode draid_predict_energy --duration 20 --nodes 6 --stripes 200 --log .\experiments\draid_predict_energy_log.csv
```

Each run writes a CSV with columns:
```
[time_ms, mode, op, latency_ms, bytes, stripe, node_id, extra]
```

---

## Analyze and visualize

Compute summary stats and plot a latency CDF from any produced CSV:

```powershell
python .\analysis\plot_results.py .\experiments\baseline_log.csv
python .\analysis\plot_results.py .\experiments\draid_log.csv
python .\analysis\plot_results.py .\experiments\draid_predict_energy_log.csv
```

What you get:
- Console stats: Ops count, average latency, P95, P99
- A PNG saved next to the CSV (e.g., `*_latency_cdf.png`)

Tip: If you re‑run simulations, feel free to delete or archive older CSVs in `experiments/`.

---

## How it works (at a glance)

- Workload: Zipfian access with a configurable hot fraction (`client.py`).
- Placement: Controller stripes blocks across nodes, tracks relocations (`controller.py`).
- Network: Simple latency + jitter + bandwidth model to cost I/O (`network.py`).
- Prediction: Sliding window + threshold marks hot stripes; hot data may be cached on a fast node (`predictor.py`).
- Energy‑aware: Cold stripes preferentially involve low‑power nodes (`energy_manager.py`).

Result: Hot paths get faster service, cold paths conserve energy; reads may hit the relocated hot cache when present.

---

## Example interpretation (qualitative)

| Configuration                   | Avg Latency | P95 | P99 | Stability |
|---------------------------------|-------------|-----|-----|-----------|
| Baseline RAID‑style             | Higher      | ↑   | ↑   | Low       |
| dRAID                           | Improved    | →   | →   | Good      |
| dRAID + Predictive + Energy     | Lowest      | ↓   | ↓   | Excellent |

Exact numbers depend on RNG seed, duration, and workload skew.

---

## Troubleshooting

- ModuleNotFoundError: No module named 'simulator'
  - Always run from the project root using the module form: `python -m simulator.run_experiment ...`
  - Or, as a fallback, add a small path shim at the very top of `simulator/run_experiment.py`:
    ```python
    import sys, pathlib
    if __package__ in (None, ""):
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    ```

- Plotting errors
  - Ensure `matplotlib`, `numpy`, and `pandas` are installed (use `pip install -r requirements.txt`).
  - The plotter cleans non‑numeric latencies and saves a `*_latency_cdf.png` next to your CSV.

- File permission or path issues
  - Run commands from the project root. The simulator writes under `data_nodes/` and `experiments/`.

---

## Requirements

```
numpy
pandas
matplotlib
scikit-learn
tqdm
```

Install with:
```powershell
pip install -r requirements.txt
```

---

## What to read in the code

- `simulator/run_experiment.py` – orchestration; CLI entry
- `simulator/controller.py` – stripe placement, hot relocation map
- `simulator/predictor.py` – hot‑stripe marking (window/threshold)
- `simulator/energy_manager.py` – picks low‑power nodes when appropriate
- `analysis/plot_results.py` – stats + CDF plotting

---
