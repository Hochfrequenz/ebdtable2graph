"""
contains the conversion logic
"""
from ebd_table_to_graph.models.ebd_graph import EbdGraph
from ebd_table_to_graph.models.ebd_table import EbdTable


def table_to_graph(table: EbdTable) -> EbdGraph:
    """
    converts the given table into a graph
    """
    if table is None:
        raise ValueError("table must not be None")
    raise NotImplementedError("Todo @Leon")
