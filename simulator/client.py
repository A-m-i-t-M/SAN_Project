# client.py
import os
import random
import time
from simulator.constants import BLOCK_SIZE, BLOCKS_PER_STRIPE
import numpy as np

def random_block(seed=None):
    # return BLOCK_SIZE bytes (pseudo-random)
    if seed is not None:
        random.seed(seed)
    return os.urandom(BLOCK_SIZE)

class WorkloadGenerator:
    """
    Workload generator that yields (op, stripe_id, data_index, data_bytes).
    op: 'read' or 'write'
    Supports modes: random, seq, zipf (hotspot).
    """
    def __init__(self, mode="zipf", stripes=1000, zipf_s=1.2, hot_fraction=0.1):
        self.mode = mode
        self.stripes = stripes
        self.zipf_s = zipf_s
        self.hot_fraction = hot_fraction
        # precompute hot stripes
        self.hot_count = max(1, int(stripes * hot_fraction))
        self.hot_stripes = list(range(self.hot_count))
        # Zipf generator (numpy)
        if self.mode == "zipf":
            ranks = np.arange(1, stripes+1)
            weights = 1 / np.power(ranks, self.zipf_s)
            self.p = weights / weights.sum()

    def next_op(self):
        op = 'read' if random.random() < 0.7 else 'write'
        if self.mode == "random":
            stripe = random.randint(0, self.stripes - 1)
        elif self.mode == "seq":
            stripe = random.randint(0, self.stripes - 1)  # could be improved
        else:  # zipf
            stripe = np.random.choice(self.stripes, p=self.p)
        data_index = random.randint(0, BLOCKS_PER_STRIPE - 1)
        data = random_block()
        return op, int(stripe), int(data_index), data
