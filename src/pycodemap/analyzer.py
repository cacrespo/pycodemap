import os
import networkx as nx
from pyan import analyzer

class CodeAnalyzer:
    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)

    def get_python_files(self):
        py_files = []
        for root, _, files in os.walk(self.root_path):
            if ".venv" in root or ".git" in root or "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    py_files.append(os.path.join(root, file))
        return py_files

    def _shorten_name(self, name):
        # Moderate shortening: keep the last two parts if available
        # e.g. src.pycodemap.main.PyCodeMap -> main.PyCodeMap
        parts = name.split(".")
        if len(parts) > 2:
            return ".".join(parts[-2:])
        return name

    def analyze_call_graph(self, filter_path=None):
        files = self.get_python_files()
        if not files:
            return nx.DiGraph()

        v = analyzer.CallGraphVisitor(files, root=self.root_path)
        v.process()
        
        G = nx.DiGraph()
        
        # Helper to check if a node belongs to the filtered path
        def is_in_filter(node):
            if not filter_path or filter_path == self.root_path:
                return True
            # node.filename is the absolute path to the file where it's defined
            if not node.filename:
                return False
            return os.path.abspath(node.filename).startswith(os.path.abspath(filter_path))

        # Add nodes and edges only if they match the filter
        for node_list in v.nodes.values():
            for node in node_list:
                if node.defined and is_in_filter(node):
                    u_name = self._shorten_name(node.get_name())
                    G.add_node(u_name)

        for node, used_nodes in v.uses_edges.items():
            if node.defined and is_in_filter(node):
                u_name = self._shorten_name(node.get_name())
                for used_node in used_nodes:
                    # We show edges if the source is in the filter
                    # Even if the destination is outside (so we see external calls)
                    if used_node.defined:
                        v_name = self._shorten_name(used_node.get_name())
                        if u_name != v_name:
                            G.add_edge(u_name, v_name)
        return G
