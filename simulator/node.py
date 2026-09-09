from validator import Validator as V


class Node:
    def __init__(self, node_id: int):
        V.validate_node_id(node_id)

        self._color = node_id
        self._inbox_succ = None
        self._inbox_pred = None

    @property
    def color(self) -> int:
        return self._color

    def receive_message_cole_vishkin(self, succ_color: int):
        V.validate_node_id(succ_color)

        self._inbox_succ = succ_color

    def receive_message_greedy(self, succ_color: int, pred_color: int):
        V.validate_node_id(succ_color)
        V.validate_node_id(pred_color)

        self._inbox_succ = succ_color
        self._inbox_pred = pred_color

    def reduce_color_cole_vishkin(self):
        if self._inbox_succ is None:
            raise ValueError("Execution failed: Inbox missing successor message.")

        diff = self._color ^ self._inbox_succ
        index = (diff & -diff).bit_length() - 1
        b = (self._color >> index) & 1

        self._color = 2 * index + b
        self._clear_buffers()

    def reduce_color_greedy(self):
        if self._inbox_pred is None or self._inbox_succ is None:
            raise ValueError("Execution failed: Incomplete neighborhood state.")

        for c in range(3):
            if c != self._inbox_succ and c != self._inbox_pred:
                self._color = c
                break

        self._clear_buffers()

    def _clear_buffers(self):
        self._inbox_pred = None
        self._inbox_succ = None

    def skip_round(self):
        self._clear_buffers()
