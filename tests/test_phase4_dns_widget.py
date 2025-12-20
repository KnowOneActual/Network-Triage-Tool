"""Phase 4.2 DNS Resolver Widget Tests."""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

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
        # compose() is defined in the widget
        assert hasattr(widget, 'compose')
        assert callable(widget.compose)
    
    def test_has_button_handler(self):
        """Test widget has button press handler."""
        widget = DNSResolverWidget()
        # on_button_pressed should be defined
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
        # Should not raise an error
        try:
            # This would normally update the UI, but we're testing the method exists
            assert hasattr(widget, 'error_message')
        except Exception as e:
            pytest.fail(f"Error handling failed: {str(e)}")
    
    def test_widget_inherits_caching(self):
        """Test that widget can cache results (inherited from AsyncOperationMixin)."""
        widget = DNSResolverWidget()
        # Should have cache methods from AsyncOperationMixin
        assert hasattr(widget, 'cache_result')
        assert hasattr(widget, 'get_cached')
        assert callable(widget.cache_result)
        assert callable(widget.get_cached)
    
    def test_widget_inherits_progress_tracking(self):
        """Test that widget can show progress (inherited from BaseWidget)."""
        widget = DNSResolverWidget()
        # Should have progress methods from BaseWidget
        assert hasattr(widget, 'is_loading')
        assert hasattr(widget, 'show_loading')
        assert callable(widget.show_loading)
    
    def test_widget_inherits_status_management(self):
        """Test that widget manages status (inherited from BaseWidget)."""
        widget = DNSResolverWidget()
        # Should have status methods from BaseWidget
        assert hasattr(widget, 'current_status')
        assert hasattr(widget, 'set_status')
        assert callable(widget.set_status)


class TestDNSResolverIntegration:
    """Integration tests for DNS resolver."""
    
    def test_widget_uses_foundation_features(self):
        """Test that widget properly uses foundation features."""
        widget = DNSResolverWidget()
        
        # Check inheritance chain
        from tui.widgets.base import BaseWidget, AsyncOperationMixin
        assert isinstance(widget, BaseWidget)
        assert isinstance(widget, AsyncOperationMixin)
    
    def test_widget_has_ui_structure(self):
        """Test that widget has all required UI structure."""
        widget = DNSResolverWidget()
        
        # Widget should have compose method
        assert hasattr(widget, 'compose')
        
        # Widget should have button handler
        assert hasattr(widget, 'on_button_pressed')
        
        # Widget should have resolve and clear methods
        assert hasattr(widget, 'resolve_hostname')
        assert hasattr(widget, 'clear_results')
    
    def test_widget_can_be_instantiated_safely(self):
        """Test that widget can be instantiated without app context."""
        # This is important for testing - widget should initialize
        # without requiring a full Textual app context
        try:
            widget = DNSResolverWidget()
            assert widget is not None
            assert isinstance(widget, DNSResolverWidget)
        except Exception as e:
            pytest.fail(f"Widget instantiation failed: {str(e)}")
