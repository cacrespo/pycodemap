from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree, Static
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual import work
from .analyzer import CodeAnalyzer
from .visualizer import CodeVisualizer
from .ai_client import AIAnalyzer
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            self.callback()

    def on_created(self, event):
        if event.src_path.endswith(".py"):
            self.callback()


class PyCodeMap(App):
    CSS = """
    Screen {
        background: #1e1e1e;
    }

    #sidebar {
        width: 30;
        border-right: solid $accent;
        background: #252526;
    }

    #legend-panel {
        height: auto;
        border-top: solid $accent;
        padding: 1 2;
        background: #252526;
        color: $text-muted;
    }

    #main-view {
        width: 1fr;
    }

    #summary-panel {
        height: 6;
        border-bottom: solid $accent;
        background: #1e1e1e;
        padding: 1 2;
        color: $text;
        text-style: italic;
    }

    #diagram-container {
        height: 1fr;
        padding: 1 2;
        background: #1e1e1e;
    }

    #diagram-content {
        width: auto;
        height: auto;
    }
    """

    TITLE = "pyCodeMap"
    SUB_TITLE = "TUI Code Visualizer + AI"
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
        ("h", "scroll_left", "Left"),
        ("j", "scroll_down", "Down"),
        ("k", "scroll_up", "Up"),
        ("l", "scroll_right", "Right"),
    ]

    def action_scroll_left(self) -> None:
        self.query_one("#diagram-container").scroll_left(animate=False)

    def action_scroll_right(self) -> None:
        self.query_one("#diagram-container").scroll_right(animate=False)

    def action_scroll_up(self) -> None:
        self.query_one("#diagram-container").scroll_up(animate=False)

    def action_scroll_down(self) -> None:
        self.query_one("#diagram-container").scroll_down(animate=False)

    def __init__(self, root_path="."):
        super().__init__()
        self.root_path = os.path.abspath(root_path)
        self.current_filter = self.root_path
        self.analyzer = CodeAnalyzer(self.root_path)
        self.visualizer = CodeVisualizer()
        self.ai = AIAnalyzer()
        self.observer = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield DirectoryTree(self.root_path, id="tree")
                yield Static(
                    "[bold]LEGEND[/bold]\n"
                    "[blue]──→[/blue] Call / Dependency\n"
                    "[green][A][/green]  Module / Function\n"
                    "HJKL: move | Click: Filter",
                    id="legend-panel"
                )
            with Vertical(id="main-view"):
                yield Static("AI Summary will load here...", id="summary-panel")
                with VerticalScroll(id="diagram-container"):
                    yield Static("Analyzing code...", id="diagram-content")
        yield Footer()

    def on_mount(self) -> None:
        self.title = self.TITLE
        self.sub_title = self.SUB_TITLE
        self.refresh_all()
        self.start_watcher()

    def start_watcher(self):
        event_handler = CodeChangeHandler(
            lambda: self.call_from_thread(self.refresh_all)
        )
        self.observer = Observer()
        self.observer.schedule(event_handler, self.root_path, recursive=True)
        self.observer.start()

    def on_unmount(self) -> None:
        if self.observer:
            self.observer.stop()
            self.observer.join()

    @work(exclusive=True)
    async def refresh_all(self) -> None:
        diagram_static = self.query_one("#diagram-content", Static)
        summary_static = self.query_one("#summary-panel", Static)

        try:
            # 1. Analyze code with current filter
            graph = self.analyzer.analyze_call_graph(filter_path=self.current_filter)

            # 2. Update Diagram
            diagram = self.visualizer.render_graph(graph)
            diagram_static.update(diagram)

            # 3. Update AI Summary (always summarize the whole project or just the filter?)
            # Let's summarize the whole project for context, or we can use the graph too.
            summary_static.update("✨ Gemini is analyzing the architecture...")
            summary = await self.ai.get_summary(graph)
            summary_static.update(f"🤖 [bold]AI Summary:[/bold] {summary}")

        except Exception as e:
            diagram_static.update(f"Error: {e}")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.current_filter = str(event.path)
        self.sub_title = f"Viewing: {os.path.basename(self.current_filter)}"
        self.refresh_all()

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        self.current_filter = str(event.path)
        self.sub_title = f"Viewing folder: {os.path.basename(self.current_filter)}"
        self.refresh_all()

    def action_refresh(self) -> None:
        self.current_filter = self.root_path  # Reset filter on manual refresh
        self.sub_title = self.SUB_TITLE
        self.refresh_all()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="pyCodeMap: TUI for code visualization with AI."
    )
    parser.add_argument("path", nargs="?", default=".", help="Directory to analyze")
    args = parser.parse_args()

    app = PyCodeMap(root_path=args.path)
    app.run()


if __name__ == "__main__":
    main()
