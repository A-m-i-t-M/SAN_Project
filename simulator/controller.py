# controller.py
import hashlib
from simulator.constants import BLOCKS_PER_STRIPE, PARITY_BLOCKS, STRIPE_SIZE, BLOCK_SIZE
import time
import os

class Controller:
    """
    Simple controller that maps stripe_id -> nodes.
    Data layout: each stripe has k data chunks + r parity chunks placed across nodes
    in round-robin fashion starting at stripe_id % N.
    """
    def __init__(self, nodes: list, network):
        self.nodes = nodes
        self.N = len(nodes)
        self.k = BLOCKS_PER_STRIPE
        self.r = PARITY_BLOCKS
        self.network = network
        # mapping for relocated hot stripes: stripe_id -> node_id (cache node index)
        self.relocations = {}

    def stripe_nodes(self, stripe_id):
        start = stripe_id % self.N
        chosen = [self.nodes[(start + i) % self.N] for i in range(self.k + self.r)]
        return chosen[:self.k], chosen[self.k:]

    def write_stripe(self, stripe_id, data_blocks):
        # data_blocks: list of k bytes objects
        data_nodes, parity_nodes = self.stripe_nodes(stripe_id)
        # compute parity
        from simulator.parity import xor_parity
        parity = xor_parity(data_blocks)
        # write data to nodes (peer-to-peer style: instruct nodes)
        # We'll write data blocks to respective nodes then parity to first parity node
        for idx, block in enumerate(data_blocks):
            node = data_nodes[idx]
            chunk_id = f"stripe{stripe_id}_d{idx}"
            node.write_chunk(chunk_id, block)
        # parity write
        parity_node = parity_nodes[0]
        parity_chunk_id = f"stripe{stripe_id}_p0"
        parity_node.write_chunk(parity_chunk_id, parity)

    def read_block(self, stripe_id, data_index):
        # read a single data block
        data_nodes, parity_nodes = self.stripe_nodes(stripe_id)
        node = data_nodes[data_index]
        chunk_id = f"stripe{stripe_id}_d{data_index}"
        return node.read_chunk(chunk_id)

    def degrade_and_recover(self, failed_node_index, replacement_node):
        """
        Simulate degraded read & reconstruct missing chunks and write to replacement node.
        This is simplified to reconstruct all missing chunks that belonged to failed_node.
        """
        failed_node = self.nodes[failed_node_index]
        # find chunks belonging to failed node by scanning stripes (small search)
        # For simplicity, we scan all stripe ids up to some bound (user chooses)
        # In practice we'd maintain metadata—we'll reconstruct a configured range.
        # Not implemented here: caller will reconstruct specific stripe(s) by invoking recovery_stripe.
        raise NotImplementedError("Use recovery_stripe for reconstructing specific stripes")

    def recovery_stripe(self, stripe_id, missing_index, replacement_node):
        # missing_index: index in [0..k-1] of missing data chunk
        # read other data blocks and parity, reconstruct via XOR and write to replacement
        data_nodes, parity_nodes = self.stripe_nodes(stripe_id)
        blocks = []
        present_indices = []
        for idx, node in enumerate(data_nodes):
            if idx == missing_index:
                continue
            try:
                blocks.append(node.read_chunk(f"stripe{stripe_id}_d{idx}"))
                present_indices.append(idx)
            except Exception:
                # if another missing, reconstruct not possible in single parity case
                raise RuntimeError("Insufficient blocks for single parity recovery")
        # read parity
        parity = parity_nodes[0].read_chunk(f"stripe{stripe_id}_p0")
        # reconstruct = XOR of parity + other data blocks
        from simulator.parity import xor_parity
        combined = xor_parity(blocks + [parity])
        # write reconstructed into replacement_node
        chunk_id = f"stripe{stripe_id}_d{missing_index}"
        replacement_node.write_chunk(chunk_id, combined)
        return True
