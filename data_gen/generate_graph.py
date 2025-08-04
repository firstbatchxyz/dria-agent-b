"""kg_builder.py - minimal, test-ready skeleton to iteratively build a consistent knowledge-graph via LLM calls.
Now uses Pydantic models for all external JSON payloads so that responses are
strictly validated before they enter the graph.
"""

from __future__ import annotations
import json
from typing import List, Dict, Any, Union
from dotenv import load_dotenv
from jsonschema import validate, ValidationError  # pip install jsonschema
from pydantic import BaseModel, ValidationError as PydanticValidationError, Field
from openai import OpenAI  # or any LLM client
from graph import KG
from llm import LLM

load_dotenv()


# ---------------------------------------------------------------------------
# ▶︎  Pydantic payload models
# ---------------------------------------------------------------------------
class PersonStub(BaseModel):
    id: str
    name: str


class EntityStub(BaseModel):
    """Entity stub for KG generation."""

    id: str
    name: str
    entity_type: str | None = None


class StubResponse(BaseModel):
    people: List[PersonStub]
    entities: List[EntityStub]


class Edge(BaseModel):
    subject_id: str  # subject id
    predicate: str  # predicate / relation label
    object_id: str  # object id


class EdgeResp(BaseModel):
    edges: List[Edge]


class GraphPayload(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Edge]


class AttrPair(BaseModel):
    key: str = Field(..., description="attribute name")
    value: Union[str, int, float, bool] = Field(..., description="attribute value")


class AttrList(BaseModel):
    attributes: List[AttrPair]

    class Config:
        extra = "forbid"


# ---------------------------------------------------------------------------
# ▶︎  JSON-Schema for deep validation (post-pydantic)
# ---------------------------------------------------------------------------
PERSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["id", "name"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0},
        "occupation": {"type": "string"},
    },
}

ENTITY_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["id", "name", "entity_type"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "entity_type": {"type": "string"},
        "location": {"type": "string"},
    },
}


# ---------------------------------------------------------------------------
# ▶︎  Consistency checking utilities
# ---------------------------------------------------------------------------
class ConsistencyChecker:
    def __init__(self, kg: KG):
        self.kg = kg

    def run(self) -> List[str]:
        errs: List[str] = []
        for n, d in self.kg.g.nodes(data=True):
            schema = PERSON_SCHEMA if d["type"] == "Person" else ENTITY_SCHEMA
            try:
                validate(d, schema)
            except ValidationError as e:
                errs.append(f"Node {n}: {e.message}")
        # duplicate name check
        seen: Dict[str, str] = {}
        for n, d in self.kg.g.nodes(data=True):
            name = d.get("name")
            if not name:
                continue
            if name in seen:
                errs.append(f"Duplicate name '{name}' on {n} & {seen[name]}")
            seen[name] = n
        return errs


class Checker:
    def __init__(self, kg: KG):
        self.kg = kg

    def issues(self) -> List[str]:
        out: List[str] = []
        for n, d in self.kg.g.nodes(data=True):
            schema = PERSON_SCHEMA if d["type"] == "Person" else ENTITY_SCHEMA
            try:
                validate(d, schema)
            except ValidationError as e:
                out.append(f"{n}: {e.message}")
        # duplicates
        names: Dict[str, str] = {}
        for n, d in self.kg.g.nodes(data=True):
            name = d.get("name")
            if name in names:
                out.append(f"duplicate name {name}")
            names[name] = n
        return out


# ---------------------------------------------------------------------------
# ▶︎  LLM orchestration driver
# ---------------------------------------------------------------------------
class KGBuildDriver:
    def __init__(self, model: str = "gpt-4o") -> None:
        self.model = model
        self.kg = KG()
        self.llm = LLM(model)  # LLM client for text and JSON generation

    # ---------------- Phase A: generate stubs ----------------
    def gen_stubs(self, prompt: str, n_people: int, n_entities: int | None):
        q = f"Create people={n_people} and entities={n_entities or 1} using: {prompt}"
        raw = self.llm.create_json(
            "You are a KG stub generator and a world builder. Think througly about given world description,create a fictional world that would fit into context with fictional people and entities. Be creative.",
            q,
            StubResponse,
        )
        try:
            stub_resp = raw
        except PydanticValidationError as e:
            raise RuntimeError(f"✖ LLM returned invalid JSON: {e}") from None

        for people in stub_resp.people:
            self.kg.add_node("Person", people.model_dump())
        for e in stub_resp.entities:
            self.kg.add_node("Entity", e.model_dump())

    def edges(self, prompt: str):
        nodes = [
            {"id": n, "name": d["name"], "type": d["type"]}
            for n, d in self.kg.g.nodes(data=True)
        ]
        ids = [node["id"] for node in nodes]
        sys = "Given a world description, plan plausible relations. No self-loops or duplicates."
        sys += f"\n\nWorld: {prompt}\n\n"
        usr = json.dumps(nodes)
        data = self.llm.create_json(sys, usr, EdgeResp)
        for e in data.edges:
            try:
                # Check if ids exist for both subject and object
                if e.subject_id not in ids:
                    print(
                        f"✖ Subject ID {e.subject_id} not found in nodes. Trying by name."
                    )
                    s_id = [node["id"] for node in nodes if node["name"] == e.subject_id]
                    if not s_id:
                        print(f"✖ Subject name {e.subject_id} not found in nodes.")
                        continue
                    s_id = s_id[0]
                else:
                    s_id = e.subject_id
                if e.object_id not in ids:
                    print(
                        f"✖ Object ID {e.object_id} not found in nodes. Trying by name."
                    )
                    o_id = [node["id"] for node in nodes if node["name"] == e.object_id]
                    if not o_id:
                        print(f"✖ Object name {e.object_id} not found in nodes.")
                        continue
                    o_id = o_id[0]
                else:
                    o_id = e.object_id
                try:
                    self.kg.add_edge(s_id, e.predicate, o_id)
                except ValidationError:
                    print("✖ Error adding edge:", e)
            except ValueError:
                pass

    def enrich_and_verify(self, world: str):
        for name, data in self.kg.g.nodes(data=True):
            # get all in-out degree relations to this node
            try:
                log = self.log_node_humanreadable(data["id"])
                # 2. Ask LLM to add attrs / edges / new nodes
                sys = (
                    "You are a KG enricher. Given the world description, and a node, add attributes, to enrich the node data. Try to add distinct attributes to people for diversity. Add new made up details that does NOT CONFLICT with existing information. \n"
                    + world
                )
                usr = "\n\nNode:\n" + log
                resp = self.llm.create_json(sys, usr, AttrList)
                # 3. Apply additions
                for n in resp.attributes:
                    self.kg.add_attribute(data["id"], n.key, n.value)

            except ValueError as e:
                print(f"✖ Error processing node {name} ({data}): {e}")
                continue

    def log_node_humanreadable(self, node_id: str) -> str:
        """Return a human-readable summary of the selected node, its attributes, and its 1-hop neighborhood."""
        if node_id not in self.kg.g:
            return f"[!] Node {node_id} does not exist."

        node = self.kg.g.nodes[node_id]
        name = node.get("name", node_id)
        ntype = node.get("type", "Unknown")

        parts: list[str] = []
        # Header
        parts.append(f"NODE: {name} (ID: {node_id}, Type: {ntype})")

        # Its attributes
        parts.append("ATTRIBUTES:")
        for k, v in node.items():
            if k not in ("name", "type"):
                parts.append(f"  - {k}: {v}")

        # Find neighbors
        nbrs = set(self.kg.g.predecessors(node_id)) | set(self.kg.g.successors(node_id))
        if nbrs:
            parts.append("\nNEIGHBORS:")
            for nbr in nbrs:
                nd = self.kg.g.nodes[nbr]
                nbr_name = nd.get("name", nbr)
                nbr_type = nd.get("type", "Unknown")
                # neighbor attributes
                attrs = ", ".join(
                    f"{kk}={vv}" for kk, vv in nd.items() if kk not in ("name", "type")
                )
                parts.append(
                    f"  • {nbr_name} (ID: {nbr}, Type: {nbr_type}) — attrs: {attrs or 'none'}"
                )

        # Edges
        parts.append("\nRELATIONS:")
        # incoming
        for src, _, rel, data in self.kg.g.in_edges(node_id, keys=True, data=True):
            src_name = self.kg.g.nodes[src].get("name", src)
            parts.append(f"  ← {src_name} --[{rel}]--> {name}  (edge attrs: {data})")
        # outgoing
        for _, dst, rel, data in self.kg.g.out_edges(node_id, keys=True, data=True):
            dst_name = self.kg.g.nodes[dst].get("name", dst)
            parts.append(f"  {name} --[{rel}]--> {dst_name}  (edge attrs: {data})")

        return "\n".join(parts)


if __name__ == "__main__":
    client = OpenAI()  # expects OPENAI_API_KEY env var
    driver = KGBuildDriver()
    # example_world = "A large italian-american family originated from New Jersey. Few of the members in the family works in the family-owned Italian restaurant 'Pangorio'."
    example_world = "Two neighboring families in Morocco."

    driver.gen_stubs(example_world, n_people=5, n_entities=5)
    driver.edges(example_world)
    driver.enrich_and_verify(example_world)
    checker = ConsistencyChecker(driver.kg)
    problems = checker.run()
    if problems:
        print("❌ Consistency Issues:")
        for p in problems:
            print("  -", p)
    else:
        print("✅ Graph valid. Payload:\n")
        print(driver.kg.to_json())
