# parity.py
def xor_parity(blocks: list[bytes]) -> bytes:
    """Return XOR parity of equal-length blocks."""
    if len(blocks) == 0:
        return b""
    length = len(blocks[0])
    # pad/truncate to same length
    blocks = [b.ljust(length, b'\x00')[:length] for b in blocks]
    result = bytearray(length)
    for b in blocks:
        for i, val in enumerate(b):
            result[i] ^= val
    return bytes(result)
