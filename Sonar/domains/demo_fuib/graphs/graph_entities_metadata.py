from thetaray.api.solution import Graph, NodeType, EdgeType, Property, DataType


def graph() -> Graph:
    return Graph(
        identifier="fuib_graph",
        nodes=[
            NodeType(identifier="AC", display_name="Account", description="Account", properties=[
                Property(identifier="AN", display_name="Account Number",
                         description="The account number", type=DataType.STRING, is_key=True),
                Property(identifier="NM", display_name="Account Name",
                         description="Display name of the account", type=DataType.STRING),
                Property(identifier="CT", display_name="Country",
                         description="Country of account", type=DataType.STRING),
            ]),
   
            NodeType(identifier="AL", display_name="Alerted activity", description="Alerted activity", properties=[
                Property(identifier="AI", display_name="Alerted activity ID",
                         description="Alerted activity ID", type=DataType.STRING),
                Property(identifier="RI", display_name="Risk identifier",
                         description="Risk ID", type=DataType.STRING),
                Property(identifier="SP", display_name="Suppressed",
                         description="Was the alerted activity suppressed", type=DataType.BOOLEAN)
            ])],
        edges=[
            EdgeType(identifier="TX", display_name="Transaction",
                     description="The transaction from one account to another", properties=[
                        Property(identifier="AM", display_name="Amount",
                                 description="The transaction amount", type=DataType.DOUBLE),
                        Property(identifier="CR", display_name="Currency",
                                 description="The transaction currency", type=DataType.STRING),
                        Property(identifier="CT", display_name="Transactions count",
                                 description="Amount of transactions, represented by the edge", type=DataType.LONG)
                     ],
                    source_nodes=['AC'],
                    target_nodes=['AC']),
            EdgeType(identifier="AL", display_name="Alerting edge",
                     description="Edge, connecting alerted activity to account", properties=[],
                     source_nodes=['AL'],
                     target_nodes=['AC'])
        ],
        data_permission="dpv:demo_fuib"
    )


def entities():
    return [graph()]