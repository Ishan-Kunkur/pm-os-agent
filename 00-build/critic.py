"""Independent validation with labeled evidence and five explicit check results.

The critic sees its own request, not the drafter conversation. Malformed or
incomplete verdicts fail closed; the production loop owns revision limits.
"""
from __future__ import annotations

import json
import os
import re
from prompts import CRITIC_SYSTEM

CHECKS = ('facts', 'stories', 'authority', 'confidentiality', 'escalation')


def evidence_packet(source_data: str) -> dict:
    """Label recorded tool results without dropping the original source log."""
    records = []
    for line in source_data.splitlines():
        match = re.match(r'^(\w+)\(.*\) -> (.*)$', line)
        if match:
            try:
                records.append({'tool': match[1], 'result': json.loads(match[2])})
            except json.JSONDecodeError:
                pass
    return {
        'tool_evidence': records,
        'projects': [r['result'] for r in records if r['tool'] == 'get_project'],
        'activity': [r['result'] for r in records if r['tool'] == 'get_activity'],
        'queue_results': [r['result'] for r in records if r['tool'] == 'propose_stories'],
        'runtime_queue_cap': int(os.environ.get('CORTEX_MAX_QUEUE_ITEMS', '10')),
        'original_source_log': source_data,
    }


def review(client, model: str, proposed_output: str, source_data: str) -> dict:
    # Exit markers are parsed by the production loop, not semantic evidence.
    # Preserve every claim and review/queue statement; remove only the marker.
    semantic_draft = re.sub(r'(?m)^DONE:\s*', '', proposed_output)
    payload = {'evidence': evidence_packet(source_data), 'draft': semantic_draft}
    resp = client.chat.completions.create(
        model=model,
        messages=[{'role': 'system', 'content': CRITIC_SYSTEM},
                  {'role': 'user', 'content': json.dumps(payload)}],
        response_format={'type': 'json_object'},
    )
    usage = resp.usage
    try:
        body = json.loads(resp.choices[0].message.content)
        checks = body['checks']
        if not isinstance(checks, list) or len(checks) != len(CHECKS):
            raise ValueError('five checks required')
        if {c['id'] for c in checks} != set(CHECKS):
            raise ValueError('unknown or duplicate checks')
        reasons = []
        for check in checks:
            if type(check['pass']) is not bool:
                raise ValueError('boolean result required')
            if not isinstance(check['explanation'], str) or not check['explanation'].strip():
                raise ValueError('explanation required')
            violations = check['violations']
            if not isinstance(violations, list) or check['pass'] != (not violations):
                raise ValueError('inconsistent verdict')
            for violation in violations:
                for key in ('claim', 'evidence', 'reason'):
                    if not isinstance(violation[key], str) or not violation[key].strip():
                        raise ValueError('concrete violation required')
                if violation['claim'] not in proposed_output:
                    raise ValueError('claim must be an exact draft excerpt')
                reasons.append({'check': check['id'], **violation})
        verdict = {'verdict': 'fail' if reasons else 'pass',
                   'reasons': reasons, 'checks': checks}
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        verdict = {'verdict': 'fail', 'reasons': ['critic returned invalid or incomplete check results']}
    verdict['_usage'] = {'prompt': usage.prompt_tokens, 'completion': usage.completion_tokens}
    return verdict
