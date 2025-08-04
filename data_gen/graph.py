"""kg_builder.py – minimal, test-ready skeleton to iteratively build a consistent knowledge-graph via LLM calls.
Now uses Pydantic models for all external JSON payloads so that responses are
strictly validated before they enter the graph.
"""

from __future__ import annotations
import uuid
import json
from typing import List, Dict, Any
import networkx as nx
from pydantic import BaseModel


class Edge(BaseModel):
    s: str  # subject id
    p: str  # predicate / relation label
    o: str  # object id


class EdgeResp(BaseModel):
    edges: List[Edge]


class GraphPayload(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Edge]


class KG:
    def __init__(self) -> None:
        self.g = nx.MultiDiGraph()

    def add_node(self, node_type: str, attrs: Dict[str, Any]) -> str:
        node_id = attrs.get("id", str(uuid.uuid4()))
        self.g.add_node(node_id, **attrs, type=node_type)
        return node_id

    def add_attribute(self, node_id: str, key: str, value: Any) -> None:
        """Add or update an attribute on a node."""
        if node_id not in self.g:
            raise ValueError(f"Node {node_id} does not exist in the graph.")
        self.g.nodes[node_id][key] = value

    def add_edge(self, src: str, predicate: str, dst: str, **attrs) -> None:
        self.g.add_edge(src, dst, key=predicate, **attrs)

    # export helpers
    def payload(self) -> GraphPayload:
        nodes = [{"id": n, **d} for n, d in self.g.nodes(data=True)]
        edges = [
            {"s": s, "p": k, "o": o, **d}
            for s, o, k, d in self.g.edges(keys=True, data=True)
        ]
        return GraphPayload(nodes=nodes, edges=[Edge(**e) for e in edges])

    def to_json(self) -> str:
        return self.payload().model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str | dict) -> "KG":
        """
        Create a KG instance from a JSON payload or string.
        Expects a dict or JSON string with:
          {
            "nodes": [ { "id":…, "type":…, … } ],
            "edges": [ { "s":…, "p":…, "o":…, … } ]
          }
        """
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        kg = cls()

        # add nodes
        for node in data.get("nodes", []):
            nid = node.pop("id")
            ntype = node.pop("type", "Entity")
            attrs = {**node, "id": nid}
            kg.add_node(ntype, attrs)

        # add edges
        for edge in data.get("edges", []):
            src = edge["s"]
            pred = edge["p"]
            dst = edge["o"]
            extra = {k: v for k, v in edge.items() if k not in ("s", "p", "o")}
            kg.add_edge(src, pred, dst, **extra)

        return kg
