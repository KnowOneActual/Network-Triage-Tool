"""DNS Resolver Widget for Phase 4.2."""

from src.tui.widgets.base import BaseWidget
from textual.app import ComposeResult

class DNSResolverWidget(BaseWidget):
    def __init__(self):
        super().__init__(name="DNSResolver")
    
    def compose(self) -> ComposeResult:
        yield from []
