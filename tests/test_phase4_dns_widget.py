import sys
from pathlib import Path
import pytest

src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tui.widgets.dns_resolver_widget import DNSResolverWidget

class TestDNSResolverWidget:
    def test_widget_initialization(self):
        widget = DNSResolverWidget()
        assert widget.widget_name == "DNSResolver"

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
        assert widget.widget_name == "DNSResolver"
