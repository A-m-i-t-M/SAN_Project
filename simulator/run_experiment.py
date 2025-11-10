# run_experiment.py
import os
import argparse
import time
import csv
from simulator.network import NetworkSimulator
from simulator.node import Node
from simulator.controller import Controller
from simulator.client import WorkloadGenerator
from simulator.predictor import HotStripePredictor
from simulator.energy_manager import EnergyManager
from simulator.constants import LOG_FORMAT
from tqdm import trange

LOGFILE = "experiment_log.csv"

def setup_nodes(base_dir, num_nodes, network):
    nodes = []
    for i in range(num_nodes):
        nodes.append(Node(i, base_dir, network))
    return nodes

def clear_node_dirs(base_dir):
    if os.path.exists(base_dir):
        # remove existing files carefully
        for entry in os.scandir(base_dir):
            if entry.is_dir():
                for f in os.scandir(entry.path):
                    os.remove(f.path)
    else:
        os.makedirs(base_dir, exist_ok=True)

def time_ms():
    return int(time.time() * 1000)

def run(mode="baseline", duration=30, num_nodes=6, stripes=200, logpath=LOGFILE, seed=42):
    random_seed = seed
    import random, numpy as np
    random.seed(random_seed)
    np.random.seed(random_seed)

    base_dir = "./data_nodes"
    clear_node_dirs(base_dir)

    network = NetworkSimulator(base_ms=1.0, jitter_ms=0.5, bw_mbps=200.0, time_scale=0.002)
    nodes = setup_nodes(base_dir, num_nodes, network)
    controller = Controller(nodes, network)
    workload = WorkloadGenerator(mode="zipf", stripes=stripes, zipf_s=1.2, hot_fraction=0.1)

    predictor = HotStripePredictor(window_size=300, threshold=15)
    energy_mgr = EnergyManager(nodes, low_power_node_ids=[n.id for n in nodes[-2:]])  # last 2 nodes low-power

    # prepare log
    with open(logpath, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["time_ms","mode","op","latency_ms","bytes","stripe","node_id","extra"])

    start_ts = time.time()
    ops = 0

    try:
        # steady stream of ops until duration reached
        while time.time() - start_ts < duration:
            op, stripe_id, data_index, data = workload.next_op()
            ts0 = time.time()
            bytes_len = len(data)
            extra = ""
            # if mode includes energy-aware and stripe is cold, place parity on low-power node
            if mode == "baseline":
                # baseline: central controller writes everything to node0 (simulate local RAID)
                # For baseline we do central write (not distributed)
                try:
                    node = nodes[0]
                    node.write_chunk(f"baseline_{stripe_id}_{data_index}", data)
                    latency_ms = (time.time() - ts0) * 1000.0
                    with open(logpath, "a") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([time_ms(), mode, op, f"{latency_ms:.3f}", bytes_len, stripe_id, node.id, ""])
                except Exception as e:
                    with open(logpath, "a") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([time_ms(), mode, op, "ERR", bytes_len, stripe_id, -1, str(e)])
            else:
                # dRAID modes:
                # if it's a write -> write full stripe (simulate writing all k blocks)
                try:
                    if op == "write":
                        # create k blocks for stripe
                        data_blocks = [os.urandom(4096) for _ in range(4)]
                        # energy-aware: if mode includes 'energy' and stripe is cold, choose cold node
                        if mode == "draid_predict_energy":
                            # simple heuristics: if not hot (predictor says not hot) we store parity/cold on low-power
                            if not predictor.is_hot(stripe_id):
                                cold_node = energy_mgr.choose_cold_node(stripe_id)
                                extra = f"cold_to_node{cold_node.id}"
                        controller.write_stripe(stripe_id, data_blocks)
                        latency_ms = (time.time() - ts0) * 1000.0
                        with open(logpath, "a") as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow([time_ms(), mode, "write_stripe", f"{latency_ms:.3f}", 4096*4, stripe_id, -1, extra])
                        # predictor observe after write
                        predictor.observe(stripe_id)
                        # if stripe is hot and predictor marks hot and we're in mode==predict_energy, relocate
                        if mode == "draid_predict_energy" and predictor.is_hot(stripe_id):
                            # relocation: copy stripe to node0 (fast node) as cache
                            # NOTE: for simplicity we pick node 0 as hot cache
                            cache_node = nodes[0]
                            # we will copy existing blocks from their nodes (simulate read + write)
                            data_nodes, parity_nodes = controller.stripe_nodes(stripe_id)
                            try:
                                for i, n in enumerate(data_nodes):
                                    b = n.read_chunk(f"stripe{stripe_id}_d{i}")
                                    cache_node.write_chunk(f"stripe{stripe_id}_hot_d{i}", b)
                                # Mark relocation mapping
                                controller.relocations[stripe_id] = cache_node.id
                                with open(logpath, "a") as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow([time_ms(), mode, "relocate", 0, 0, stripe_id, cache_node.id, "relocated"])
                            except Exception as e:
                                # ignore relocation failures for this lightweight sim
                                pass

                    else:  # op == "read"
                        # decide where to route read: if relocated present -> read from cache node
                        if stripe_id in controller.relocations:
                            cache_id = controller.relocations[stripe_id]
                            node = next(n for n in nodes if n.id == cache_id)
                            # read one block
                            try:
                                _ = node.read_chunk(f"stripe{stripe_id}_hot_d{data_index}")
                                latency_ms = (time.time() - ts0)*1000.0
                                with open(logpath, "a") as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow([time_ms(), mode, "read_hot", f"{latency_ms:.3f}", 4096, stripe_id, node.id, "hit"])
                                predictor.observe(stripe_id)
                            except Exception:
                                # fallback to dRAID read
                                b = controller.read_block(stripe_id, data_index)
                                latency_ms = (time.time() - ts0)*1000.0
                                with open(logpath, "a") as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow([time_ms(), mode, "read", f"{latency_ms:.3f}", 4096, stripe_id, -1, "fallback"])
                                predictor.observe(stripe_id)
                        else:
                            # read from mapped node
                            try:
                                _ = controller.read_block(stripe_id, data_index)
                                latency_ms = (time.time() - ts0)*1000.0
                                with open(logpath, "a") as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow([time_ms(), mode, "read", f"{latency_ms:.3f}", 4096, stripe_id, -1, ""])
                                predictor.observe(stripe_id)
                            except Exception as e:
                                # simulate degraded read and recovery (not implemented fully)
                                with open(logpath, "a") as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow([time_ms(), mode, "read_err", "ERR", 0, stripe_id, -1, str(e)])
                except Exception as e:
                    with open(logpath, "a") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([time_ms(), mode, "op_err", "ERR", 0, stripe_id, -1, str(e)])
            ops += 1
    except KeyboardInterrupt:
        print("Interrupted.")
    finally:
        print(f"Finished. ops={ops}, log={logpath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["baseline","draid","draid_predict_energy"], default="draid")
    parser.add_argument("--duration", type=int, default=20, help="seconds")
    parser.add_argument("--nodes", type=int, default=6)
    parser.add_argument("--stripes", type=int, default=200)
    parser.add_argument("--log", type=str, default=LOGFILE)
    args = parser.parse_args()
    run(mode=args.mode, duration=args.duration, num_nodes=args.nodes, stripes=args.stripes, logpath=args.log)
