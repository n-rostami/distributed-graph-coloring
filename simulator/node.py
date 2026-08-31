from validator import Validator as V


class Node:
    def __init__(self, node_id: int):
        V.validate_node_id(node_id)
        self._color = node_id
        self._successor_color = None

    def send_message(self) -> int:
        return self._color

    def receive_message(self, successor_color: int):
        V.validate_node_id(successor_color)
        self._successor_color = successor_color

    def update(self):
        if self._successor_color is None:
            raise ValueError("Cannot reduce color: successor color was not received.")

        diff = self._color ^ self._successor_color

        index = (diff & -diff).bit_length() - 1

        b = (self._color >> index) & 1

        self._color = 2 * index + b

        self._successor_color = None
