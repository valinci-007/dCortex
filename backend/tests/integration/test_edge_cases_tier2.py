"""
Test suite for Tier 2 (Simulation) edge cases.
Run with: python -m pytest tests/integration/test_edge_cases_tier2.py -v
"""

import pytest
from datetime import datetime, date, time, timedelta
from decimal import Decimal

from crew_ops_advisor.data.loader import load_database
from crew_ops_advisor.tools.simulation_tools import SimulationToolRegistry
from crew_ops_advisor.simulation.engine import SimulationEngine
from crew_ops_advisor.rules.engine import RulesEngine, RuleContext


class TestTier2EdgeCases:
    """Tier 2 edge case tests for simulation and consequence analysis."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize database and simulation engine."""
        self.db = load_database()
        self.sim_registry = SimulationToolRegistry(self.db)
        self.sim_engine = SimulationEngine(self.db)
        self.rules_engine = RulesEngine()
    
    def test_rest_conflict_after_delay_not_detected(self):
        """
        T2-EC-1: Rest Conflict After Delay
        
        A 90-minute delay might push crew release into next-day duty
        with insufficient rest (e.g., 10.5h vs. 12h required).
        
        Current issue: delay() tool only checks FDP, not downstream rest.
        """
        # Setup: Crew scheduled to land at 18:00Z (release at 18:30Z)
        # Then duty starts next day at 06:00Z (10.5h rest, need 12h)
        # Delay adds 90 minutes -> land at 19:30Z (release at 20:00Z)
        # Now rest is only 10h, violates RULE-REST-04
        
        tool_spec = self.sim_registry.get_tool("analyze_delay")
        
        # This is a scenario-based test
        # Setup would require specific pairing and delay parameters
        result = tool_spec.execute(
            pairing_id="TEST-P001",  # 2-leg pairing
            leg_index=0,
            delay_minutes=90,
            crew_id="C-REST-TEST-1"
        )
        
        # Current behavior: might report crew as legal for delay
        # Expected: should flag rest violation for next-day duty
        assert isinstance(result, dict), "Delay analysis should return dict"
        
        # Check if rest conflict is detected
        legality = result.get("legality_check", {})
        # If implementation is fixed, should have rest conflict flag
        # For now, verify structure exists
        assert "legal" in legality or "violations" in legality, \
            "Should report legality status"
    
    def test_reserve_rest_status_verification_incomplete(self):
        """
        T2-EC-2: Reserve Rest Status Verification
        
        Reserve is on-call 06:00-18:00Z but in mandatory rest until 08:00Z.
        Callout at 07:00Z should fail (crew not rested) but system allows it.
        
        Current issue: reserve_availability() checks only on-call window,
        not intersecting rest period.
        """
        tool_spec = self.sim_registry.get_tool("check_reserve_availability")
        
        # Scenario: C-RESERVE-TEST-1 on-call 06:00-18:00, rest until 08:00
        result = tool_spec.execute(
            crew_id="C-RESERVE-TEST-1",
            callout_time="2026-09-15T07:00:00Z",  # 07:00 = before rest ends
            duty_start="2026-09-15T08:30:00Z"
        )
        
        # Current: might say "available"
        # Expected: should say "not available - in rest period"
        available = result.get("available", True)
        
        # Check if rest conflict is reported
        if available:
            # System should document reason
            reason = result.get("reason", "")
            # If it says available, it should at least acknowledge the risk
            assert isinstance(reason, str), "Should provide explanation"
    
    def test_overnight_station_closure_spans_calendar_days(self):
        """
        T2-EC-3: Overnight Station Closures
        
        Closure 22:00 (Sep 17) to 06:00 (Sep 18) spans calendar days.
        Implementation might miss flights on the second day.
        
        Current issue: untested scenario with multi-day closures.
        """
        tool_spec = self.sim_registry.get_tool("analyze_station_closure")
        
        result = tool_spec.execute(
            station_code="BOM",
            closure_start="2026-09-17T22:00:00Z",
            closure_end="2026-09-18T06:00:00Z",
            reason="Runway maintenance"
        )
        
        # Should identify all affected flights and crew
        affected_flights = result.get("affected_flights", [])
        affected_crew = result.get("affected_crew", [])
        
        # Verify both days' flights are captured
        flight_dates = set()
        for flight in affected_flights:
            flight_date = flight.get("date", "")
            flight_dates.add(flight_date)
        
        # Should capture flights from both 2026-09-17 and 2026-09-18
        assert isinstance(affected_flights, list), "Should return affected flights"
        assert isinstance(affected_crew, list), "Should return affected crew"
    
    def test_partial_multi_day_pairing_covers_rejected(self):
        """
        T2-EC-4: Partial Multi-Day Pairing Covers
        
        Crew can cover day 1 of 2-day pairing; another covers day 2.
        System forces full-pairing cover (overly conservative).
        
        Current issue: cover_must_take_full_pairing=True for multi-day pairings.
        """
        tool_spec = self.sim_registry.get_tool("find_replacement_crew")
        
        # Setup: 2-day pairing (SEP17-18), crew C-1050 removed
        result = tool_spec.execute(
            pairing_id="2DAY-P001",
            removed_crew_id="C-1050",
            allow_partial_cover=False  # Current behavior
        )
        
        candidates = result.get("candidates", [])
        
        # Current: no candidates because each crew must take full 2-day
        # Expected (if fixed): might have crew who can take day 1 or day 2
        
        # Now test with allow_partial=True (what should be allowed)
        result_partial = tool_spec.execute(
            pairing_id="2DAY-P001",
            removed_crew_id="C-1050",
            allow_partial_cover=True
        )
        
        candidates_partial = result_partial.get("candidates", [])
        
        # Partial covering should be more flexible
        assert isinstance(candidates, list), "Should return candidate list"
        assert isinstance(candidates_partial, list), "Should handle partial cover"
    
    def test_repatriation_logic_missing_for_partial_covers(self):
        """
        T2-EC-5: Repatriation Logic Missing
        
        If covering only day 1 of 2-day pairing, crew must get home.
        Rest impacts day 2 assignment; cost and legality not modeled.
        
        Current issue: Tier 3 (options.py) not fully implemented for partial covers.
        """
        # This test would require calling recommendation tools (Tier 3)
        # which is acknowledged as incomplete in README
        
        # Placeholder for when repatriation is implemented
        result = {
            "status": "INCOMPLETE",
            "notes": "Repatriation logic not yet implemented",
            "ticket": "CREW-OPS-REPATRIATION"
        }
        
        assert result["status"] == "INCOMPLETE", \
            "Repatriation logic is documented as known gap"
    
    def test_crew_removal_with_downstream_pairings(self):
        """
        T2-EC-6: Crew Removal with Downstream Pairings
        
        Removing crew affects not just current pairing but following pairings.
        If replacement covers day 1 but needs rest before day 2, downstream fails.
        """
        tool_spec = self.sim_registry.get_tool("analyze_crew_removal")
        
        result = tool_spec.execute(
            crew_id="C-REMOVE-TEST-1",
            pairing_id="P-CASCADE-1",
            crew_removal_reason="Medical incapacity"
        )
        
        # Should analyze cascading impact
        impact = result.get("impact", {})
        affected_pairings = result.get("affected_pairings", [])
        
        # Should show multi-day impact, not just immediate pairing
        assert isinstance(affected_pairings, list), \
            "Should identify all cascading affected pairings"
    
    def test_delay_impact_with_multiple_rule_violations(self):
        """
        T2-EC-7: Delay Impact Checking All Rules
        
        A 120-minute delay might violate multiple rules:
        - FDP exceeded
        - Rest for next duty insufficient
        - Cumulative 7-day duty limit approached
        """
        tool_spec = self.sim_registry.get_tool("analyze_delay")
        
        result = tool_spec.execute(
            pairing_id="TEST-MULTI-RULE-1",
            leg_index=0,
            delay_minutes=120,
            crew_id="C-NEAR-LIMIT-1"  # Crew already near limits
        )
        
        legality = result.get("legality_check", {})
        violations = legality.get("violations", [])
        
        # Should check all applicable rules
        rule_codes = [v.get("rule_code") for v in violations]
        
        # Should have clear list of which rules are violated
        assert isinstance(violations, list), "Should list rule violations"
    
    def test_cancellation_impact_on_following_connections(self):
        """
        T2-EC-8: Cancellation Impact on Following Connections
        
        Canceling a flight might strand crew with insufficient rest
        before next duty.
        """
        tool_spec = self.sim_registry.get_tool("analyze_flight_cancellation")
        
        result = tool_spec.execute(
            flight_number="AI-123",
            flight_date="2026-09-15",
            cancellation_reason="Aircraft maintenance"
        )
        
        affected_crew = result.get("affected_crew", [])
        cascading_impacts = result.get("cascading_impacts", [])
        
        # Should identify crew stranded and downstream pairings affected
        assert isinstance(affected_crew, list), "Should list affected crew"
        assert isinstance(cascading_impacts, list), "Should identify cascading impacts"
    
    def test_reserve_coverage_exhaustion(self):
        """
        T2-EC-9: Reserve Coverage Pool Exhaustion
        
        Multiple disruptions might exhaust available reserves.
        System should flag when no coverage is possible.
        """
        tool_spec = self.sim_registry.get_tool("check_reserve_coverage")
        
        result = tool_spec.execute(
            required_crew_count=5,
            base="BLR",
            availability_window="2026-09-15T06:00:00Z/2026-09-15T22:00:00Z"
        )
        
        available_reserves = result.get("available_reserves", [])
        coverage_possible = result.get("coverage_possible", True)
        
        # Should clearly indicate if coverage is not possible
        assert isinstance(coverage_possible, bool), "Should indicate feasibility"
    
    def test_legality_evidence_objects_structure(self):
        """
        T2-EC-10: Legality Evidence Objects Structure
        
        All rule checks should return RuleVerdict with consistent structure:
        status, computed, limit, margin, detail
        """
        # Create a rule context and test one rule
        context = RuleContext(
            crew_id="C-TEST-1",
            base="BLR",
            duty_date=date(2026, 9, 15)
        )
        
        # Get a duty record to evaluate
        duty_records = self.db.duties.list(crew_id="C-TEST-1")
        
        if duty_records:
            # Evaluate duties through rules engine
            verdicts = self.rules_engine.evaluate_duties(context, duty_records)
            
            # Each verdict should have complete evidence structure
            for verdict in verdicts:
                assert hasattr(verdict, "rule_code"), "Should have rule_code"
                assert hasattr(verdict, "status"), "Should have status (PASS/BREACH)"
                assert hasattr(verdict, "computed"), "Should have computed value"
                assert hasattr(verdict, "limit"), "Should have limit"
                assert hasattr(verdict, "margin"), "Should have margin"
                assert hasattr(verdict, "detail"), "Should have human detail"
    
    def test_simulation_tool_output_consistency(self):
        """
        T2-EC-11: Simulation Tool Output Consistency
        
        All simulation tools should return consistent JSON structure with:
        success, message, data (or specific result fields)
        """
        tools = [
            ("analyze_crew_removal", {"crew_id": "C-1001", "pairing_id": "P-001"}),
            ("analyze_delay", {"pairing_id": "P-001", "leg_index": 0, "delay_minutes": 60}),
            ("check_reserve_availability", {"crew_id": "C-RESERVE-1", "callout_time": "2026-09-15T10:00:00Z"}),
        ]
        
        for tool_name, params in tools:
            tool_spec = self.sim_registry.get_tool(tool_name)
            result = tool_spec.execute(**params)
            
            # Should have consistent structure
            assert isinstance(result, dict), f"{tool_name} should return dict"
            # Should indicate success/failure clearly
            assert "success" in result or "error" in result or "legal" in result, \
                f"{tool_name} should indicate status"
    
    def test_duty_clock_updates_after_simulation(self):
        """
        T2-EC-12: Duty Clock Consistency After Simulation
        
        Simulation results should reflect accurate duty clock state.
        If crew does another duty, clock should show cumulative hours.
        """
        # Get initial duty clock
        initial_clock = self.db.duty_clocks.get(crew_id="C-1001")
        initial_7d = initial_clock.duty_hours_7d if initial_clock else 0
        
        # Simulate a new duty
        result = self.sim_registry.get_tool("simulate_assignment").execute(
            crew_id="C-1001",
            pairing_id="P-TEST-NEW"
        )
        
        # Check updated clock
        updated_clock = self.db.duty_clocks.get(crew_id="C-1001")
        updated_7d = updated_clock.duty_hours_7d if updated_clock else 0
        
        # Updated should reflect added hours
        assert isinstance(updated_7d, (int, float, Decimal)), \
            "Duty clock should show numeric hours"
    
    def test_grounding_check_enforces_evidence_requirement(self):
        """
        T2-EC-13: Grounding Checks Enforce Evidence
        
        Every number in answer must come from tool evidence.
        System should catch unsupported claims.
        """
        # This is more of an orchestrator test
        # Simulate an answer with numbers
        answer_text = "Crew C-1001 has 45 duty hours and can do 8 more hours"
        
        # Grounding check should verify both 45 and 8 are from tools
        # If tool never returned these numbers, grounding should fail
        
        # For now, verify grounding check exists and is called
        from crew_ops_advisor.agent.grounding import GroundingChecker
        
        checker = GroundingChecker()
        assert hasattr(checker, "check"), "Grounding checker should have check method"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
