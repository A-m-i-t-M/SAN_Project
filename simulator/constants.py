# constants.py
BLOCK_SIZE = 4096              # block size in bytes (4KB)
BLOCKS_PER_STRIPE = 4          # number of data blocks per stripe (k)
PARITY_BLOCKS = 1              # number of parity blocks (r) => RAID5 style
STRIPE_SIZE = BLOCKS_PER_STRIPE * BLOCK_SIZE
DEFAULT_NUM_NODES = 6
LOG_FORMAT = "{time},{mode},{op},{latency_ms},{bytes},{stripe},{node_id}"