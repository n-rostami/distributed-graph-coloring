import random
from node import Node
from validator import Validator as V


class CycleNetwork:
    def __init__(self, size: int, initial_color_range: int):
        V.validate_network_size(size)

        self.size = size
        self.cycle = []
        self._build_cycle(initial_color_range)
        self.rounds_executed = 0

    @property
    def max_color(self) -> int:
        return max(node.color for node in self.cycle) + 1

    def _build_cycle(self, initial_color_range: int):
        initial_colors = random.sample(range(0, initial_color_range), self.size)
        self.cycle = [Node(c) for c in initial_colors]

    def execute_simulation(self) -> int:
        self.run_cole_vishkin_phase()
        self.run_greedy_phase()

        return self.rounds_executed

    def run_cole_vishkin_phase(self):
        while self.max_color >= 6:
            self._distribute_messages_cole_vishkin()
            for node in self.cycle:
                node.reduce_color_cole_vishkin()

            self.rounds_executed += 1

    def run_greedy_phase(self):
        while (current_max := (self.max_color - 1)) > 2:
            self._distribute_messages_greedy()

            for node in self.cycle:
                if node.color == current_max:
                    node.reduce_color_greedy()
                else:
                    node.skip_round()

            self.rounds_executed += 1

    def _distribute_messages_cole_vishkin(self):
        frozen_colors = [node.color for node in self.cycle]

        for i, node in enumerate(self.cycle):
            succ_color = frozen_colors[(i + 1) % self.size]
            node.receive_message_cole_vishkin(succ_color)

    def _distribute_messages_greedy(self):
        frozen_colors = [node.color for node in self.cycle]

        for i, node in enumerate(self.cycle):
            succ_color = frozen_colors[(i + 1) % self.size]
            pred_color = frozen_colors[i - 1]
            node.receive_message_greedy(succ_color, pred_color)
