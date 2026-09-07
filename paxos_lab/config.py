from dataclasses import dataclass
import math
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class Peer:
    host: str
    port: int


@dataclass(frozen=True)
class ClusterConfig:
    nodes: dict[str, Peer]
    timeout: float = 3.0
    max_message_bytes: int = 1_048_576
    inbox_size: int = 1024

    @classmethod
    def load(cls, path: str | Path) -> "ClusterConfig":
        with open(path, "rb") as stream:
            data = tomllib.load(stream)
        raw_nodes = data.get("nodes")
        if not isinstance(raw_nodes, dict) or not raw_nodes:
            raise ValueError("configuration needs a nonempty [nodes] table")
        nodes = {}
        for node_id, entry in raw_nodes.items():
            if not node_id or not isinstance(entry, dict):
                raise ValueError("each node needs an ID, host, and port")
            host, port = entry.get("host"), entry.get("port")
            if not isinstance(host, str) or not host.strip():
                raise ValueError(f"{node_id}: host must be a nonempty string")
            if type(port) is not int or not 1 <= port <= 65535:
                raise ValueError(f"{node_id}: port must be an integer from 1 to 65535")
            nodes[node_id] = Peer(host, port)
        endpoints = {(peer.host, peer.port) for peer in nodes.values()}
        if len(endpoints) != len(nodes):
            raise ValueError("each node must have a distinct host/port pair")
        network = data.get("network", {})
        if not isinstance(network, dict):
            raise ValueError("network must be a table")
        timeout = network.get("timeout", 3.0)
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("network.timeout must be a finite positive number")
        limits = {}
        for key, default in (("max_message_bytes", 1_048_576), ("inbox_size", 1024)):
            value = network.get(key, default)
            if type(value) is not int or value <= 0:
                raise ValueError(f"network.{key} must be a positive integer")
            limits[key] = value
        if limits["max_message_bytes"] > 0xFFFFFFFF:
            raise ValueError("max_message_bytes exceeds the wire format limit")
        return cls(nodes=nodes, timeout=float(timeout), **limits)
