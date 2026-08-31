class Validator:
    @staticmethod
    def validate_node_id(node_id):
        if node_id is None:
            return

        if not isinstance(node_id, int):
            raise TypeError(f"Node ID must be an integer, got {type(node_id).__name__}")

        if node_id < 0:
            raise ValueError(f"Node ID must be positive, got {node_id}")

    @staticmethod
    def validate_network_size(n):
        if not isinstance(n, int):
            raise TypeError(f"Network size must be an integer, got {type(n).__name__}")

        if n < 3:
            raise ValueError(f"A cycle graph requires at least 3 nodes, got {n}")
