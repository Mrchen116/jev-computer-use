"""Task state contains current evidence and past facts, not stale advice."""


def make_state(task, context, observation, history, feedback=None):
    events = []
    for record in history[-6:]:
        events.append({key: record[key] for key in (
            'operation', 'target', 'input', 'execution', 'effect', 'error', 'rejected_completion'
        ) if key in record})
    controls = [
        {'id': key, **{field: action[field] for field in ('role', 'label', 'value') if field in action}}
        for key, action in observation['actions'].items() if 'ref' in action
    ]
    state = {'task': task, 'user_facts': context, 'current_page': observation['page'],
             'current_controls': controls, 'recent_events': events}
    if feedback:
        state['completion_not_yet_verified'] = feedback
    return state


def compact_report(report):
    """Persist counts/timings only; task text, UI, answers and inputs stay out."""
    summary = {key: report[key] for key in (
        'backend', 'status', 'elapsed_seconds', 'llm_calls', 'llm_events', 'jev_calls', 'cua_tool_calls'
    )}
    summary['steps'] = [
        {key: record[key] for key in ('step', 'operation', 'execution', 'jev_seconds') if key in record}
        for record in report['steps']
    ]
    return summary
