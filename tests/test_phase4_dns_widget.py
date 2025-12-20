"""Phase 4.2 DNS Resolver Widget Tests."""

import sys
from pathlib import Path
import pytest

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tui.widgets.dns_resolver_widget import DNSResolverWidget


class TestDNSResolverWidget:
    """Tests for DNSResolverWidget."""
    
    def test_widget_initialization(self):
        """Test widget initializes correctly."""
        widget = DNSResolverWidget()
        # BaseWidget sets widget_name to the class name by default
        assert widget.widget_name == "DNSResolverWidget"
    
    def test_inherits_from_base_widget(self):
        """Test widget inherits from BaseWidget."""
        from tui.widgets.base import BaseWidget
        widget = DNSResolverWidget()
        assert isinstance(widget, BaseWidget)
    
    def test_has_required_methods(self):
        """Test widget has required methods from BaseWidget."""
        widget = DNSResolverWidget()
        # Methods inherited from BaseWidget
        assert hasattr(widget, 'display_error')
        assert hasattr(widget, 'display_success')
        assert hasattr(widget, 'show_loading')
        assert hasattr(widget, 'set_status')
        assert callable(widget.display_error)
        assert callable(widget.display_success)
        assert callable(widget.show_loading)
        assert callable(widget.set_status)
