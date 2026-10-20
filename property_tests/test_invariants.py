"""Generated schedules checked against an independent business-state model."""
from pathlib import Path
import sqlite3
import tempfile
import unittest

from hypothesis import given, settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from agentlab.durable import DurableRun
from agentlab.stateful import ActionConflict, InjectedCrash, SupportTools, verify_outcome

FAULT = st.sampled_from(('none', 'before_write', 'before_ack', 'after_ack'))


class TicketMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.directory = tempfile.TemporaryDirectory()
        self.database = Path(self.directory.name) / 'state.sqlite'
        self.tools = SupportTools(self.database)
        self.tools.seed_order()
        self.actions = {}
        self.reason = None
        self.duplicates = []

    @rule(action_id=st.sampled_from(('a', 'b', 'c')),
          reason=st.sampled_from(('missing parcel', 'damaged package')), fault=FAULT)
    def write(self, action_id, reason, fault):
        conflicting = ((action_id in self.actions and self.actions[action_id] != reason)
                       or (self.reason is not None and self.reason != reason))
        expected_error = (InjectedCrash if fault == 'before_write' else
                          ActionConflict if conflicting else
                          InjectedCrash if fault in ('before_ack', 'after_ack') else None)
        actual_error = None
        try:
            self.tools.open_ticket(action_id, 'order-001', reason, fault=fault)
        except (InjectedCrash, ActionConflict) as exc:
            actual_error = type(exc)
        assert actual_error is expected_error
        if fault != 'before_write' and not conflicting:
            if action_id in self.actions:
                self.duplicates.append('replayed_action')
            elif self.reason is not None:
                self.duplicates.append('duplicate_intent')
            self.actions[action_id] = reason
            self.reason = reason

    @rule()
    def reopen(self):
        self.tools.close()
        self.tools = SupportTools(self.database)
        self.tools.seed_order()

    @invariant()
    def independent_database_matches_model(self):
        with sqlite3.connect(self.database) as connection:
            orders = connection.execute('SELECT order_id,status FROM orders').fetchall()
            tickets = connection.execute('SELECT order_id,reason FROM tickets').fetchall()
            actions = dict(connection.execute('SELECT action_id,reason FROM actions').fetchall())
            duplicates = [row[0] for row in connection.execute('SELECT kind FROM duplicate_actions ORDER BY event_id')]
            assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
        assert orders == [('order-001', 'shipped')]
        assert tickets == ([] if self.reason is None else [('order-001', self.reason)])
        assert actions == self.actions
        assert duplicates == self.duplicates

    def teardown(self):
        self.tools.close()
        self.directory.cleanup()


TestTicketMachine = TicketMachine.TestCase
TestTicketMachine.settings = settings(max_examples=50, stateful_step_count=30,
                                      deadline=None, derandomize=True)


class RecoveryProperties(unittest.TestCase):
    @settings(max_examples=100, deadline=None, derandomize=True)
    @given(schedule=st.lists(FAULT, min_size=0, max_size=8))
    def test_generated_restart_schedule_never_duplicates_business_write(self, schedule):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'durable.sqlite'
            tools = SupportTools(database)
            tools.seed_order()
            tools.close()
            now = 0
            identity = None
            for fault in [*schedule, 'none']:
                run = DurableRun(database, clock=lambda: now)
                try:
                    state = run.create('generated', budget=9)
                    identity = identity or state['action_id']
                    assert state['action_id'] == identity
                    try:
                        run.step('generated', fault=fault)
                    except InjectedCrash:
                        pass
                    state = run.state('generated')
                    assert state['attempts'] <= 9
                    now = state['next_at']
                finally:
                    run.close()
            result = verify_outcome(database)
            assert state['status'] == 'completed'
            assert result['success']
            assert result['action_count'] == 1
            assert len(result['tickets']) == 1

    @settings(max_examples=50, deadline=None, derandomize=True)
    @given(budget=st.integers(min_value=1, max_value=10))
    def test_persistent_failure_never_exceeds_persisted_budget(self, budget):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'budget.sqlite'
            now = 0
            for _ in range(budget + 2):
                run = DurableRun(database, clock=lambda: now)
                try:
                    run.create('bounded', budget=budget)
                    try:
                        run.step('bounded', fault='before_write')
                    except InjectedCrash:
                        pass
                    state = run.state('bounded')
                    now = state['next_at']
                    assert state['attempts'] <= budget
                finally:
                    run.close()
            assert state['status'] == 'exhausted'
            assert state['attempts'] == budget
            assert len(state['trace']) == budget
