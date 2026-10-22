import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

import script_instruction
from script_instruction import NodeID, ScriptInstruction, WaggleParams


@dataclass
class Binary:
    path: str
    percent_of_nodes: int


@dataclass
class ExperimentParams:
    script: List[ScriptInstruction] = field(default_factory=list)


def init_waggle(node_count: int, template_params: WaggleParams) -> List[ScriptInstruction]:
    instructions = []
    for i in range(node_count):
        instructions.append(
            script_instruction.IfNodeIDEquals(
                nodeID=i,
                instruction=script_instruction.InitWaggle(
                    waggleParams=template_params,
                ),
            )
        )
    return instructions


def waggle_scenario(
    node_count: int, mesh: List[ScriptInstruction]
) -> List[ScriptInstruction]:
    instructions: List[ScriptInstruction] = []
    instructions.extend(init_waggle(node_count, WaggleParams()))
    instructions.extend(mesh)

    topic = "waggle-topic"
    instructions.append(script_instruction.SubscribeToTopic(topicID=topic))

    # Wait for subscriptions and topic streams to establish.
    elapsed_seconds = 30
    instructions.append(script_instruction.WaitUntil(elapsedSeconds=elapsed_seconds))

    objectID = random.randint(0, (2**64) - 1)

    # Assign random parts to each node.
    if node_count == 2:
        # If just two nodes, make sure we can always generate a full message.
        part = random.randint(0, 255)
        instructions.append(
            script_instruction.IfNodeIDEquals(
                nodeID=0,
                instruction=script_instruction.AddPiece(
                    topicID=topic, objectID=objectID, parts=part
                ),
            )
        )
        instructions.append(
            script_instruction.IfNodeIDEquals(
                nodeID=1,
                instruction=script_instruction.AddPiece(
                    topicID=topic, objectID=objectID, parts=(0xFF ^ part)
                ),
            )
        )
    else:
        for i in range(node_count):
            # Every node has at least one part so that publishing always has
            # something to send.
            parts = random.randint(1, 255)
            instructions.append(
                script_instruction.IfNodeIDEquals(
                    nodeID=i,
                    instruction=script_instruction.AddPiece(
                        topicID=topic, objectID=objectID, parts=parts
                    ),
                )
            )

    # Everyone publishes their partial message. This is how nodes learn about
    # each others parts and can request them.
    instructions.append(
        script_instruction.Publish(topicID=topic, objectID=objectID)
    )

    # Wait for everything to flush.
    elapsed_seconds += 10
    instructions.append(script_instruction.WaitUntil(elapsedSeconds=elapsed_seconds))

    return instructions


def scenario(scenario_name: str, node_count: int) -> ExperimentParams:
    match scenario_name:
        case "waggle":
            mesh = random_network_mesh(node_count, min(20, node_count - 1))
            instructions = waggle_scenario(node_count, mesh)
        case "waggle-sparse":
            instructions = waggle_scenario(node_count, sparse_network_mesh(node_count, 3))
        case _:
            raise ValueError(f"Unknown scenario name: {scenario_name}")

    return ExperimentParams(script=instructions)


IMPLEMENTATIONS: Dict[str, str] = {
    "go": "go-libp2p/waggle-bin",
    # Always use debug rust. We don't measure compute performance here.
    "rust": "rust-libp2p/target/debug/waggle-interop",
}


def composition(impls: List[str]) -> List[Binary]:
    if not impls:
        raise ValueError("composition requires at least one implementation")
    for name in impls:
        if name not in IMPLEMENTATIONS:
            raise ValueError(
                f"Unknown implementation '{name}'. "
                f"Known: {sorted(IMPLEMENTATIONS)}"
            )

    # Split 100% as evenly as possible. First `leftover` impls get +1 (e.g. 3 impls -> 34/33/33).
    base, leftover = divmod(100, len(impls))
    percents = [base + 1] * leftover + [base] * (len(impls) - leftover)

    return [
        Binary(IMPLEMENTATIONS[name], percent_of_nodes=pct)
        for name, pct in zip(impls, percents)
    ]


def sparse_network_mesh(
    node_count: int, number_of_connections: int
) -> List[ScriptInstruction]:
    """Node i connects to nodes i+1, ..., i+number_of_connections (mod node_count)."""
    connected: Set[Tuple[NodeID, NodeID]] = set()
    instructions = []
    for node_id in range(node_count):
        connect_to = []
        for k in range(1, number_of_connections + 1):
            target = (node_id + k) % node_count
            edge = (min(node_id, target), max(node_id, target))
            if target == node_id or edge in connected:
                continue
            connected.add(edge)
            connect_to.append(target)
        if connect_to:
            instructions.append(
                script_instruction.IfNodeIDEquals(
                    nodeID=node_id,
                    instruction=script_instruction.Connect(connectTo=connect_to),
                )
            )
    return instructions


def random_network_mesh(
    node_count: int, number_of_connections: int
) -> List[ScriptInstruction]:
    connections: Dict[NodeID, Set[NodeID]] = defaultdict(set)
    connect_to: Dict[NodeID, List[NodeID]] = defaultdict(list)
    for node_id in range(node_count):
        while len(connections[node_id]) < number_of_connections:
            target = random.randint(0, node_count - 1)
            if target == node_id:
                continue
            if target in connections[node_id] or node_id in connections[target]:
                continue
            connections[node_id].add(target)
            connections[target].add(node_id)

            connect_to[node_id].append(target)

    instructions = []
    for node_id, node_connections in connect_to.items():
        instructions.append(
            script_instruction.IfNodeIDEquals(
                nodeID=node_id,
                instruction=script_instruction.Connect(
                    connectTo=list(node_connections),
                ),
            )
        )
    return instructions
