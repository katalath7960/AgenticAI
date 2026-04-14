"""LangGraph wiring: read_csv -> generate_barcodes -> send_emails -> update_status."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.state import AgentState
from agent.nodes.read_csv import read_csv_node
from agent.nodes.generate_barcode import generate_barcodes_node
from agent.nodes.send_email import send_emails_node
from agent.nodes.update_status import update_status_node


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("read_csv", read_csv_node)
    g.add_node("generate_barcodes", generate_barcodes_node)
    g.add_node("send_emails", send_emails_node)
    g.add_node("update_status", update_status_node)

    g.add_edge(START, "read_csv")
    g.add_edge("read_csv", "generate_barcodes")
    g.add_edge("generate_barcodes", "send_emails")
    g.add_edge("send_emails", "update_status")
    g.add_edge("update_status", END)

    return g.compile()
