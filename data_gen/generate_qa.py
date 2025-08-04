from typing import Dict, List
import networkx as nx


def generate_retrieval_attr_qas(
    graph: nx.MultiDiGraph, start: str
) -> Dict[str, List[Dict[str, str]]]:
    """
    Generate QA pairs:
      - zero_hop: attributes of start itself
      - one_hop: attributes of its direct neighbors
      - two_hop: attributes of nodes exactly two edges away
    """

    def label(s: str) -> str:
        return s.replace("_", " ")

    zero_hop, one_hop, two_hop = [], [], []

    # 0-hop
    for attr, val in graph.nodes[start].items():
        if attr in ("id", "type", "name"):
            continue
        zero_hop.append(
            {
                "q": f"What is the {label(attr)} of {graph.nodes[start].get('name', start)}?",
                "a": str(val),
            }
        )

    # 1-hop outgoing: start -> rel -> neighbor
    for _, nbr, rel in graph.out_edges(start, keys=True):
        rel_phrase = label(rel)
        for attr, val in graph.nodes[nbr].items():
            if attr in ("id", "type", "name"):
                continue
            if rel_phrase[-2:] == "of":
                q = (
                    f"What is the {label(attr)} of the entity that {graph.nodes[start]['name']} {rel_phrase}?",
                )
            else:
                q = (
                    f"What is the {label(attr)} of the entity that {rel_phrase} {graph.nodes[start]['name']}?",
                )
            one_hop.append(
                {
                    "q": q,
                    "a": str(val),
                    "attribute": f"{label(attr)}={val}",
                    "path": f"{graph.nodes[start]['name']} -> {graph.nodes[nbr]['name']}",
                }
            )

    # 1-hop incoming: neighbor -> rel -> start
    for nbr, _, rel in graph.in_edges(start, keys=True):
        rel_phrase = label(rel)
        for attr, val in graph.nodes[nbr].items():
            if attr in ("id", "type", "name"):
                continue
            if rel_phrase[-2:] == "of":
                q = (
                    f"What is the {label(attr)} of the entity that {graph.nodes[start]['name']} {rel_phrase}?",
                )
            else:
                q = (
                    f"What is the {label(attr)} of the entity that {rel_phrase} {graph.nodes[start]['name']}?",
                )
            one_hop.append(
                {
                    "q": q,
                    "a": str(val),
                    "attribute": f"{label(attr)}={val}",
                    "path": f"{graph.nodes[nbr]['name']} -> {graph.nodes[start]['name']}",
                }
            )

    # 2-hop (two outgoing hops): start -> mid -> end, distance exactly 2
    for mid in graph.successors(start):
        # get rel1 for start->mid
        edge_data = graph.get_edge_data(start, mid)
        if edge_data is None:
            continue
        rel1s = [k for k in edge_data.keys()]
        rel1_phrase = " & ".join(label(r) for r in rel1s)
        for _, end, rel2 in graph.out_edges(mid, keys=True):
            if end == start:
                continue
            # ensure exactly two hops
            try:
                if nx.shortest_path_length(graph, start, end) != 2:
                    continue
            except nx.NetworkXNoPath:
                continue
            rel2_phrase = label(rel2)
            for attr, val in graph.nodes[end].items():
                if attr in ("id", "type", "name"):
                    continue
                if rel2_phrase.endswith("of"):
                    if rel1_phrase.endswith("of"):
                        question = (
                            f"What is the {label(attr)} of the node that {rel2_phrase} "
                            f"{graph.nodes[mid]['type']} that {rel1_phrase} "
                            f"{graph.nodes[start]['name']}?"
                        )
                    else:
                        question = (
                            f"What is the {label(attr)} of the node that {rel1_phrase} "
                            f"{graph.nodes[mid]['type']} that {rel2_phrase} "
                            f"{graph.nodes[start]['name']}?"
                        )
                else:
                    question = (
                        f"What is the {label(attr)} of the entity that "
                        f"{rel2_phrase} the entity"
                        f" where/which {graph.nodes[start]['name']} {rel1_phrase}?"
                    )
                two_hop.append(
                    {
                        "q": question,
                        "a": str(val),
                        "attribute": f"{label(attr)}={val}",
                        "path": f"{graph.nodes[start]['name']} - {rel1_phrase} -> {graph.nodes[mid]['name']} - {rel2_phrase}-> {graph.nodes[end]['name']}",
                    }
                )

    return {"0_hop": zero_hop, "1_hop": one_hop, "2_hop": two_hop}
