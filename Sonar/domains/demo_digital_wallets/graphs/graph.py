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
        identifier="demo_dwallets_graph",
        nodes=[
            NodeType(
                identifier="AC",
                display_name="Account",
                description="Customer or counterparty account",
                encrypted=True,
                audited=True,
                properties=[
                    Property(
                        identifier="AN",
                        display_name="Account ID",
                        description="Unique identifier of the account (client_id or counterparty_id)",
                        type=DataType.STRING,
                        is_key=True,
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="NM",
                        display_name="Name",
                        description="Client or counterparty name",
                        type=DataType.STRING,
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="CN",
                        display_name="Country code",
                        description="Country of residence (for clients) or transaction country (for counterparties)",
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
                        description="Was the alerted activity",
                        type=DataType.BOOLEAN,
                    ),
                ],
            ),
            NodeType(
                identifier="PR",
                display_name="Party",
                description="Customer party (one per client_id)",
                encrypted=True,
                audited=True,
                write_allowed=True,
                properties=[
                    Property(
                        identifier="PI",
                        display_name="Party uuid",
                        description="Unique party identifier (client_id)",
                        type=DataType.STRING,
                        is_key=True,
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="NM",
                        display_name="Party name",
                        description="Party display name (client_name)",
                        type=DataType.STRING,
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="AD",
                        display_name="Party address",
                        description="Party address (from customer address)",
                        type=DataType.STRING,
                        reference=NodePropertyReference(
                            node_identifier="AC", property_identifier="AD"
                        ),
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="CT",
                        display_name="Party country code",
                        description="Country of residence code",
                        type=DataType.STRING,
                        encrypted=True,
                        audited=True,
                        reference=NodePropertyReference(
                            node_identifier="AC", property_identifier="CN"
                        ),
                    )
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
                identifier="ER",
                display_name="EMP Match",
                write_allowed=True,
                encrypted=True,
                audited=True,
                description="Edge from party to matched account",
                source_nodes=["PR"],
                target_nodes=["AC"],
                properties=[
                    Property(
                        identifier="ST",
                        display_name="State",
                        description="State of the candidate",
                        type=DataType.LONG,
                    ),
                    Property(
                        identifier="SC",
                        display_name="Score",
                        description="Score of the match",
                        type=DataType.DOUBLE,
                    ),
                ],
            ),
        ],
        data_permission="dpv:demo_digital_wallets",
    )


def entities() -> List[Graph]:
    return [graph()]
