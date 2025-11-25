from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Label, Markdown
from textual.binding import Binding

class NetworkTriageApp(App):
    """A Textual TUI for Network Triage."""

    CSS = """
    /* Global "Slick" Styles */
    Screen {
        layout: vertical;
    }
    
    Header {
        dock: top;
        height: 3;
        content-align: center middle;
    }

    Footer {
        dock: bottom;
    }
    """

    # Keyboard shortcuts - making it fast to use
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "show_tab('dashboard')", "Dashboard"),
        Binding("c", "show_tab('connection')", "Connection"),
        Binding("p", "show_tab('ping')", "Ping"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with TabbedContent(initial="dashboard", id="main_tabs"):
            with TabPane("Dashboard", id="dashboard"):
                yield Label("System Info will go here", id="status_label")
                
            with TabPane("Connection", id="connection"):
                yield Label("Interface details will go here")
                
            with TabPane("Ping", id="ping"):
                yield Label("Ping tool will go here")

        yield Footer()

    def action_show_tab(self, tab: str) -> None:
        """Switch tabs using keyboard shortcuts."""
        self.query_one("#main_tabs").active = tab

if __name__ == "__main__":
    app = NetworkTriageApp()
    app.run()