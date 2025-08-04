"""
# data_gen/run.py

This script orchestrates the generation of a knowledge graph, retrieval questions, and update queries.
It processes person nodes to create markdown files, retrieval questions, and update queries with diffs.

"""

import uuid
import json
import random
from pathlib import Path
from tqdm import tqdm
import networkx as nx
from dotenv import load_dotenv

from llm import QuestionReformat
from generate_graph import KGBuildDriver, ConsistencyChecker
from generate_md import generate_markdown_kb_json
from generate_qa import generate_retrieval_attr_qas
from generate_update import select_random_path_attrs, find_neighbor_by_edge
from diff import diff_strings
from configs import CONFIGS

# --- Constants ---
NODE_TYPE_PERSON = "person"
HOP_LEVELS = ["0_hop", "1_hop", "2_hop"]


def create_and_validate_graph(
    world: str, n_people: int, n_entities: int
) -> KGBuildDriver:
    """
    Generates, enriches, and validates a knowledge graph based on a world description.

    Args:
        world: A string describing the world to model.
        n_people: The number of person stubs to generate.
        n_entities: The number of entity stubs to generate.

    Returns:
        A validated KGBuildDriver instance.

    Raises:
        ValueError: If the generated graph has consistency issues.
    """
    print("Step 1: Building and validating the knowledge graph...")
    driver = KGBuildDriver()
    driver.gen_stubs(world, n_people=n_people, n_entities=n_entities)
    driver.edges(world)
    driver.enrich_and_verify(world)

    checker = ConsistencyChecker(driver.kg)
    problems = checker.run()

    if problems:
        print("❌ Consistency Issues Found:")
        for p in problems:
            print(f"  - {p}")
        raise ValueError("Graph has consistency issues, cannot proceed.")

    print("✅ Graph is consistent and valid.")
    return driver


def generate_retrieval_data(
    graph: nx.MultiDiGraph,
    reformatter: QuestionReformat,
    start_node_id: str,
    user_md: str,
    num_qa: int,
) -> dict:
    """
    Generates and reformats retrieval questions for 0, 1, and 2-hop paths.

    Args:
        graph: The knowledge graph.
        reformatter: The question reformatting utility.
        start_node_id: The ID of the node to start from.
        user_md: The markdown content for the user's personal info.
        num_qa: The number of questions to generate per hop level (for 1 and 2-hops).

    Returns:
        A dictionary containing lists of questions for each hop level.
    """
    print(f"Generating retrieval questions for node {start_node_id}...")
    user_name = graph.nodes[start_node_id]["name"]
    raw_qas = generate_retrieval_attr_qas(graph, start=start_node_id)
    retrieval_questions = {}

    for hop in HOP_LEVELS:
        is_zero_hop = hop == "0_hop"
        questions = raw_qas.get(hop, [])
        if not is_zero_hop:
            questions = questions[:num_qa]

        if questions:
            retrieval_questions[hop] = reformatter.reformat(
                user=user_name,
                personal_info=user_md,
                questions=questions,
                is_zero=is_zero_hop,
            )
    print("✅ Retrieval questions generated.")
    return retrieval_questions


def _calculate_update_diff(
    original_graph: nx.MultiDiGraph,
    updated_graph: nx.MultiDiGraph,
    base_node_id: str,
    update_info: dict,
) -> str:
    """Helper function to calculate the markdown diff for a given update."""
    original_md_bundle = generate_markdown_kb_json(original_graph, node_id=base_node_id)
    updated_md_bundle = generate_markdown_kb_json(updated_graph, node_id=base_node_id)

    # Case 1: A simple attribute was changed on a node.
    if "attribute_name" in update_info:
        return "==='user.md'===\n" + diff_strings(
            original_md_bundle["user_md"], updated_md_bundle["user_md"]
        )

    # Case 2: A relationship was changed, involving adding/removing nodes/edges.
    elif "name" in update_info:
        # Find the slug names for diffing entity files
        changed_node_slug = (
            original_graph.nodes[update_info["changed_node_id"]]["name"]
            .lower()
            .replace(" ", "_")
        )
        added_node_slug = update_info["name"].lower().replace(" ", "_")

        # Find the content of the file that was changed
        old_entity_files = {e["entity_name"]: e for e in original_md_bundle["entities"]}
        new_entity_files = {e["entity_name"]: e for e in updated_md_bundle["entities"]}

        # Diff for the file of the node whose relationship changed
        old_content1 = old_entity_files.get(changed_node_slug, {}).get(
            "entity_file_content", ""
        )
        if len(old_content1) == 0:
            # Fallback to user.md if the entity file is not found
            old_content1 = original_md_bundle["user_md"]
        new_content1 = new_entity_files.get(changed_node_slug, {}).get(
            "entity_file_content", ""
        )
        if len(new_content1) == 0:
            # Fallback to user.md if the entity file is not found
            new_content1 = updated_md_bundle["user_md"]
        file_path1 = old_entity_files.get(changed_node_slug, {}).get(
            "entity_file_path", "user.md"
        )  # Fallback to user.md
        diff1 = diff_strings(old_content1, new_content1)

        # Diff for the newly created entity file
        new_content2 = new_entity_files.get(added_node_slug, {}).get(
            "entity_file_content", ""
        )
        file_path2 = new_entity_files.get(added_node_slug, {}).get(
            "entity_file_path", ""
        )
        diff2 = diff_strings(
            "", new_content2
        )  # Diff against an empty string for a new file

        return f"==={file_path1}===\n{diff1}\n==={file_path2}===\n{diff2}"

    return ""  # Should not happen with valid update_info


def generate_update_data(
    driver: KGBuildDriver, reformatter: QuestionReformat, base_node_id: str
) -> dict:
    """
    Generates update queries by simulating changes to the graph and calculating diffs.

    Args:
        driver: The KGBuildDriver instance holding the graph.
        reformatter: The question reformatting utility.
        base_node_id: The ID of the node to generate updates around.

    Returns:
        A dictionary containing lists of update queries for each hop level.
    """
    print(f"Generating update queries for node {base_node_id}...")
    update_queries = {hop: [] for hop in HOP_LEVELS}
    original_graph = driver.kg.g

    for hop_num in [0, 0, 0, 1, 1, 2]:
        try:
            path_info = select_random_path_attrs(
                original_graph, base_node_id, hops=hop_num
            )

            # Reformat into natural language update queries
            reformatted_data = reformatter.reformat_update(
                user=path_info["path"][0], path=path_info
            )
            queries = reformatted_data[:2]
            update_details: dict = reformatted_data[-1]

            update_details["changed_node_id"] = path_info.get(
                "changed_node_id", base_node_id
            )

            # Simulate the update on a copy of the graph
            new_graph = original_graph.copy()
            if "attribute_name" in update_details:
                # Update a node's attribute
                target = update_details["changed_node_id"]
                nx.set_node_attributes(
                    new_graph,
                    {
                        target: {
                            update_details["attribute_name"]: update_details[
                                "attribute_value"
                            ]
                        }
                    },
                )
            elif "name" in update_details:
                # Change a relationship: remove old edge, add new node and edge
                rel_name = path_info["path"][-2]
                end_node_id = find_neighbor_by_edge(
                    new_graph, path_info["changed_node_id"], rel_name
                )[0]
                new_graph.remove_edge(
                    update_details["changed_node_id"], end_node_id, key=rel_name
                )

                new_node_id = str(uuid.uuid4())
                node_attrs = {
                    "name": update_details["name"],
                    "type": "Entity" if "entity_type" in update_details else "Person",
                }
                if "entity_type" in update_details:
                    node_attrs["entity_type"] = update_details["entity_type"]
                new_graph.add_node(new_node_id, **node_attrs)
                new_graph.add_edge(
                    update_details["changed_node_id"], new_node_id, key=rel_name
                )

            # Calculate the diff and format the output
            diff = _calculate_update_diff(
                original_graph, new_graph, base_node_id, update_details
            )
            hop_key = f"{hop_num}_hop"
            for query in queries:
                update_queries[hop_key].append({"query": query, "diff": diff})

        except ValueError as e:
            print(f"⚠️ Could not generate update for hop {hop_num}. Reason: {e}")
            continue

    print("✅ Update queries generated.")
    return update_queries


def process_person_node(
    driver: KGBuildDriver,
    reformatter: QuestionReformat,
    node_id: str,
    instance_path: Path,
    cfg: dict,
):
    """
    Processes a single person node to generate and save all associated data.

    Args:
        driver: The KGBuildDriver instance.
        reformatter: The question reformatting utility.
        node_id: The ID of the person node to process.
        instance_path: The base path for the current instance run.
        cfg: The configuration dictionary.
    """
    # Create a unique directory for this memory instance
    mem_id = f"memory_{uuid.uuid4().hex}"
    memory_path = instance_path / mem_id
    memory_path.mkdir(exist_ok=True)
    print(f"\n--- Processing Node: {node_id} | Memory ID: {mem_id} ---")

    # 1. Generate base markdown files from the graph
    md_bundle = generate_markdown_kb_json(driver.kg.g, node_id=node_id)
    md_bundle["mem_id"] = mem_id
    with open(memory_path / "base_memory.json", "w", encoding="utf-8") as f:
        json.dump(md_bundle, f, indent=2)

    # 2. Generate retrieval questions
    retrieval_questions = generate_retrieval_data(
        graph=driver.kg.g,
        reformatter=reformatter,
        start_node_id=node_id,
        user_md=md_bundle["user_md"],
        num_qa=cfg["num_qa_per_iter"],
    )
    with open(memory_path / "retrieval_questions.json", "w", encoding="utf-8") as f:
        json.dump(retrieval_questions, f, indent=2)

    # 3. Generate update queries with diffs
    update_queries = generate_update_data(
        driver=driver, reformatter=reformatter, base_node_id=node_id
    )
    with open(memory_path / "update_queries.json", "w", encoding="utf-8") as f:
        json.dump(update_queries, f, indent=2)


def run(config):
    """Main execution function."""
    load_dotenv()

    # --- Initialization ---
    instance_id = str(uuid.uuid4())
    instance_path = Path(config["output_base_dir"]) / instance_id
    instance_path.mkdir(parents=True, exist_ok=True)
    print(f"Starting data generation for instance: {instance_id}")

    reformatter = QuestionReformat()

    # --- Graph Generation ---
    try:
        driver = create_and_validate_graph(
            config["world_description"], config["num_people"], config["num_entities"]
        )
    except ValueError as e:
        print(f"🚨 Halting execution due to graph validation error: {e}")
        return

    # Save the base graph
    graph_output_path = instance_path / "graph.json"
    with open(graph_output_path, "w", encoding="utf-8") as f:
        f.write(driver.kg.to_json())
    print(f"✅ Base graph saved to {graph_output_path}")

    # --- Data Generation Loop ---
    person_nodes = [
        n
        for n, d in driver.kg.g.nodes(data=True)
        if d.get("type", "").lower() == NODE_TYPE_PERSON
    ]

    if len(person_nodes) < config["num_iter_per_graph"]:
        print(
            f"⚠️ Warning: Not enough person nodes ({len(person_nodes)}) to meet "
            f"the required number of iterations ({config['num_iter_per_graph']})."
        )
        num_to_process = len(person_nodes)
    else:
        num_to_process = config["num_iter_per_graph"]

    selected_nodes = random.sample(person_nodes, num_to_process)

    for node_id in tqdm(selected_nodes, desc="Processing person nodes"):
        process_person_node(driver, reformatter, node_id, instance_path, config)

    print(f"\n🎉 Successfully completed data generation for instance {instance_id}.")


if __name__ == "__main__":
    from random import shuffle

    shuffle(CONFIGS)
    for CONFIG in tqdm(CONFIGS, desc="Running configurations"):
        print(f"\n--- Running with configuration: {CONFIG['world_description']} ---")
        run(CONFIG)
        print("Finished processing")
