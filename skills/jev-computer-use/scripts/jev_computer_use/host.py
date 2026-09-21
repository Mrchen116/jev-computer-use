"""Pause a live worker for its calling agent; never launch a text model."""
import argparse
import json
import os
from pathlib import Path
import time
import uuid


def write_json(path, value):
    """Publish a complete private message atomically to the local caller."""
    temporary = path.with_suffix('.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
    temporary.replace(path)


def validate_reply(request, reply):
    if reply.get('request_id') != request['request_id']:
        raise ValueError('Reply does not match the pending request_id')
    answer = reply.get('answer')
    fields = request['fields']
    if not isinstance(answer, dict) or set(answer) != set(fields):
        raise ValueError('Answer must contain exactly the requested fields')
    types = {'string': str, 'boolean': bool}
    if any(type(answer[key]) is not types[kind] for key, kind in fields.items()):
        raise ValueError('Answer field types do not match the request')
    return answer


class HostHelper:
    """Keep CUA/session state in memory while the caller supplies missing reasoning."""

    def __init__(self, directory, max_calls=20, timeout=600):
        self.directory = Path(directory).expanduser().resolve()
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        if any(self.directory.iterdir()):
            raise ValueError('Use a new, empty exchange directory for each run')
        self.directory.chmod(0o700)
        self.max_calls, self.timeout = max_calls, timeout
        self.events = []
        self.publish({'status': 'running', 'pid': os.getpid()})

    def publish(self, event):
        write_json(self.directory / 'event.json', event)

    def check_cancelled(self):
        if (self.directory / 'cancel').exists():
            raise RuntimeError('Run cancelled by the calling agent')

    def ask(self, purpose, step, instruction, state, fields):
        self.check_cancelled()
        if len(self.events) >= self.max_calls:
            raise RuntimeError('Host help budget reached; increase --max-llm-calls for a new run')
        event = {'purpose': purpose, 'step': step}
        self.events.append(event)
        request = {'status': 'needs_host', 'request_id': uuid.uuid4().hex,
                   'purpose': purpose, 'step': step,
                   'instruction': instruction, 'state': state, 'fields': fields}
        self.publish(request)
        print(json.dumps({'status': 'needs_host', 'purpose': purpose,
                          'exchange_dir': str(self.directory)}), flush=True)
        started = time.monotonic()
        response_path = self.directory / 'reply.json'
        try:
            while True:
                self.check_cancelled()
                if response_path.exists():
                    reply = json.loads(response_path.read_text())
                    response_path.unlink()
                    answer = validate_reply(request, reply)
                    self.publish({'status': 'running', 'pid': os.getpid(), 'step': step})
                    return answer
                if time.monotonic() - started >= self.timeout:
                    raise RuntimeError('Timed out waiting for the calling agent; no action was replayed')
                time.sleep(.1)
        finally:
            event['wait_seconds'] = round(time.monotonic() - started, 3)

    def finish(self, status, answer, counts):
        (self.directory / 'reply.json').unlink(missing_ok=True)
        self.publish({'status': status, 'answer': answer, **counts})


def main(argv=None):
    """Read a handoff or deliver a response without restarting the UI worker."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    status = sub.add_parser('status')
    status.add_argument('directory', type=Path)
    status.add_argument('--wait', type=float, default=0, help='Wait at most 60 seconds for a handoff/result')
    respond = sub.add_parser('respond')
    respond.add_argument('directory', type=Path)
    respond.add_argument('--response-file', required=True, type=Path)
    stop = sub.add_parser('stop')
    stop.add_argument('directory', type=Path)
    args = parser.parse_args(argv)
    event_path = args.directory / 'event.json'
    if args.command == 'status':
        deadline = time.monotonic() + max(0, min(60, args.wait))
        while True:
            event = json.loads(event_path.read_text()) if event_path.exists() else {'status': 'starting'}
            if event['status'] == 'needs_host' and (args.directory / 'reply.json').exists():
                event = {'status': 'running', 'detail': 'Reply queued; waiting for worker'}
            if event['status'] not in ('running', 'starting') or time.monotonic() >= deadline:
                print(json.dumps(event, ensure_ascii=False, indent=2))
                return 0
            time.sleep(.1)
    if not event_path.is_file():
        parser.error('Exchange directory has no worker event')
    if args.command == 'stop':
        write_json(args.directory / 'cancel', {'cancel': True})
        print('{"status":"cancellation_requested"}')
        return 0
    event = json.loads(event_path.read_text())
    if event['status'] != 'needs_host':
        parser.error('Worker is not waiting for a host response')
    reply = json.loads(args.response_file.read_text())
    validate_reply(event, reply)
    if (args.directory / 'reply.json').exists():
        parser.error('A reply is already pending; do not submit it twice')
    write_json(args.directory / 'reply.json', reply)
    print('{"status":"reply_queued"}')
    return 0
