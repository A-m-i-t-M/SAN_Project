# network.py
import random
import time

class NetworkSimulator:
    """
    Simple network delay model. Keep calls fast (no huge sleep).
    You can scale down time by 'scale' to accelerate experiments.
    """
    def __init__(self, base_ms=1.0, jitter_ms=0.5, bw_mbps=100.0, time_scale=0.001):
        self.base_ms = base_ms
        self.jitter_ms = jitter_ms
        self.bw_mbps = bw_mbps
        # time_scale multiplies real sleep time so experiments don't take too long;
        # e.g., time_scale=0.001 means 1ms simulated -> 1 microsecond actual.
        self.time_scale = time_scale

    def transfer_delay_sec(self, bytes_len):
        transfer_ms = (bytes_len * 8) / (self.bw_mbps * 1e6) * 1000.0
        delay_ms = self.base_ms + transfer_ms + random.uniform(0, self.jitter_ms)
        return (delay_ms / 1000.0) * self.time_scale

    def small_delay_sec(self):
        delay_ms = random.uniform(0, self.jitter_ms)
        return (delay_ms / 1000.0) * self.time_scale

    def simulate_send(self, bytes_len):
        time.sleep(self.transfer_delay_sec(bytes_len))

    def simulate_small(self):
        time.sleep(self.small_delay_sec())
