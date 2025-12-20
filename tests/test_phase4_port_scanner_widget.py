"""Phase 4.3 Port Scanner Widget Tests."""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tui.widgets.port_scanner_widget import PortScannerWidget


class TestPortScannerWidgetInitialization:
    """Tests for PortScannerWidget initialization."""
    
    def test_widget_initialization(self):
        """Test widget initializes correctly."""
        widget = PortScannerWidget()
        assert widget.widget_name == "PortScannerWidget"
    
    def test_scan_in_progress_flag_initialized(self):
        """Test scan_in_progress flag is initialized to False."""
        widget = PortScannerWidget()
        assert widget.scan_in_progress is False
    
    def test_inherits_from_base_widget(self):
        """Test widget inherits from BaseWidget."""
        from tui.widgets.base import BaseWidget
        widget = PortScannerWidget()
        assert isinstance(widget, BaseWidget)
    
    def test_has_required_methods(self):
        """Test widget has required methods from BaseWidget."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'display_error')
        assert hasattr(widget, 'display_success')
        assert hasattr(widget, 'show_loading')
        assert hasattr(widget, 'set_status')
        assert callable(widget.display_error)
        assert callable(widget.display_success)
        assert callable(widget.show_loading)
        assert callable(widget.set_status)


class TestPortScannerUIMethods:
    """Tests for Port Scanner UI methods."""
    
    def test_has_compose_method(self):
        """Test widget has compose() method for UI layout."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'compose')
        assert callable(widget.compose)
    
    def test_has_button_handler(self):
        """Test widget has button press handler."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'on_button_pressed')
        assert callable(widget.on_button_pressed)
    
    def test_has_select_handler(self):
        """Test widget has select change handler."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'on_select_changed')
        assert callable(widget.on_select_changed)
    
    def test_has_scan_method(self):
        """Test widget has scan_ports method."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'scan_ports')
        assert callable(widget.scan_ports)
    
    def test_has_clear_method(self):
        """Test widget has clear_results method."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'clear_results')
        assert callable(widget.clear_results)
    
    def test_has_parse_ports_method(self):
        """Test widget has parse_ports_input method."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'parse_ports_input')
        assert callable(widget.parse_ports_input)


class TestPortParsingLogic:
    """Tests for port input parsing."""
    
    def test_parse_single_port_valid(self):
        """Test parsing valid single port."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("80", "single")
        assert result == [80]
    
    def test_parse_single_port_invalid_string(self):
        """Test parsing invalid single port (non-numeric)."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("abc", "single")
        assert result is None
    
    def test_parse_single_port_out_of_range_low(self):
        """Test parsing port number below valid range."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("0", "single")
        assert result is None
    
    def test_parse_single_port_out_of_range_high(self):
        """Test parsing port number above valid range."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("65536", "single")
        assert result is None
    
    def test_parse_single_port_boundary_min(self):
        """Test parsing minimum valid port (1)."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("1", "single")
        assert result == [1]
    
    def test_parse_single_port_boundary_max(self):
        """Test parsing maximum valid port (65535)."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("65535", "single")
        assert result == [65535]
    
    def test_parse_multiple_ports_valid(self):
        """Test parsing valid multiple ports."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("80,443,22", "multiple")
        assert sorted(result) == [22, 80, 443]
    
    def test_parse_multiple_ports_with_spaces(self):
        """Test parsing multiple ports with spaces."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("80, 443, 22", "multiple")
        assert sorted(result) == [22, 80, 443]
    
    def test_parse_multiple_ports_removes_duplicates(self):
        """Test parsing multiple ports removes duplicates."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("80,443,80,22", "multiple")
        assert sorted(result) == [22, 80, 443]
    
    def test_parse_multiple_ports_invalid_format(self):
        """Test parsing invalid multiple port format."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("80,abc,443", "multiple")
        assert result is None
    
    def test_parse_multiple_ports_empty(self):
        """Test parsing empty port list."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("", "multiple")
        assert result is None
    
    def test_parse_range_valid(self):
        """Test parsing valid port range."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("80-85", "range")
        assert result == [80, 81, 82, 83, 84, 85]
    
    def test_parse_range_with_spaces(self):
        """Test parsing port range with spaces."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("80 - 85", "range")
        assert result == [80, 81, 82, 83, 84, 85]
    
    def test_parse_range_reversed(self):
        """Test parsing port range with start > end (should swap)."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("443-80", "range")
        assert result == [80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443]
    
    def test_parse_range_invalid_format(self):
        """Test parsing invalid range format."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("80:443", "range")
        assert result is None
    
    def test_parse_range_too_large(self):
        """Test parsing range that exceeds maximum limit (5000 ports)."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("1-10000", "range")
        assert result is None
    
    def test_parse_range_at_limit(self):
        """Test parsing range at maximum limit (5000 ports)."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("1-5000", "range")
        assert result is not None
        assert len(result) == 5000


class TestPortScannerFoundationFeatures:
    """Tests for Port Scanner using foundation features."""
    
    def test_widget_uses_foundation(self):
        """Test that widget properly uses foundation features."""
        widget = PortScannerWidget()
        from tui.widgets.base import BaseWidget, AsyncOperationMixin
        assert isinstance(widget, BaseWidget)
        assert isinstance(widget, AsyncOperationMixin)
    
    def test_widget_has_error_handling(self):
        """Test that widget can display errors (inherited from BaseWidget)."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'error_message')
    
    def test_widget_has_caching(self):
        """Test that widget can cache results (inherited from AsyncOperationMixin)."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'cache_result')
        assert hasattr(widget, 'get_cached')
        assert callable(widget.cache_result)
        assert callable(widget.get_cached)
    
    def test_widget_has_progress_tracking(self):
        """Test that widget can show progress (inherited from BaseWidget)."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'is_loading')
        assert hasattr(widget, 'show_loading')
        assert callable(widget.show_loading)
    
    def test_widget_has_status_management(self):
        """Test that widget manages status (inherited from BaseWidget)."""
        widget = PortScannerWidget()
        assert hasattr(widget, 'current_status')
        assert hasattr(widget, 'set_status')
        assert callable(widget.set_status)


class TestPortScannerIntegration:
    """Integration tests for Port Scanner."""
    
    def test_widget_can_be_instantiated_safely(self):
        """Test that widget can be instantiated without app context."""
        try:
            widget = PortScannerWidget()
            assert widget is not None
            assert isinstance(widget, PortScannerWidget)
        except Exception as e:
            pytest.fail(f"Widget instantiation failed: {str(e)}")
    
    def test_port_status_enum_available(self):
        """Test that PortStatus enum from Phase 3 is available."""
        from shared.port_utils import PortStatus
        
        # Check that the enum has the expected values
        assert hasattr(PortStatus, 'OPEN')
        assert hasattr(PortStatus, 'CLOSED')
        assert hasattr(PortStatus, 'FILTERED')
        assert hasattr(PortStatus, 'TIMEOUT')
        assert hasattr(PortStatus, 'ERROR')
    
    def test_port_check_result_structure(self):
        """Test that PortCheckResult dataclass has expected fields."""
        from shared.port_utils import PortCheckResult, PortStatus
        
        # Create a test result
        result = PortCheckResult(
            host='localhost',
            port=80,
            status=PortStatus.OPEN,
            service_name='HTTP',
            response_time_ms=5.0
        )
        
        # Verify fields
        assert result.host == 'localhost'
        assert result.port == 80
        assert result.status == PortStatus.OPEN
        assert result.service_name == 'HTTP'
        assert result.response_time_ms == 5.0
    
    def test_common_service_ports_available(self):
        """Test that COMMON_SERVICE_PORTS is available from Phase 3."""
        from shared.port_utils import COMMON_SERVICE_PORTS
        
        # Check that common ports are available
        assert 22 in COMMON_SERVICE_PORTS  # SSH
        assert 80 in COMMON_SERVICE_PORTS  # HTTP
        assert 443 in COMMON_SERVICE_PORTS  # HTTPS
        assert COMMON_SERVICE_PORTS[22] == 'SSH'
        assert COMMON_SERVICE_PORTS[80] == 'HTTP'
        assert COMMON_SERVICE_PORTS[443] == 'HTTPS'


class TestPortScannerPhase3Integration:
    """Test integration with Phase 3 port utilities."""
    
    def test_imports_port_utilities(self):
        """Test that widget imports required port utilities."""
        from tui.widgets import port_scanner_widget
        
        # Check that the module imports the required functions
        assert hasattr(port_scanner_widget, 'check_port_open')
        assert hasattr(port_scanner_widget, 'check_multiple_ports')
        assert hasattr(port_scanner_widget, 'PortStatus')
        assert hasattr(port_scanner_widget, 'COMMON_SERVICE_PORTS')
        assert hasattr(port_scanner_widget, 'summarize_port_scan')
    
    def test_check_multiple_ports_available(self):
        """Test that check_multiple_ports utility is available."""
        from shared.port_utils import check_multiple_ports
        assert callable(check_multiple_ports)
    
    def test_summarize_port_scan_available(self):
        """Test that summarize_port_scan utility is available."""
        from shared.port_utils import summarize_port_scan
        assert callable(summarize_port_scan)
    
    def test_summarize_port_scan_result_structure(self):
        """Test the structure of summarize_port_scan results."""
        from shared.port_utils import summarize_port_scan, PortCheckResult, PortStatus
        
        # Create mock results
        results = [
            PortCheckResult('localhost', 22, PortStatus.OPEN, 'SSH', 5.0),
            PortCheckResult('localhost', 80, PortStatus.OPEN, 'HTTP', 5.0),
            PortCheckResult('localhost', 443, PortStatus.CLOSED, 'HTTPS', 3.0),
        ]
        
        # Summarize
        summary = summarize_port_scan(results)
        
        # Verify structure
        assert 'total_scanned' in summary
        assert 'open_count' in summary
        assert 'closed_count' in summary
        assert 'filtered_count' in summary
        assert 'avg_response_time_ms' in summary
        assert summary['total_scanned'] == 3
        assert summary['open_count'] == 2
        assert summary['closed_count'] == 1


class TestPortScannerEdgeCases:
    """Edge case tests for Port Scanner."""
    
    def test_parse_ports_empty_input(self):
        """Test parsing with empty input."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("", "single")
        # Empty input should fail
        assert result is None or result == []
    
    def test_parse_ports_whitespace_only(self):
        """Test parsing with whitespace only."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("   ", "single")
        assert result is None
    
    def test_parse_multiple_with_invalid_port_in_list(self):
        """Test that single invalid port in list fails entire parse."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("80,443,99999", "multiple")
        assert result is None
    
    def test_parse_range_single_port(self):
        """Test range with same start and end port."""
        widget = PortScannerWidget()
        result = widget.parse_ports_input("80-80", "range")
        assert result == [80]
    
    def test_scan_in_progress_flag_prevents_concurrent_scans(self):
        """Test that scan_in_progress flag prevents concurrent scans."""
        widget = PortScannerWidget()
        widget.scan_in_progress = True
        
        # Mock the display_error method
        with patch.object(widget, 'display_error') as mock_error:
            widget.scan_ports()
            # Should display error about scan already in progress
            mock_error.assert_called()


class TestPortScannerDocstring:
    """Test that widget has proper documentation."""
    
    def test_widget_has_docstring(self):
        """Test widget class has docstring."""
        assert PortScannerWidget.__doc__ is not None
        assert len(PortScannerWidget.__doc__) > 0
    
    def test_parse_ports_input_has_docstring(self):
        """Test parse_ports_input method has docstring."""
        widget = PortScannerWidget()
        assert widget.parse_ports_input.__doc__ is not None
    
    def test_scan_ports_has_docstring(self):
        """Test scan_ports method has docstring."""
        widget = PortScannerWidget()
        assert widget.scan_ports.__doc__ is not None
    
    def test_clear_results_has_docstring(self):
        """Test clear_results method has docstring."""
        widget = PortScannerWidget()
        assert widget.clear_results.__doc__ is not None
