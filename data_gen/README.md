# Synthetic Data Generator

`data_gen` contains a sophisticated data generation pipeline that creates synthetic knowledge graphs based on various "world scenarios". For each generated graph, it produces a rich dataset including markdown-formatted knowledge bases, multi-hop question-answer pairs for retrieval tasks, and complex update queries with corresponding diffs.

The pipeline leverages Large Language Models (LLMs) for creative and contextual data generation, including entity creation, relationship inference, and natural language rephrasing.

## Features

-   **Scenario-Based Graph Generation**: Creates knowledge graphs from diverse, configurable world descriptions (e.g., an Italian-American restaurant, a space station crew, a tech startup).
-   **LLM-Powered Enrichment**: Uses LLMs to generate initial nodes, infer plausible relationships, and add detailed attributes to enrich the graph.
-   **Graph Consistency Validation**: Includes a validation step to check for issues like duplicate names or malformed nodes before proceeding.
-   **Markdown Knowledge Base**: For each "person" node, it generates a set of markdown files representing their 2-hop knowledge neighborhood, simulating a personal knowledge base.
-   **Multi-Hop Q&A Generation**: Creates structured question-answer pairs for testing knowledge retrieval at 0, 1, and 2 hops from a central node.
-   **Update Query Simulation**: Simulates changes to the knowledge graph (both attribute and relationship updates) and generates:
    -   Natural language queries that would trigger such an update.
    -   A `git`-style diff of the markdown files, showing the exact changes before and after the update.
-   **Configurable & Extensible**: New world scenarios can be easily added to `configs.py` to generate different kinds of data.

## Directory Structure

The project is organized as follows:

```
└── data_gen/
    ├── configs.py          # Defines the world scenarios for data generation.
    ├── run.py              # Main script to orchestrate the entire pipeline.
    ├── generate_graph.py   # Builds and enriches the initial knowledge graph.
    ├── generate_md.py      # Generates markdown knowledge bases from the graph.
    ├── generate_qa.py      # Generates raw retrieval Q&A pairs.
    ├── generate_update.py  # Simulates graph changes for update queries.
    ├── llm.py              # Wrappers for LLM (OpenAI, Anthropic) API calls.
    ├── graph.py            # A NetworkX-based wrapper for the knowledge graph.
    ├── diff.py             # Utility for generating string/file diffs.
    └── prompts/
        ├── ...             # Jinja2 templates for prompting LLMs.
```

## How It Works

The `run.py` script executes the following process for each scenario defined in `configs.py`:

1.  **Create Graph**: A `KGBuildDriver` instance is created. It calls an LLM with a world description to generate person/entity stubs, infer relationships (edges), and enrich each node with detailed attributes.
2.  **Validate Graph**: The generated graph is checked for consistency. If issues are found, the process for that scenario halts.
3.  **Process Nodes**: The script selects a configured number of "Person" nodes from the graph to serve as focal points for data generation.
4.  **Generate Data**: For each selected person node:
    a.  **Markdown KB**: A set of markdown files representing the node's knowledge is created (`base_memory.json`).
    b.  **Retrieval Q&A**: 0, 1, and 2-hop questions are generated based on the graph structure and then reformatted by an LLM into natural language (`retrieval_questions.json`).
    c.  **Update Queries**: The script simulates a random change in the graph. It generates natural language queries that could initiate this change and calculates a `diff` showing the resulting modification to the markdown knowledge base (`update_queries.json`).
5.  **Save Output**: All generated data is saved into a unique directory under the `instances/` folder.


### How to Run the Code

Follow these steps to set up and run the data generation pipeline.


**Set Up API Keys**

Create a file named `.env` in the root directory (the parent directory of `data_gen/`). Add your API keys to this file:

```bash
    OPENAI_API_KEY="sk-..."
    ANTHROPIC_API_KEY="sk-..."
```

**Set up configurations**

Use configs.py to set worlds for data generation. 
Example world:

```json
        {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A large italian-american family originated from New Jersey. "
        "Few of the members in the family works in the "
        "family-owned Italian restaurant 'Pangorio'.",
        "output_base_dir": "instances",
    },
```

**Run the Main Script**

Execute the `run.py` script from the root directory. Using the `-m` flag ensures that Python's module import system works correctly.

```bash
cd data_gen
uv sync
uv run data_gen.run
```

**Monitor the Process**

The script will print its progress to the console. It will first build and validate a graph for a given scenario, then loop through a subset of person nodes to generate the associated data. You will see progress bars from `tqdm` for each major step.

```bash
    --- Running with configuration: A large italian-american family... ---
    Starting data generation for instance: 2f4b...
    Step 1: Building and validating the knowledge graph...
    ✅ Graph is consistent and valid.
    ✅ Base graph saved to instances/2f4b.../graph.json
    Processing person nodes: 100%|██████████| 3/3 [01:30<00:00, 30.00s/it]

    🎉 Successfully completed data generation for instance 2f4b...
```

#### 4. Output

-   The generated data will be saved in the `instances/` directory (or the `output_base_dir` specified in `configs.py`).
-   Each run creates a new subdirectory with a unique instance ID (e.g., `instances/2f4b...d93a/`).
-   Inside an instance directory, you will find:
    -   `graph.json`: The full knowledge graph for the scenario.
    -   One or more `memory_<uuid>` subdirectories, each corresponding to a processed person node.
    -   Inside each `memory` directory:
        -   `base_memory.json`: Contains the initial markdown knowledge base.
        -   `retrieval_questions.json`: Contains the 0, 1, and 2-hop Q&A pairs.
        -   `update_queries.json`: Contains the update queries and their corresponding diffs.