"""Exercise the real native backend with deterministic actions and zero model calls."""
import json
from pathlib import Path
import time
from .desktop import Desktop

def main():
    root = Path(__file__).resolve().parent
    started = time.monotonic()
    desktop = Desktop()
    try:
        initial = desktop.observe()
        assert initial['app'] is None and initial['scope'] == 'apps'
        app = next(a for a in initial['actions'].values() if a.get('app') == 'com.google.Chrome')
        desktop.execute(app)
        state = desktop.execute({'verb': 'keyboard'}, 'super+t')
        # The fixed selectors below belong to this test, never to the agent strategy.
        address = next(a for a in state['actions'].values() if a['verb'] == 'fill' and a['name'] in ('地址和搜索栏', 'Address and search bar'))
        desktop.execute(address, (root/'fixtures/native.html').as_uri())
        desktop.execute({'verb': 'enter'})
        state = desktop.observe()
        field = next(a for a in state['fields'] if a['name'] == 'Test message')
        state = desktop.execute(field, 'Jev native transport works 中文')
        assert next(a for a in state['fields'] if a['name'] == 'Test message')['value'] == 'Jev native transport works 中文'
        button = next(a for a in state['actions'].values() if a['label'] == 'Apply locally')
        state = desktop.execute(button)
        assert 'Received: Jev native transport works 中文' in state['page']
        result = {
            'success': True, 'backend': 'native-cua',
            'plugin_version': desktop.client.config.parent.name, 'initial_scope': initial['scope'],
            'operations': ['select app', 'new tab', 'fill address', 'Return', 'fill field', 'click button', 'verify output'],
            'evidence': 'Received: Jev native transport works 中文',
            'llm_calls': 0, 'jev_calls': 0, 'cua_tool_calls': desktop.client.tool_calls,
            'seconds': round(time.monotonic()-started, 2),
            'note': 'Codex desktop running; native permissions unchanged; test tab left open.',
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        desktop.close()


if __name__ == "__main__":
    main()
