"""Exercise connection reuse and ambiguous failures across actual HTTP messages."""
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import unittest
from unittest.mock import Mock, patch

from jev_computer_use.models import JevClient

PAYLOAD = {'questions': {'next': {'type': 'choice', 'criteria': {'wait': 'Wait'}}}}
RESULT = {'model': 'test', 'usage': {'input_tokens': 3, 'output_tokens': 2},
          'answers': {'next': {'choice': 'wait', 'confidence': 1, 'probabilities': {'wait': 1}}}}


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.status = 200
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def log_message(self, *args):
                pass

            def do_POST(self):
                owner.requests.append((self.client_address, json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                body = json.dumps(RESULT).encode()
                self.send_response(owner.status)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.client = JevClient('synthetic-test-key')
        self.proxies = patch('jev_computer_use.models.urllib.request.getproxies', return_value={})
        self.factory = patch('jev_computer_use.models.http.client.HTTPSConnection',
                             side_effect=lambda *a, **kw: http.client.HTTPConnection('127.0.0.1', self.server.server_port))
        self.proxies.start()
        self.factory.start()

    def tearDown(self):
        self.client.close()
        self.factory.stop()
        self.proxies.stop()
        self.server.shutdown()
        self.server.server_close()

    def test_successes_share_connection_and_account_each_response(self):
        for _ in range(2):
            result, _ = self.client.ask(PAYLOAD)
            self.assertEqual(result, RESULT)
        self.assertEqual(self.requests[0][0], self.requests[1][0])
        self.assertEqual(self.client.usage, {'input_tokens': 6, 'output_tokens': 4})
        self.assertEqual([e['connection_reused'] for e in self.client.events], [False, True])

    def test_failed_post_is_never_retried_and_remains_unmetered(self):
        self.status = 503
        with self.assertRaisesRegex(RuntimeError, 'Jev HTTP 503'):
            self.client.ask(PAYLOAD)
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(self.client.unmetered_calls, 1)
        self.assertIsNone(self.client.events[0]['usage'])
        self.status = 200
        self.client.ask(PAYLOAD)
        self.assertNotEqual(self.requests[0][0], self.requests[1][0])
        self.assertEqual(self.client.usage['input_tokens'], 3)

    def test_connect_proxy_preserves_tls_destination_and_separates_credentials(self):
        connection = Mock()
        with patch('jev_computer_use.models.urllib.request.getproxies', return_value={'https': 'http://u:p@proxy.test:1234'}), patch('jev_computer_use.models.urllib.request.proxy_bypass', return_value=False), patch('jev_computer_use.models.http.client.HTTPSConnection', return_value=connection) as factory:
            self.client._connect()
        factory.assert_called_once_with('proxy.test', 1234, timeout=45)
        connection.set_tunnel.assert_called_once_with('api.typesafe.ai', 443, headers={'Proxy-Authorization': 'Basic dTpw'})


if __name__ == '__main__':
    unittest.main()
