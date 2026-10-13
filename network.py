import math
import random
from typing import Callable, List, Optional, Sequence

from node import Node
from utils import bits
from validator import Validator as V


def log_star(x) -> int:
    """Smallest k such that log2 applied k times to x gives a value <= 1."""
    k = 0
    while x > 1:
        x = math.log2(x)
        k += 1
    return k


def cole_vishkin_palette_schedule(id_space: int) -> List[int]:
    """Palette size before each Cole-Vishkin round, plus the final size.

    Depends only on the ID-space bound N, which every node knows, so all nodes
    agree on when to stop without any global inspection of the network.
    len(result) - 1 is the number of Cole-Vishkin rounds. The last entry is
    exactly 6 whenever N > 6 (6 is the fixed point of the recurrence below);
    for N <= 6 the schedule is empty and the last entry is just N itself.
    """
    sizes = [id_space]
    palette = id_space
    while palette > 6:
        palette = 2 * (palette - 1).bit_length()
        sizes.append(palette)
    return sizes


class CycleNetwork:
    """Synchronous LOCAL-model simulation on an oriented n-cycle.

    Node i's successor is node (i+1) mod n; every node can tell its
    successor port from its predecessor port (a consistent orientation).
    """

    def __init__(
        self,
        size: int,
        id_space: Optional[int] = None,
        anonymous: bool = False,
        seed: Optional[int] = None,
        ids: Optional[Sequence[int]] = None,
    ):
        V.validate_network_size(size)
        if id_space is None:
            id_space = size ** 3  # polynomial ID space, the standard LOCAL assumption
        V.validate_id_space(id_space, size)

        self.size = size
        self.id_space = id_space
        self.anonymous = anonymous
        self._rng = random.Random(seed)

        self.cycle: List[Node] = []
        self._build_cycle(anonymous, ids)

        # metrics
        self.palette_size = id_space
        self.rounds_executed = 0
        self.message_complexity = 0        # number of messages sent
        self.message_bits = 0              # total bits sent
        self.node_local_state_size_track = []  # peak per-node state bits, one entry per round

    # ---- construction ------------------------------------------------------
    def _draw_unique_ids(self) -> List[int]:
        n, N = self.size, self.id_space
        if N < 2 ** 62:
            return self._rng.sample(range(N), n)
        ids = set()
        while len(ids) < n:
            ids.add(self._rng.randrange(N))
        ids = list(ids)
        self._rng.shuffle(ids)
        return ids

    def _build_cycle(self, anonymous: bool, ids: Optional[Sequence[int]]):
        if anonymous:
            self.cycle = [Node(None) for _ in range(self.size)]
            return
        if ids is None:
            ids = self._draw_unique_ids()
        else:
            ids = list(ids)
            if len(ids) != self.size:
                raise ValueError("Number of IDs must equal the network size")
            V.validate_unique_ids(ids)
            if max(ids) >= self.id_space:
                raise ValueError("Every ID must be smaller than id_space")
        self.cycle = [Node(i) for i in ids]

    # ---- read-only helpers -------------------------------------------------
    @property
    def colors(self) -> List[int]:
        return [node.color for node in self.cycle]

    @property
    def is_proper(self) -> bool:
        return V.is_proper_coloring(self.colors)

    def verify(self):
        """Raise if the current colors are not a proper coloring with <= 3 colors."""
        V.validate_proper_coloring(self.colors, max_colors=3)

    def view(self, i: int, radius: int) -> tuple:
        """What node i can possibly know after `radius` rounds: the IDs within
        `radius` hops, in orientation order."""
        n = self.size
        return tuple(self.cycle[(i + d) % n].id for d in range(-radius, radius + 1))

    def count_distinct_views(self, radius: int) -> int:
        return len({self.view(i, radius) for i in range(self.size)})

    def all_states_identical(self) -> bool:
        return len(set(self.colors)) == 1

    # ---- full algorithm ----------------------------------------------------
    def execute_simulation(self) -> int:
        self.run_cole_vishkin_phase()
        self.run_greedy_phase()
        self.verify()
        return self.rounds_executed

    def run_cole_vishkin_phase(self):
        sizes = cole_vishkin_palette_schedule(self.id_space)
        for palette in sizes[:-1]:
            self._distribute_messages_cole_vishkin(palette)
            self._record_state()
            for node in self.cycle:
                node.reduce_color_cole_vishkin()
            self.rounds_executed += 1
        self.palette_size = sizes[-1]

    def run_greedy_phase(self):
        """Colors 5, 4, 3 (or fewer) are removed one per round. Nodes holding the
        same color are never adjacent, so they can recolor simultaneously.
        self.palette_size is passed to every round below as the bit-cost of a
        message, even though the live max color shrinks round over round; this
        over-counts message_bits slightly in later rounds (documented in README)."""
        for target in range(self.palette_size - 1, 2, -1):
            self._distribute_messages_greedy(self.palette_size)
            self._record_state()
            for node in self.cycle:
                if node.color == target:
                    node.reduce_color_greedy()
                else:
                    node.skip_round()
            self.rounds_executed += 1
        self.palette_size = min(self.palette_size, 3)

    # ---- generic deterministic rules (used for the anonymous-cycle demo) ----
    def run_generic_rounds(self, rule: Callable[[int, int, int], int], rounds: int, palette: int = 8):
        for _ in range(rounds):
            self._distribute_messages_greedy(palette)
            self._record_state()
            for node in self.cycle:
                node.apply_rule(rule)
            self.rounds_executed += 1

    # ---- message passing ---------------------------------------------------
    def _record_state(self):
        self.node_local_state_size_track.append(max(node.state_bits for node in self.cycle))

    def _distribute_messages_cole_vishkin(self, palette: int):
        frozen_colors = self.colors
        for i, node in enumerate(self.cycle):
            node.receive_message_cole_vishkin(frozen_colors[(i + 1) % self.size])
        self.message_complexity += self.size
        self.message_bits += self.size * bits(palette - 1)

    def _distribute_messages_greedy(self, palette: int):
        frozen_colors = self.colors
        for i, node in enumerate(self.cycle):
            node.receive_message_greedy(frozen_colors[(i + 1) % self.size], frozen_colors[i - 1])
        self.message_complexity += 2 * self.size
        self.message_bits += 2 * self.size * bits(palette - 1)
