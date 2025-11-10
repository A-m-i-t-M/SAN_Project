# energy_manager.py
class EnergyManager:
    """
    Energy-aware placement: we mark some nodes as 'low_power' where cold data should be stored.
    This is a simple policy interface used by the controller to decide where to place cold stripes.
    """
    def __init__(self, nodes, low_power_node_ids=None):
        self.nodes = nodes
        self.low_power_node_ids = set(low_power_node_ids or [])

    def choose_cold_node(self, stripe_id):
        """Return a low-power node for cold stripe storage (round-robin)."""
        if not self.low_power_node_ids:
            # no low-power preference, fallback to first node
            return self.nodes[0]
        # simple deterministic pick
        list_ids = sorted(list(self.low_power_node_ids))
        pick = list_ids[ stripe_id % len(list_ids) ]
        # return Node object with id == pick
        for n in self.nodes:
            if n.id == pick:
                return n
        return self.nodes[0]
