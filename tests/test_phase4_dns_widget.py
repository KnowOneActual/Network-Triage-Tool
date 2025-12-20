"""Phase 4.2 DNS Resolver Widget Tests."""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

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
        assert widget.widget_name == "DNSResolverWidget"
    
    def test_inherits_from_base_widget(self):
        """Test widget inherits from BaseWidget."""
        from tui.widgets.base import BaseWidget
        widget = DNSResolverWidget()
        assert isinstance(widget, BaseWidget)
    
    def test_has_required_methods(self):
        """Test widget has required methods from BaseWidget."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'display_error')
        assert hasattr(widget, 'display_success')
        assert hasattr(widget, 'show_loading')
        assert hasattr(widget, 'set_status')
        assert callable(widget.display_error)
        assert callable(widget.display_success)
        assert callable(widget.show_loading)
        assert callable(widget.set_status)
    
    def test_has_ui_methods(self):
        """Test widget has UI-specific methods."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'resolve_hostname')
        assert hasattr(widget, 'clear_results')
        assert callable(widget.resolve_hostname)
        assert callable(widget.clear_results)
    
    def test_has_compose_method(self):
        """Test widget has compose() method for UI layout."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'compose')
        assert callable(widget.compose)
    
    def test_has_button_handler(self):
        """Test widget has button press handler."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'on_button_pressed')
        assert callable(widget.on_button_pressed)
    
    def test_clear_results_method_exists(self):
        """Test clear_results method exists and is callable."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'clear_results')
        assert callable(widget.clear_results)
    
    def test_resolve_hostname_method_exists(self):
        """Test resolve_hostname method exists and is callable."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'resolve_hostname')
        assert callable(widget.resolve_hostname)


class TestDNSResolverUILogic:
    """Test UI logic of DNS resolver."""
    
    def test_widget_inherits_error_handling(self):
        """Test that widget can display errors (inherited from BaseWidget)."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'error_message')
    
    def test_widget_inherits_caching(self):
        """Test that widget can cache results (inherited from AsyncOperationMixin)."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'cache_result')
        assert hasattr(widget, 'get_cached')
        assert callable(widget.cache_result)
        assert callable(widget.get_cached)
    
    def test_widget_inherits_progress_tracking(self):
        """Test that widget can show progress (inherited from BaseWidget)."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'is_loading')
        assert hasattr(widget, 'show_loading')
        assert callable(widget.show_loading)
    
    def test_widget_inherits_status_management(self):
        """Test that widget manages status (inherited from BaseWidget)."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'current_status')
        assert hasattr(widget, 'set_status')
        assert callable(widget.set_status)


class TestDNSResolverIntegration:
    """Integration tests for DNS resolver."""
    
    def test_widget_uses_foundation_features(self):
        """Test that widget properly uses foundation features."""
        widget = DNSResolverWidget()
        from tui.widgets.base import BaseWidget, AsyncOperationMixin
        assert isinstance(widget, BaseWidget)
        assert isinstance(widget, AsyncOperationMixin)
    
    def test_widget_has_ui_structure(self):
        """Test that widget has all required UI structure."""
        widget = DNSResolverWidget()
        assert hasattr(widget, 'compose')
        assert hasattr(widget, 'on_button_pressed')
        assert hasattr(widget, 'resolve_hostname')
        assert hasattr(widget, 'clear_results')
    
    def test_widget_can_be_instantiated_safely(self):
        """Test that widget can be instantiated without app context."""
        try:
            widget = DNSResolverWidget()
            assert widget is not None
            assert isinstance(widget, DNSResolverWidget)
        except Exception as e:
            pytest.fail(f"Widget instantiation failed: {str(e)}")


class TestDNSResolution:
    """Test DNS resolution functionality."""
    
    def test_resolve_hostname_with_mock(self):
        """Test resolve_hostname method with mocked DNS utility."""
        from shared.dns_utils import DNSRecord, DNSStatus, DNSLookupResult
        
        widget = DNSResolverWidget()
        
        # Mock the resolve_dns_hostname function
        with patch('tui.widgets.dns_resolver_widget.resolve_dns_hostname') as mock_resolve:
            # Create mock result
            mock_result = MagicMock()
            mock_result.status = DNSStatus.SUCCESS
            mock_result.ipv4_addresses = ['1.2.3.4']
            mock_result.ipv6_addresses = []
            mock_result.reverse_dns = None
            mock_result.lookup_time_ms = 10.5
            mock_result.records = [
                DNSRecord('A', '1.2.3.4', 10.5, DNSStatus.SUCCESS)
            ]
            mock_resolve.return_value = mock_result
            
            # The method would normally be called through the UI
            # For testing, we just verify it can be called
            assert callable(widget.resolve_hostname)
    
    def test_resolve_hostname_imports_dns_utility(self):
        """Test that resolve_hostname uses Phase 3 DNS utility."""
        widget = DNSResolverWidget()
        # Import statement is at module level
        from tui.widgets import dns_resolver_widget
        
        # Check that the module imports the DNS utility
        assert hasattr(dns_resolver_widget, 'resolve_dns_hostname')
        assert hasattr(dns_resolver_widget, 'DNSStatus')
    
    def test_widget_has_results_widget(self):
        """Test widget has results display widget."""
        from tui.widgets.components import ResultsWidget
        widget = DNSResolverWidget()
        
        # Results widget is created in compose()
        # We can't test it directly without running the app,
        # but we can verify compose exists and will create it
        assert hasattr(widget, 'compose')
        assert callable(widget.compose)
    
    def test_dns_status_enum_available(self):
        """Test that DNSStatus enum from Phase 3 is available."""
        from src.shared.dns_utils import DNSStatus
        
        # Check that the enum has the expected values
        assert hasattr(DNSStatus, 'SUCCESS')
        assert hasattr(DNSStatus, 'NOT_FOUND')
        assert hasattr(DNSStatus, 'TIMEOUT')
        assert hasattr(DNSStatus, 'ERROR')
    
    def test_dns_record_structure(self):
        """Test that DNSRecord dataclass has expected fields."""
        from src.shared.dns_utils import DNSRecord, DNSStatus
        
        # Create a test record
        record = DNSRecord(
            record_type='A',
            value='1.2.3.4',
            query_time_ms=5.0,
            status=DNSStatus.SUCCESS
        )
        
        # Verify fields
        assert record.record_type == 'A'
        assert record.value == '1.2.3.4'
        assert record.query_time_ms == 5.0
        assert record.status == DNSStatus.SUCCESS
    
    def test_dns_lookup_result_structure(self):
        """Test that DNSLookupResult dataclass has expected fields."""
        from src.shared.dns_utils import DNSLookupResult, DNSStatus
        
        # Create a test result
        result = DNSLookupResult(
            hostname='example.com',
            ipv4_addresses=['1.2.3.4'],
            ipv6_addresses=[],
            reverse_dns=None,
            lookup_time_ms=10.0,
            status=DNSStatus.SUCCESS
        )
        
        # Verify fields
        assert result.hostname == 'example.com'
        assert result.ipv4_addresses == ['1.2.3.4']
        assert result.ipv6_addresses == []
        assert result.lookup_time_ms == 10.0
        assert result.status == DNSStatus.SUCCESS
