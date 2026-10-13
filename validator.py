from typing import Optional, Sequence


class Validator:
    """Input and output checks shared by the simulator."""

    @staticmethod
    def validate_node_id(node_id: Optional[int]):
        if node_id is None:  # anonymous node
            return
        if isinstance(node_id, bool) or not isinstance(node_id, int):
            raise TypeError(f"Node ID must be an integer, got {type(node_id).__name__}")
        if node_id < 0:
            raise ValueError(f"Node ID must be non-negative, got {node_id}")

    @staticmethod
    def validate_network_size(n):
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError(f"Network size must be an integer, got {type(n).__name__}")
        if n < 3:
            raise ValueError(f"A cycle graph requires at least 3 nodes, got {n}")

    @staticmethod
    def validate_id_space(id_space: int, size: int):
        if isinstance(id_space, bool) or not isinstance(id_space, int):
            raise TypeError(f"ID space must be an integer, got {type(id_space).__name__}")
        if id_space < size:
            raise ValueError(
                f"ID space ({id_space}) must be at least the network size ({size}) "
                "to give every node a unique ID"
            )

    @staticmethod
    def validate_unique_ids(ids: Sequence[int]):
        if len(set(ids)) != len(ids):
            raise ValueError("Node IDs must be unique")

    @staticmethod
    def is_proper_coloring(colors: Sequence[int]) -> bool:
        """True iff no two cyclically adjacent nodes share a color."""
        n = len(colors)
        return all(colors[i] != colors[(i + 1) % n] for i in range(n))

    @staticmethod
    def validate_proper_coloring(colors: Sequence[int], max_colors: Optional[int] = None):
        n = len(colors)
        for i in range(n):
            if colors[i] == colors[(i + 1) % n]:
                raise ValueError(
                    f"Improper coloring: nodes {i} and {(i + 1) % n} both have color {colors[i]}"
                )
        if max_colors is not None and len(set(colors)) > max_colors:
            raise ValueError(
                f"Coloring uses {len(set(colors))} colors, expected at most {max_colors}"
            )
