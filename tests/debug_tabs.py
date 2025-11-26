from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Label

class DebugTabsApp(App):
    """A minimal app to verify Tabs work in your terminal."""
    
    # INLINE CSS: This overrides everything else.
    CSS = """
    Screen {
        background: #222222;
    }
    
    /* 1. Make the Tab container huge and red so we see if it exists */
    TabbedContent {
        height: 1fr;
        border: solid red; 
    }

    /* 2. Style the internal Tabs strip */
    Tabs {
        background: #0000FF; /* Blue background */
        height: 3;
        dock: top; /* This forces it to the top of the Red Box */
    }

    /* 3. Style the individual tabs */
    Tab {
        background: #444444;
        color: #ffffff;
        border: solid white;
    }

    /* 4. Active tab style */
    Tab.-active {
        background: #00FF00; /* Bright Green */
        color: #000000;
    }
    
    Label {
        padding: 2;
        /* font-size removed because terminals don't support it! */
        text-style: bold; 
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("If you see Blue/Green tabs below, your terminal is fine.")
        
        with TabbedContent(initial="tab1"):
            with TabPane("Tab 1", id="tab1"):
                yield Label("✅ Tab 1 Content is Visible")
            with TabPane("Tab 2", id="tab2"):
                yield Label("✅ Tab 2 Content is Visible")
        
        yield Footer()

if __name__ == "__main__":
    DebugTabsApp().run()