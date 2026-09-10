from pathlib import Path

import networkx as nx

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree.semantic_kind import SemanticKind


class PythonExtractor:
    graph = nx.DiGraph()
    codebase: dict = {}

    def process(self, file: Path):
        root = PythonRstNode.load(file)
        module_name = root.filename.replace("/", ".").replace(".py", "")
        folder = str(Path(file).parent)
        self.graph.add_node(folder, type="folder")
        self.graph.add_edge(folder, module_name, type="contains")

        for stmt in root:
            match stmt.semantic_kind:
                case SemanticKind.IMPORT:
                    self.graph.add_edge(module_name, stmt.name, type="include")
                case _ if stmt.parser_kind == "ImportFrom":
                    for alias in stmt.node.names:
                        self.graph.add_edge(module_name, f"{stmt.node.module}.{alias.name}", type="include")
                case SemanticKind.FUNCTION:
                    self.graph.add_edge(module_name, f"{module_name}.{stmt.name}", type="definition")
                    self.graph.add_node(f"{module_name}.{stmt.name}", properties="function")
                    # TODO:  convert #, stmt.properties) to graphml
                case SemanticKind.CLASS:
                    self.graph.add_edge(module_name, f"{module_name}.{stmt.name}", type="definition")
                    self.graph.add_node(f"{module_name}.{stmt.name}")  # convert to args, stmt.properties)
                case _:
                    pass

        self.codebase[file] = root
        # # reconstruct dependencies inside module
        # tu.lazy_create_refers(root)
        # self.nodes |= tu._nodes
        # self.edges |=tu._references
        # self.edges |= tu._referenced_by

    def save_graph(self, filename: str):
        nx.write_graphml(self.graph, filename)
        print(f"Graph saved to: {filename}")
