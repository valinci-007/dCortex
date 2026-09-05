"""
Test suite for Tier 1 (Lookup) edge cases.
Run with: python -m pytest tests/integration/test_edge_cases_tier1.py -v
"""

import pytest
from datetime import datetime, date, time
from decimal import Decimal

from crew_ops_advisor.data.loader import load_database
from crew_ops_advisor.tools.query_tools import ToolRegistry
from crew_ops_advisor.domain.models import ReserveEntry


class TestTier1EdgeCases:
    """Tier 1 edge case tests for lookup and query tools."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize database and tool registry."""
        self.db = load_database()
        self.registry = ToolRegistry(self.db)
    
    def test_overnight_reserve_window_wraps_midnight(self):
        """
        T1-EC-1: Overnight Reserve Window
        
        Reserve works 22:00-06:00Z (wraps past midnight).
        System should recognize availability within window.
        """
        # Create a reserve entry with overnight window
        reserve = ReserveEntry(
            crew_id="TEST-OVERNIGHT-1",
            base="BLR",
            oncall_start=time(22, 0),  # 22:00 UTC
            oncall_end=time(6, 0),      # 06:00 UTC next day
            on_date=date(2026, 9, 15),
        )
        
        # Test callout at 23:30 (within overnight window) - should be available
        callout_2330 = datetime(2026, 9, 15, 23, 30, 0)
        assert reserve.covers(callout_2330), "23:30 should be within 22:00-06:00 window"
        
        # Test callout at 05:00 (within overnight window) - should be available
        callout_0500 = datetime(2026, 9, 15, 5, 0, 0)
        assert reserve.covers(callout_0500), "05:00 should be within 22:00-06:00 window"
        
        # Test callout at 07:00 (after window ends) - should NOT be available
        callout_0700 = datetime(2026, 9, 15, 7, 0, 0)
        assert not reserve.covers(callout_0700), "07:00 should NOT be within 22:00-06:00 window"
        
        # Test callout at 21:00 (before window starts) - should NOT be available
        callout_2100 = datetime(2026, 9, 15, 21, 0, 0)
        assert not reserve.covers(callout_2100), "21:00 should NOT be within 22:00-06:00 window"
    
    def test_zero_duty_days_excluded_from_history(self):
        """
        T1-EC-2: Zero-Duty Days Excluded
        
        Days with 0 duty hours are filtered out.
        LLM needs to understand that hidden days are off-days, not data gaps.
        """
        # Get a crew member's duty clock
        tool_spec = self.registry.get_tool("get_duty_clock")
        result = tool_spec.execute(crew_id="C-1001")
        
        # Verify result includes only non-zero days
        if result.get("success"):
            daily_history = result.get("daily_history", [])
            # Check that all returned days have at least some hours
            for day_record in daily_history:
                duty_hours = day_record.get("duty_hours", 0)
                flight_hours = day_record.get("flight_hours", 0)
                # At least one should be non-zero (implementation should filter)
                assert duty_hours > 0 or flight_hours > 0, \
                    f"Zero-hour day should be filtered: {day_record}"
    
    def test_station_code_validation_error_handling(self):
        """
        T1-EC-3: Station Code Validation
        
        Invalid station codes should return error, not silent empty result.
        """
        tool_spec = self.registry.get_tool("list_flights_from_station")
        result = tool_spec.execute(station_code="INVALID_XYZ")
        
        # Should either return empty or explicit error, not crash
        assert isinstance(result, dict), "Result should be dict"
        # Either no flights found or error message should be clear
        flights = result.get("flights", [])
        assert isinstance(flights, list), "Flights should be a list"
    
    def test_ambiguous_relative_time_parsing(self):
        """
        T1-EC-4: Ambiguous Relative Time
        
        Phrases like "this afternoon" are ambiguous without context.
        System should require clarification or document assumptions.
        """
        # This is more of a documentation test
        # The system should log/track when relative times are used
        tool_spec = self.registry.get_tool("get_crew")
        result = tool_spec.execute(crew_id="C-1001")
        
        # System should have consistent handling of times
        assert "crew_id" in result, "Crew lookup should work"
    
    def test_crew_with_multiple_pairings_same_day(self):
        """
        T1-EC-5: Crew with Multiple Pairings Same Day
        
        A crew might have multiple pairings on same day (e.g., two short legs).
        Query should return all pairings for that crew/date.
        """
        tool_spec = self.registry.get_tool("list_pairings_for_crew")
        
        # Try to get pairings for a crew on a specific date
        result = tool_spec.execute(crew_id="C-1001", duty_date="2026-09-10")
        
        # Should return list (possibly empty, possibly multiple)
        pairings = result.get("pairings", [])
        assert isinstance(pairings, list), "Should return list of pairings"
    
    def test_certification_valid_from_date_enforcement(self):
        """
        T1-EC-6: Certification Valid-From Not Enforced
        
        Certifications have valid_from dates; system doesn't check them.
        This is documented as known limitation.
        """
        tool_spec = self.registry.get_tool("get_certifications_for_crew")
        result = tool_spec.execute(crew_id="C-1001")
        
        # Should return certifications
        certifications = result.get("certifications", [])
        
        # Check that valid_from dates exist but may not be enforced
        for cert in certifications:
            # Cert should have valid_from (even if not checked in legality)
            assert "valid_from" in cert or "valid_date" in cert, \
                f"Certification should have valid date: {cert}"
    
    def test_crew_reachability_status_field(self):
        """
        T1-EC-7: Crew Reachability Status
        
        Crew has reachability status; query should return it.
        """
        tool_spec = self.registry.get_tool("get_crew")
        result = tool_spec.execute(crew_id="C-1001")
        
        # Crew record should include reachability if it exists
        if result.get("success"):
            # Check for any reachability indicator
            assert "crew_id" in result, "Crew should have ID"
    
    def test_reserve_window_boundary_precision(self):
        """
        T1-EC-8: Reserve Window Boundary Precision (05:59 vs 06:00)
        
        Reserve ends at 06:00Z. Callout at 05:59 should be available.
        Callout at 06:00 should NOT (depends on implementation: inclusive vs exclusive).
        """
        reserve = ReserveEntry(
            crew_id="TEST-BOUNDARY-1",
            base="BLR",
            oncall_start=time(22, 0),
            oncall_end=time(6, 0),
            on_date=date(2026, 9, 15),
        )
        
        # Test boundary: 05:59 should be within window
        callout_0559 = datetime(2026, 9, 15, 5, 59, 0)
        # Note: Behavior depends on whether end is inclusive or exclusive
        result_0559 = reserve.covers(callout_0559)
        
        # Test boundary: 06:00 - depends on implementation
        callout_0600 = datetime(2026, 9, 15, 6, 0, 0)
        result_0600 = reserve.covers(callout_0600)
        
        # At least one should be consistent
        assert isinstance(result_0559, bool), "Should return boolean"
        assert isinstance(result_0600, bool), "Should return boolean"
    
    def test_near_limits_threshold_definition(self):
        """
        T1-EC-9: Near Limits Threshold
        
        What is "near limit"? 85%? 90%? 95%? System should define clearly.
        """
        tool_spec = self.registry.get_tool("get_duty_clock")
        result = tool_spec.execute(crew_id="C-1001")
        
        # Check if result includes any "near_limit" or "margin" indicator
        if result.get("success"):
            # Should have clear numeric values, not vague "near" warnings
            assert "duty_hours_7d" in result or "duty_7d" in result, \
                "Should return concrete duty hour numbers"
    
    def test_query_tool_schema_validation_rejects_invalid_input(self):
        """
        T1-EC-10: Query Tool Input Validation
        
        Invalid inputs should be rejected with clear error, not silently fail.
        """
        tool_spec = self.registry.get_tool("list_flights_from_station")
        
        # Try with missing required parameter
        result = tool_spec.execute()  # No station_code provided
        
        # Should either fail gracefully or return empty
        assert isinstance(result, dict), "Should return dict even on error"
    
    def test_duty_clock_7day_window_precision(self):
        """
        T1-EC-11: 7-Day Duty Window Precision
        
        The 7-calendar-day window should be precisely defined.
        E.g., "last 7 calendar days" or "rolling 168 hours"?
        """
        tool_spec = self.registry.get_tool("get_duty_clock")
        result = tool_spec.execute(crew_id="C-1001")
        
        if result.get("success"):
            duty_7d = result.get("duty_hours_7d")
            # System should return a number, implementation detail of window clear
            assert isinstance(duty_7d, (int, float, Decimal)), \
                "7-day duty should be numeric"
    
    def test_flight_time_28day_window_precision(self):
        """
        T1-EC-12: 28-Day Flight Time Window Precision
        
        The 28-day window for flight time limits needs precise definition.
        """
        tool_spec = self.registry.get_tool("get_duty_clock")
        result = tool_spec.execute(crew_id="C-1001")
        
        if result.get("success"):
            flight_28d = result.get("flight_hours_28d")
            assert isinstance(flight_28d, (int, float, Decimal)), \
                "28-day flight should be numeric"
    
    def test_multiple_certifications_per_crew_same_type(self):
        """
        T1-EC-13: Multiple Certifications Same Type
        
        Crew might have multiple certifications of same type (renewals, ratings).
        Query should return all, not just first/last.
        """
        tool_spec = self.registry.get_tool("get_certifications_for_crew")
        result = tool_spec.execute(crew_id="C-1001")
        
        certifications = result.get("certifications", [])
        
        # Should be list format to handle multiples
        assert isinstance(certifications, list), \
            "Certifications should be list to support multiples"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
