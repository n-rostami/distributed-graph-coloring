from typing import Optional


def bits(x: Optional[int]) -> int:
    """Bits needed to write down a non-negative integer (at least 1 bit).

    ``None`` (an empty inbox, or an anonymous node's absent ID) costs 0 bits.
    Used for both the state-size and message-size metrics, so there is a
    single definition of "how many bits does this value cost" shared by
    Node and CycleNetwork.
    """
    return 0 if x is None else max(1, x.bit_length())
