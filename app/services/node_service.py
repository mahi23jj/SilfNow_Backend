from sqlmodel import Session

from app.models.edge import Edge
from app.models.node import Node


def create_node(node_data , session: Session):

    node = Node(
        name=node_data["name"],
        latitude=node_data["latitude"],
        longitude=node_data["longitude"],
        is_terminal=node_data.get("is_terminal", True)
    )

    session.add(node)
    session.commit()
    session.refresh(node)

    return node


    # Logic to create a new node in the database
   

def create_edge(edge_data , session: Session):

    edge = Edge(
        from_node_id=edge_data["from_node_id"],
        to_node_id=edge_data["to_node_id"],
        transport_types=edge_data["transport_types"],
        base_travel_time_min=edge_data["base_travel_time_min"],
        base_travel_time_max=edge_data["base_travel_time_max"],
        base_cost_min=edge_data["base_cost_min"],
        base_cost_max=edge_data["base_cost_max"]
    )

    session.add(edge)
    session.commit()
    session.refresh(edge)

    return edge
   