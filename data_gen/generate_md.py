from typing import Dict, Any, List
import networkx as nx


def generate_markdown_kb_json(g, node_id: str) -> Dict[str, Any]:
    """
    Export the selected node, its 1-hop and 2-hop neighbors into markdown content:
      - user_md           (for the selected node)
      - entities          (list of neighbors with file paths and contents)
      - extended_entities (list of 2-hop neighbors)
    """
    if node_id not in g:
        raise ValueError(f"Node {node_id} not found")

    def slug(name: str) -> str:
        return name.lower().replace(" ", "_")

    def render_md(data: Dict[str, Any], relations: Dict[str, str]) -> str:
        lines = [f"# {data.get('full_name', data['name'])}", "", "## Basic Information"]
        for k, v in data.items():
            if k in ("id", "name", "full_name"):
                continue
            lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")
        if relations:
            lines += ["", "## Relationships"]
            for rel, target in relations.items():
                lines.append(f"- **{rel.title()}**: [[{slug(target)}.md]]")
        return "\n".join(lines)

    # collect 1-hop neighbors and their relation labels
    in_edges = g.in_edges(node_id, data=True, keys=True)
    out_edges = g.out_edges(node_id, data=True, keys=True)
    neighbors = {}
    for src, _, rel, _ in in_edges:
        neighbors[src] = neighbors.get(src, []) + [rel]
    for _, dst, rel, _ in out_edges:
        neighbors[dst] = neighbors.get(dst, []) + [rel]

    # collect 2-hop neighbors (excluding start and direct neighbors)
    two_hop_ids = [
        n
        for n, length in nx.single_source_shortest_path_length(g, node_id).items()
        if length == 2 and n not in neighbors and n != node_id
    ]

    # main user markdown content
    main_data = g.nodes[node_id]
    main_rel = {
        rel: g.nodes[n]["name"] for n, rels in neighbors.items() for rel in rels
    }
    user_md = render_md(main_data, main_rel)

    # build entities list for 1-hop
    entities: List[Dict[str, Any]] = []
    for nbr_id, rels in neighbors.items():
        data = g.nodes[nbr_id]
        rel_map = {rel: main_data.get("name") for rel in rels}
        md_content = render_md(data, rel_map)
        slug_name = slug(data["name"])
        entities.append(
            {
                "entity_name": slug_name,
                "entity_file_path": f"entities/{slug_name}.md",
                "entity_file_content": md_content,
            }
        )

    for nbr2 in two_hop_ids:
        # find path via any intermediate
        path = nx.shortest_path(g, node_id, nbr2)
        # map relations along the path
        rels = []
        for u, v in zip(path, path[1:]):
            # pick first key
            key = next(iter(g.get_edge_data(u, v)))
            rels.append(key)
        # prepare relations mapping: last hop relation -> intermediate node name
        rel_map = {rels[-1]: g.nodes[path[-2]]["name"]}
        data2 = g.nodes[nbr2]
        md2 = render_md(data2, rel_map)
        slug2 = slug(data2["name"])
        entities.append(
            {
                "entity_name": slug2,
                "entity_file_path": f"entities/{slug2}.md",
                "entity_file_content": md2,
            }
        )

    return {"user_md": user_md, "entities": entities}
