"""Local estimated-spend ledger; reservations are serialized across CLI processes."""
from __future__ import annotations
import fcntl
import json
import math
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from zoneinfo import ZoneInfo


class DailyBudgetBlocked(Exception):
    pass


class DailyBudget:
    def __init__(self, path, limit=0.50, reservation=0.10, now=None):
        if not all(math.isfinite(v) and v > 0 for v in (limit, reservation)):
            raise ValueError('Daily limit and reservation must be positive and finite')
        self.path = Path(path)
        self.limit = limit
        self.reservation = reservation
        self.now = now or (lambda: datetime.now(ZoneInfo('America/Los_Angeles')))

    @contextmanager
    def locked(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.with_suffix('.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                try:
                    state = json.loads(self.path.read_text()) if self.path.exists() else self.initial_state()
                    if not isinstance(state.get('days'), dict):
                        raise ValueError('Invalid ledger')
                    yield state
                    temp = self.path.with_name(self.path.name + '.' + uuid4().hex + '.tmp')
                    try:
                        with temp.open('x') as out:
                            json.dump(state, out, indent=2, allow_nan=False)
                            out.flush()
                            os.fsync(out.fileno())
                        os.replace(temp, self.path)
                    finally:
                        temp.unlink(missing_ok=True)
                finally:
                    fcntl.flock(lock, fcntl.LOCK_UN)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise DailyBudgetBlocked('daily budget ledger unavailable or invalid') from exc

    def initial_state(self):
        """Seed from pre-ledger local run records, so recorded spend is not reset."""
        state = {'days': {}}
        for path in self.path.parent.glob('run-*.json'):
            record = json.loads(path.read_text())
            stamp = datetime.strptime(record['run_id'].split('-')[0], '%Y%m%dT%H%M%SZ')
            day = stamp.replace(tzinfo=ZoneInfo('UTC')).astimezone(
                ZoneInfo('America/Los_Angeles')).date().isoformat()
            cost = record['estimated_cost_usd']
            if not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
                raise ValueError('Invalid recorded cost')
            row = state['days'].setdefault(day, {'spent': 0.0, 'pending': {}})
            row['spent'] += cost
        return state

    def reserve(self):
        day = self.now().astimezone(ZoneInfo('America/Los_Angeles')).date().isoformat()
        token = uuid4().hex
        with self.locked() as state:
            row = state['days'].setdefault(day, {'spent': 0.0, 'pending': {}})
            spent = row['spent']
            pending = row['pending']
            values = [spent, *pending.values()]
            if not all(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0 for v in values):
                raise ValueError('Invalid ledger amounts')
            if spent + sum(pending.values()) + self.reservation > self.limit + 1e-9:
                raise DailyBudgetBlocked('daily estimated budget exhausted or reserved')
            pending[token] = self.reservation
        return day, token

    def settle(self, ticket, cost):
        if not math.isfinite(cost) or cost < 0:
            raise DailyBudgetBlocked('invalid usage estimate; reservation retained')
        day, token = ticket
        with self.locked() as state:
            row = state['days'][day]
            if token not in row['pending']:
                raise DailyBudgetBlocked('missing reservation')
            del row['pending'][token]
            row['spent'] += cost


class BudgetedClient:
    """Wrap all drafting and critic calls with the same ledger reservation gate."""
    def __init__(self, client, ledger, price_in, price_out, before_call=None):
        self.client, self.ledger = client, ledger
        self.price_in, self.price_out = price_in, price_out
        self.before_call = before_call or (lambda: None)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.before_call()
        ticket = self.ledger.reserve()
        self.before_call()
        # No automatic SDK retries: one reservation gates one request attempt.
        # Any exception/timeout retains its reservation for uncertain remote spend.
        response = self.client.chat.completions.create(**kwargs)
        usage = response.usage
        cost = (usage.prompt_tokens * self.price_in + usage.completion_tokens * self.price_out) / 1_000_000
        self.ledger.settle(ticket, cost)
        return response
