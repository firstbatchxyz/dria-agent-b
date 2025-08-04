from typing import Dict, Any
import random
import networkx as nx


def select_random_path_attrs(
    graph: nx.MultiDiGraph, start: str, hops: int = 1
) -> Dict[str, Any]:
    """
    Select a single random path of length `hops` starting from `start`,
    walking outgoing edges at each step. Returns:
      {
        "path": [name0, name1, ..., nameN],
        "edges": [edge_label0, edge_label1, ..., edge_labelN-1],
        "attributes": { attr_name: value, ... }
      }
    If no path of exact length exists, raises ValueError.
    hops=0 returns start node attributes.
    """
    if hops == 0:
        data = graph.nodes[start]
        random_attr = random.choice(list(data.keys()))
        while random_attr in (
            "id",
            "type",
            "name",
            "full_name",
            "birth_date",
            "death_date",
            "birth_place",
            "death_place",
            "entity_type",
        ):
            random_attr = random.choice(list(data.keys()))
        return {
            "path": [
                graph.nodes[start].get("name", start),
                random_attr + "=" + str(data[random_attr]),
            ],
            "new_path": [
                graph.nodes[start].get("name", start),
                random_attr + "=" + "Different/New Attribute value",
            ],
            "changed_node_id": start,
        }

    # build outgoing adjacency list
    current = start
    path = [graph.nodes[start].get("name", start)]
    node_ids = [start]
    edges = []
    for i in range(hops):
        outs = list(graph.successors(current))
        if not outs:
            raise ValueError(f"No outgoing edge at hop {i} from {current}")
        next_node = random.choice(outs)
        # pick one edge between current and next_node
        edge_data = graph.get_edge_data(current, next_node)
        # get first available relation label (edge key)
        rel = next(iter(edge_data.keys()))
        path.append(rel)
        edges.append(rel)
        path.append(graph.nodes[next_node].get("name", next_node))
        current = next_node
        node_ids.append(current)

    # collect attributes of terminal node
    data = graph.nodes[current]
    # attrs = {k: v for k, v in data.items() if k not in ("id","type","name", "full_name", "birth_date", "death_date", "birth_place", "death_place", "entity_type")}
    idx = hops - 1
    path_new = path[:-1]
    path_new.append("Different/New Entity")
    return {"path": path, "new_path": path_new, "changed_node_id": node_ids[idx]}


def find_neighbor_by_edge(G: nx.MultiDiGraph, A: str, rel_name: str) -> list[str]:
    # collect all Bs where A→B has key=rel_name
    bs = [B for _, B, key in G.out_edges(A, keys=True) if key == rel_name]
    # if you also allow incoming edges:
    bs += [B for B, _, key in G.in_edges(A, keys=True) if key == rel_name]
    return bs
