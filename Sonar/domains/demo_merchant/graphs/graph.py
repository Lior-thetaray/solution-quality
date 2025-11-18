from typing import List

from thetaray.api.solution import (
    DataType,
    EdgeType,
    Graph,
    NodePropertyReference,
    NodeType,
    Property,
)


def graph() -> Graph:
    return Graph(
        identifier="demo_merchant_graph",
        nodes=[
            NodeType(
                identifier="AC",
                display_name="Account",
                description="Merchant or counterparty account",
                encrypted=True,
                audited=True,
                properties=[
                    Property(
                        identifier="AN",
                        display_name="Account ID",
                        description="Unique identifier of the account",
                        type=DataType.STRING,
                        is_key=True,
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="NM",
                        display_name="Name",
                        description="Merchant or counterparty name",
                        type=DataType.STRING,
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="CN",
                        display_name="Country code",
                        description="Country of residence",
                        type=DataType.STRING,
                        encrypted=True,
                    ),
                    Property(
                        identifier="AD",
                        display_name="Address",
                        description="Client address (empty for counterparties)",
                        type=DataType.STRING,
                        encrypted=True,
                        audited=True,
                    ),
                ],
            ),
            NodeType(
                identifier="AL",
                display_name="Alerted activity",
                description="Alerted activity",
                properties=[
                    Property(
                        identifier="AI",
                        display_name="Alerted activity ID",
                        description="Alerted activity ID",
                        type=DataType.STRING,
                    ),
                    Property(
                        identifier="RI",
                        display_name="Risk identifier",
                        description="Alerted activity ID",
                        type=DataType.STRING,
                    ),
                    Property(
                        identifier="SP",
                        display_name="Suppressed",
                        description="Was the alerted activity suppressed",
                        type=DataType.BOOLEAN,
                    ),
                ],
            ),
        ],
        edges=[
            EdgeType(
                identifier="TX",
                display_name="Transaction",
                description="The transaction from one account to another",
                source_nodes=["AC"],
                target_nodes=["AC"],
                properties=[
                    Property(
                        identifier="AM",
                        display_name="Amount",
                        description="The transaction amount",
                        type=DataType.DOUBLE,
                    ),
                    Property(
                        identifier="CT",
                        display_name="Transactions",
                        description="Transactions",
                        type=DataType.DOUBLE,
                    ),
                    Property(
                        identifier="CO",
                        display_name="Country origin",
                        description="Origin country of the transaction",
                        type=DataType.STRING,
                    ),
                    Property(
                        identifier="CD",
                        display_name="Country destination",
                        description="Destination country of the transaction",
                        type=DataType.STRING,
                    )
                ],
            ),
            EdgeType(
                identifier="AL",
                source_nodes=["AL"],
                target_nodes=["AC"],
                display_name="Alerting edge",
                description="Edge, connecting alerted activity to account",
                properties=[],
            ),
            EdgeType(
                identifier="AL",
                source_nodes=["AL"],
                target_nodes=["AC"],
                display_name="Alerting edge",
                description="Edge connecting alerted activity to account",
                properties=[],
            ),
        ],
        data_permission="dpv:demo_merchant",
    )


def entities() -> List[Graph]:
    return [graph()]
