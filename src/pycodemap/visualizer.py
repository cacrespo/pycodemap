from phart import ASCIIRenderer, LayoutOptions
import networkx as nx

class CodeVisualizer:
    def render_graph(self, G):
        if not G or G.number_of_nodes() == 0:
            return "No code structure found to visualize."
        
        # Use sensible defaults for phart
        options = LayoutOptions(
            layer_spacing=2,
            node_spacing=3,
            margin=1
        )
        
        renderer = ASCIIRenderer(G, options=options)
        return renderer.render()
