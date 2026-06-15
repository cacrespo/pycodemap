import os
from google import genai
from dotenv import load_dotenv

class AIAnalyzer:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.model_name = 'gemini-1.5-flash'
        else:
            self.client = None

    async def get_summary(self, graph_data):
        if not self.client:
            return "⚠️ Gemini API Key not found (.env GOOGLE_API_KEY)"
        
        nodes = list(graph_data.nodes)
        edges = list(graph_data.edges)
        
        prompt = f"""
        Analyze this code structure (call graph) and provide an executive summary of 3-4 lines
        about the system's architecture and purpose. Be concise and technical.
        
        Nodes (Components): {nodes}
        Edges (Interactions): {edges}
        """
        
        try:
            # The new SDK supports synchronous generation via client.models.generate_content
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Error contacting Gemini: {e}"
