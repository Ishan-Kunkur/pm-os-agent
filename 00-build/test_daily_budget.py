"""Offline checks: no API calls, no production ledger changes."""
import json
import multiprocessing
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace as N
from zoneinfo import ZoneInfo
from daily_budget import DailyBudget, DailyBudgetBlocked, BudgetedClient


def reserve_worker(path, queue):
    try:
        DailyBudget(path).reserve()
        queue.put(True)
    except DailyBudgetBlocked:
        queue.put(False)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'daily-budget.json'
        self.now = datetime(2026, 11, 21, 12, tzinfo=ZoneInfo('America/Los_Angeles'))
        self.budget = DailyBudget(self.path, now=lambda: self.now)

    def test_exhaustion_and_settlement(self):
        for _ in range(5):
            self.budget.settle(self.budget.reserve(), .1)
        with self.assertRaises(DailyBudgetBlocked):
            self.budget.reserve()

    def test_concurrent_reservations(self):
        ctx = multiprocessing.get_context('fork')
        queue = ctx.Queue()
        workers = [ctx.Process(target=reserve_worker, args=(self.path, queue)) for _ in range(8)]
        for worker in workers:
            worker.start()
        results = [queue.get(timeout=5) for _ in workers]
        for worker in workers:
            worker.join(timeout=5)
            self.assertEqual(worker.exitcode, 0)
        self.assertEqual(sum(results), 5)

    def test_day_rollover_and_original_day_settlement(self):
        tickets = [self.budget.reserve() for _ in range(5)]
        self.now += timedelta(days=1)
        self.budget.reserve()
        self.budget.settle(tickets[0], .02)
        days = json.loads(self.path.read_text())['days']
        self.assertAlmostEqual(days['2026-11-21']['spent'], .02)
        self.assertEqual(len(days['2026-11-22']['pending']), 1)

    def test_corrupt_ledger_blocks(self):
        self.path.write_text('{invalid')
        with self.assertRaises(DailyBudgetBlocked):
            self.budget.reserve()

    def test_uncertain_request_keeps_reservation(self):
        def failure(**kw):
            raise RuntimeError('request failed')
        client = N(chat=N(completions=N(create=failure)))
        with self.assertRaises(RuntimeError):
            BudgetedClient(client, self.budget, .15, .60).create()
        row = json.loads(self.path.read_text())['days']['2026-11-21']
        self.assertAlmostEqual(sum(row['pending'].values()), .1)

    def test_usage_settled_for_each_call_and_exhaustion_prevents_call(self):
        calls = []
        def complete(**kw):
            calls.append(kw)
            return N(usage=N(prompt_tokens=100000, completion_tokens=0))
        client = BudgetedClient(N(chat=N(completions=N(create=complete))), self.budget, 1, 1)
        for _ in range(5):
            client.create()
        with self.assertRaises(DailyBudgetBlocked):
            client.create()
        self.assertEqual(len(calls), 5)

    def test_seed_recorded_spend_once(self):
        record = {'run_id': '20261121T180000Z-old', 'estimated_cost_usd': .42}
        (self.path.parent / 'run-old.json').write_text(json.dumps(record))
        with self.assertRaises(DailyBudgetBlocked):
            self.budget.reserve()


if __name__ == '__main__':
    unittest.main(verbosity=2)
