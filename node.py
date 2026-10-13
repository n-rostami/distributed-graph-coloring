from typing import Callable, Optional

from utils import bits
from validator import Validator as V


class SymmetryBreakingError(RuntimeError):
    """Raised when a rule needs to tell two nodes apart but they are identical."""


class Node:
    """A single computational agent on an oriented cycle.

    A node only ever sees what arrives in its inboxes (colors of its
    successor / predecessor). It has no access to the network object.
    An anonymous node has ``node_id = None`` and starts in state 0, so all
    anonymous nodes are literally identical.
    """

    def __init__(self, node_id: Optional[int] = None):
        V.validate_node_id(node_id)
        self._id = node_id
        self._color = node_id if node_id is not None else 0
        self._inbox_succ = None
        self._inbox_pred = None

    # ---- read-only views -------------------------------------------------
    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def color(self) -> int:
        return self._color

    @property
    def is_anonymous(self) -> bool:
        return self._id is None

    @property
    def state_bits(self) -> int:
        """Bits needed to store the current color plus whatever is in the inboxes."""
        return bits(self._color) + bits(self._inbox_succ) + bits(self._inbox_pred)

    # ---- communication ---------------------------------------------------
    def receive_message_cole_vishkin(self, succ_color: int):
        V.validate_node_id(succ_color)
        self._inbox_succ = succ_color

    def receive_message_greedy(self, succ_color: int, pred_color: int):
        V.validate_node_id(succ_color)
        V.validate_node_id(pred_color)
        self._inbox_succ = succ_color
        self._inbox_pred = pred_color

    # ---- local computation -----------------------------------------------
    def _require_inbox(self, succ: bool = False, pred: bool = False):
        """Raise if a message this method needs hasn't arrived yet."""
        if succ and self._inbox_succ is None:
            raise ValueError("Execution failed: Inbox missing successor message.")
        if pred and self._inbox_pred is None:
            raise ValueError("Execution failed: Inbox missing predecessor message.")

    def reduce_color_cole_vishkin(self):
        """New color = 2*i + b, i = lowest bit where I differ from my successor,
        b = my own value of that bit. Maps k-bit colors to colors < 2k."""
        self._require_inbox(succ=True)

        diff = self._color ^ self._inbox_succ
        if diff == 0:
            raise SymmetryBreakingError(
                "Cole-Vishkin needs a bit where I differ from my successor, "
                "but our colors are identical (anonymous / improperly colored input)."
            )
        index = (diff & -diff).bit_length() - 1
        b = (self._color >> index) & 1

        self._color = 2 * index + b
        self._clear_buffers()

    def reduce_color_greedy(self):
        """Pick the smallest color in {0,1,2} unused by both neighbors."""
        self._require_inbox(succ=True, pred=True)

        for c in range(3):
            if c != self._inbox_succ and c != self._inbox_pred:
                self._color = c
                break

        self._clear_buffers()

    def apply_rule(self, rule: Callable[[int, int, int], int]):
        """Apply an arbitrary deterministic rule f(own, succ, pred) -> new state."""
        self._require_inbox(succ=True, pred=True)
        self._color = rule(self._color, self._inbox_succ, self._inbox_pred)
        self._clear_buffers()

    def skip_round(self):
        self._clear_buffers()

    def _clear_buffers(self):
        self._inbox_pred = None
        self._inbox_succ = None
