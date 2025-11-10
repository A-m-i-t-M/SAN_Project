# node.py
import os
from pathlib import Path
from threading import Lock
from simulator.constants import BLOCK_SIZE
import time

class Node:
    def __init__(self, node_id, base_dir, network: 'NetworkSimulator'):
        self.id = node_id
        self.base_dir = Path(base_dir) / f"node_{node_id}"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.network = network
        self.alive = True
        self.lock = Lock()

    def chunk_path(self, chunk_id: str):
        return self.base_dir / f"{chunk_id}.chk"

    def write_chunk(self, chunk_id: str, data: bytes):
        if not self.alive:
            raise RuntimeError("Node is down")
        # simulate network transfer
        self.network.simulate_send(len(data))
        with self.lock:
            with open(self.chunk_path(chunk_id), "wb") as f:
                f.write(data)

    def read_chunk(self, chunk_id: str) -> bytes:
        if not self.alive:
            raise RuntimeError("Node is down")
        p = self.chunk_path(chunk_id)
        if not p.exists():
            raise FileNotFoundError(chunk_id)
        self.network.simulate_small()
        with self.lock:
            with open(p, "rb") as f:
                return f.read()

    def delete_chunk(self, chunk_id: str):
        p = self.chunk_path(chunk_id)
        if p.exists():
            p.unlink()

    def list_chunks(self):
        return [f.stem for f in self.base_dir.glob("*.chk")]

    def fail(self):
        self.alive = False

    def recover(self):
        self.alive = True
