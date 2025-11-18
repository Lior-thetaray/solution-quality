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
        identifier="demo_ret_indiv_graph",
        nodes=[
            NodeType(
                identifier="AC",
                display_name="Account",
                description="Bank Account",
                encrypted=True,
                audited=True,
                properties=[
                    Property(
                        identifier="AN",
                        display_name="IBAN",
                        description="The account IBAN",
                        type=DataType.STRING,
                        is_key=True,
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="NM",
                        display_name="Full name",
                        description="Display name of the account",
                        type=DataType.STRING,
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="CT",
                        display_name="Country",
                        description="The country of the account",
                        type=DataType.STRING,
                        encrypted=True,
                    ),
                    Property(
                        identifier="AD",
                        display_name="Address",
                        description="The address of the account",
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
                display_name="Party of accounts",
                description="Party of accounts",
                encrypted=True,
                audited=True,
                write_allowed=True,
                properties=[
                    Property(
                        identifier="PI",
                        display_name="Party uuid",
                        description="Accounts party uuid",
                        type=DataType.STRING,
                        is_key=True,
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="NM",
                        display_name="Party name",
                        description="Accounts party name",
                        type=DataType.STRING,
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="AD",
                        display_name="Party address",
                        description="Accounts party address",
                        type=DataType.STRING,
                        reference=NodePropertyReference(
                            node_identifier="AC", property_identifier="AD"
                        ),
                        encrypted=True,
                        audited=True,
                    ),
                    Property(
                        identifier="CT",
                        display_name="Party country",
                        description="Accounts party country",
                        type=DataType.STRING,
                        encrypted=True,
                        audited=True,
                        reference=NodePropertyReference(
                            node_identifier="AC", property_identifier="CT"
                        ),
                    ),
                    Property(
                        identifier="CN",
                        display_name="Consolidation flag",
                        description="Consolidation flag",
                        type=DataType.LONG,
                    ),
                    Property(
                        identifier="UON",
                        display_name="Updated on",
                        description="Last updated date",
                        type=DataType.TIMESTAMP,
                    ),
                    Property(
                        identifier="UBY",
                        display_name="Updated by",
                        description="User updated the party",
                        type=DataType.STRING,
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
                        identifier="CR",
                        display_name="Currency",
                        description="The transaction currency",
                        type=DataType.STRING,
                    ),
                    Property(
                        identifier="CT",
                        display_name="Transactions count",
                        description="Amount of transactions, represented by the edge",
                        type=DataType.LONG,
                    ),
                ],
            ),
            EdgeType(
                identifier="AL",
                source_nodes=["AL"],
                target_nodes=["AC", "PR"],
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
        data_permission="dpv:demo_ret_indiv",
    )


def entities() -> List[Graph]:
    return [graph()]
