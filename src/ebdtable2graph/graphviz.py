import re
from typing import List

import requests
from networkx import DiGraph

from ebdtable2graph.graph_utils import _mark_last_common_ancestors
from ebdtable2graph.models import (
    DecisionNode,
    EbdGraph,
    EbdGraphEdge,
    EndNode,
    OutcomeNode,
    StartNode,
    ToNoEdge,
    ToYesEdge,
)

ADD_INDENT = "    "  #: This is just for style purposes to make the plantuml files human-readable.


def _format_label(label: str) -> str:
    return label.replace("\n", '<BR align="left"/>')
    # escaped_str = re.sub(r"^(\d+): ", r"<B>\1: </B>", label)
    # escaped_str = label.replace("\n", '<BR align="left"/>')
    # return f'<{escaped_str}<BR align="left"/>>'


def _convert_start_node_to_dot(ebd_graph: EbdGraph, node: str, indent: str) -> str:
    formatted_label = (
        f'<B>{ebd_graph.metadata.ebd_code}</B><BR align="center"/>'
        f'<FONT point-size="12"><B><U>Prüfende Rolle:</U> {ebd_graph.metadata.role}</B></FONT><BR align="center"/>'
    )
    return f'{indent}"{node}" [margin="0.2,0.12", shape=box, style=filled, fillcolor="#7a8da1", label=<{formatted_label}>];'


def _convert_end_node_to_dot(node: str, indent: str) -> str:
    return f'{indent}"{node}" [margin="0.2,0.12", shape=box, style=filled, fillcolor="#7a8da1", label="Ende"];'


def _convert_outcome_node_to_dot(ebd_graph: EbdGraph, node: str, indent: str) -> str:
    formatted_label = (
        f'<B>{ebd_graph.graph.nodes[node]["node"].result_code}</B><BR align="center"/>'
        f'<FONT point-size="12">'
        f'<U>Hinweis:</U><BR align="left"/>{_format_label(ebd_graph.graph.nodes[node]["node"].note)}<BR align="left"/>'
        f"</FONT>"
    )
    return f'{indent}"{node}" [margin="0.2,0.12", shape=box, style=filled, fillcolor="#cca9ab", label=<{formatted_label}>];'


def _convert_decision_node_to_dot(ebd_graph: EbdGraph, node: str, indent: str) -> str:
    formatted_label = (
        f'<B>{ebd_graph.graph.nodes[node]["node"].step_number}: </B>'
        f'{_format_label(ebd_graph.graph.nodes[node]["node"].question)}'
        f'<BR align="left"/>'
    )
    return (
        f'{indent}"{node}" [margin="0.2,0.12", shape=box, style="filled,rounded", fillcolor="#7aab8a", '
        f"label=<{formatted_label}>];"
    )


def _convert_node_to_dot(ebd_graph: EbdGraph, node: str, indent: str) -> str:
    """
    A shorthand to convert an arbitrary node to dot code. It just determines the node type and calls the
    respective function.
    """
    match ebd_graph.graph.nodes[node]["node"]:
        case DecisionNode():
            return _convert_decision_node_to_dot(ebd_graph, node, indent)
        case OutcomeNode():
            return _convert_outcome_node_to_dot(ebd_graph, node, indent)
        case EndNode():
            return _convert_end_node_to_dot(node, indent)
        case StartNode():
            return _convert_start_node_to_dot(ebd_graph, node, indent)
        case _:
            raise ValueError(f"Unknown node type: {ebd_graph.graph.nodes[node]['node']}")


def _convert_nodes_to_dot(ebd_graph: EbdGraph, indent: str) -> str:
    if ebd_graph.multi_step_instructions:
        # TODO
        pass
    return "\n".join([_convert_node_to_dot(ebd_graph, node, indent) for node in ebd_graph.graph.nodes])


def _convert_yes_edge_to_dot(ebd_graph: EbdGraph, node_src: str, node_target: str, indent: str) -> str:
    return f'{indent}"{node_src}" -> "{node_target}" [label="Ja"];'


def _convert_no_edge_to_dot(ebd_graph: EbdGraph, node_src: str, node_target: str, indent: str) -> str:
    return f'{indent}"{node_src}" -> "{node_target}" [label="Nein"];'


def _convert_ebd_graph_edge_to_dot(ebd_graph: EbdGraph, node_src: str, node_target: str, indent: str) -> str:
    return f'{indent}"{node_src}" -> "{node_target}";'


def _convert_edge_to_dot(ebd_graph: EbdGraph, node_src: str, node_target: str, indent: str) -> str:
    """
    A shorthand to convert an arbitrary node to dot code. It just determines the node type and calls the
    respective function.
    """
    match ebd_graph.graph[node_src][node_target]["edge"]:
        case ToYesEdge():
            return _convert_yes_edge_to_dot(ebd_graph, node_src, node_target, indent)
        case ToNoEdge():
            return _convert_no_edge_to_dot(ebd_graph, node_src, node_target, indent)
        case EbdGraphEdge():
            return _convert_ebd_graph_edge_to_dot(ebd_graph, node_src, node_target, indent)
        case _:
            raise ValueError(f"Unknown edge type: {ebd_graph.graph[node_src][node_target]['edge']}")


def _convert_edges_to_dot(ebd_graph: EbdGraph, indent: str) -> List[str]:
    return [_convert_edge_to_dot(ebd_graph, edge[0], edge[1], indent) for edge in ebd_graph.graph.edges]


def convert_graph_to_dot(ebd_graph: EbdGraph) -> str:
    nx_graph = ebd_graph.graph
    _mark_last_common_ancestors(nx_graph)
    dot_code = "digraph D {\n"
    assert len(nx_graph["Start"]) == 1, "Start node must have exactly one outgoing edge."
    assert "1" in nx_graph["Start"], "Start node must be connected to decision node '1'."
    dot_code += _convert_nodes_to_dot(ebd_graph, ADD_INDENT) + "\n\n"
    dot_code += "\n".join(_convert_edges_to_dot(ebd_graph, ADD_INDENT)) + "\n"

    return dot_code + "}"


def convert_dot_to_svg_kroki(dot_code: str) -> str:
    """
    Converts dot code to svg (code) and returns the result as string. It uses kroki.io.
    """
    url = "https://kroki.io"
    answer = requests.post(
        url,
        json={"diagram_source": dot_code, "diagram_type": "graphviz", "output_format": "svg"},
        timeout=5,
    )
    if answer.status_code != 200:
        raise ValueError(
            f"Error while converting dot to svg: {answer.status_code}: {requests.codes[answer.status_code]}. "
            f"{answer.text}"
        )
    return answer.text
