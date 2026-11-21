"""Offline operator-stop tests; isolated flags, ledgers, and logs."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import patch
from openai.types.chat import ChatCompletionMessage
import agent
import tools
from daily_budget import BudgetedClient


class StopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=agent.OUTPUT_DIR)
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.patch = patch.object(agent, 'OUTPUT_DIR', self.output)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stdout.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)

    def test_stop_blocks_new_run_before_client(self):
        agent.request_stop()
        with patch.object(agent, 'OpenAI', side_effect=AssertionError('client must not start')):
            result = agent.run('happy')
        self.assertEqual(result['outcome'], 'stuck')
        self.assertEqual(result['iterations'], 0)
        self.assertIn('operator stop', result['stop_reason'])
        self.assertTrue(list(self.output.glob('run-*.json')))

    def test_resume_is_explicit_and_idempotent(self):
        agent.request_stop()
        with self.assertRaises(agent.OperatorStop):
            agent.check_operator_stop()
        agent.resume_runs()
        agent.resume_runs()
        agent.check_operator_stop()

    def test_ctrl_c_holds_output_and_blocks_restart(self):
        def interrupt(**kwargs):
            raise KeyboardInterrupt()
        client = N(chat=N(completions=N(create=interrupt)))
        with patch.object(agent, 'OpenAI', return_value=client):
            result = agent.run('happy')
        self.assertEqual(result['outcome'], 'stuck')
        self.assertIn('Ctrl+C', result['stop_reason'])
        self.assertTrue((self.output / 'STOP').exists())
        with patch.object(agent, 'OpenAI', side_effect=AssertionError('must not restart')):
            blocked = agent.run('happy')
        self.assertEqual(blocked['iterations'], 0)

    def test_stop_during_tool_batch_prevents_next_tool(self):
        message = ChatCompletionMessage(role='assistant', tool_calls=[
            {'id': 'a', 'type': 'function', 'function': {'name': 'get_project', 'arguments': '{"project_id":"P-NORTH"}'}},
            {'id': 'b', 'type': 'function', 'function': {'name': 'get_activity', 'arguments': '{"project_id":"P-NORTH"}'}},
        ])
        response = N(usage=N(prompt_tokens=0, completion_tokens=0), choices=[N(message=message)])
        client = N(chat=N(completions=N(create=lambda **kw: response)))
        def stop_in_tool(**kwargs):
            agent.request_stop()
            return {'project_id': 'P-NORTH'}
        registry = dict(tools.TOOLS)
        registry['get_project'] = stop_in_tool
        with patch.object(agent, 'OpenAI', return_value=client), patch.object(tools, 'TOOLS', registry), patch.dict(registry, get_activity=lambda **kw: self.fail('second tool executed')):
            result = agent.run('happy')
        self.assertEqual(result['outcome'], 'stuck')
        self.assertTrue(any('get_project' in source for source in result['sources']))
        self.assertFalse(any('get_activity(' in source for source in result['sources']))

    def test_critic_and_drafter_share_preflight(self):
        agent.request_stop()
        client = N(chat=N(completions=N(create=lambda **kw: self.fail('API called'))))
        ledger = N(reserve=lambda: self.fail('reservation created'))
        wrapped = BudgetedClient(client, ledger, 1, 1, before_call=agent.check_operator_stop)
        with self.assertRaises(agent.OperatorStop):
            wrapped.chat.completions.create()


if __name__ == '__main__':
    agent.OUTPUT_DIR.mkdir(exist_ok=True)
    unittest.main(verbosity=2)
