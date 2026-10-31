import base64
import importlib
import io
import json
import pathlib
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code'))
import storage


class Strip:
    def __init__(self):
        self.brightness = None
        self.displayed_brightness = None

    def setBrightness(self, value):
        self.brightness = value

    def show(self):
        self.displayed_brightness = self.brightness


class Board:
    def __init__(self):
        self.values = json.loads((ROOT / 'code/settings.example.json').read_text())
        self.__dict__.update(self.values)
        self.strip = Strip()
        self.textOrigin = [[1, 1], [1, 7]]
        self.saved = None
        self.pendingBoardConfig = None
        self._settingsLock = threading.RLock()
    def settingsSnapshot(self):
        return {key: getattr(self, key) for key in self.values}
    def dumpSettings(self):
        self.saved = json.loads(json.dumps(self.settingsSnapshot()))
    def loadSettings(self, startup):
        self.__dict__.update(self.saved)
    def textStateWipe(self): pass
    def updateDisplayString(self): pass
    def colorFill(self, *args): pass
    def changeBoardType(self, value): self.pending = value


fake_led = types.ModuleType('LEDUtils')
fake_led.PPB = Board()
fake_led.Color = lambda r, g, b: (r << 16) | (g << 8) | b
fake_led.slanted = object()
fake_led.digits = object()
with patch.dict(sys.modules, {'LEDUtils': fake_led}):
    spec = importlib.util.spec_from_file_location('api_under_test', ROOT / 'code/flaskUtils.py')
    api = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'api_under_test': api}):
        spec.loader.exec_module(api)


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name)
        self.path.joinpath('auth.json').write_text(json.dumps({'username': 'tester', 'password': 'secret'}))
        patcher = patch.object(storage, 'STATE_DIR', self.path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.board = Board()
        api.PPB = self.board
        self.client = api.app.test_client()
        token = base64.b64encode(b'tester:secret').decode()
        self.auth = {'Authorization': 'Basic ' + token}
        self.headers = dict(self.auth, **{'X-Requested-With': 'XMLHttpRequest'})

    def post(self, path, data, headers=None):
        return self.client.post(path, data=data, headers=self.headers if headers is None else headers)

    def test_authentication_covers_static_and_missing_credentials(self):
        for path in ('/', '/api/state', '/static/js/script.js'):
            self.assertEqual(self.client.get(path).status_code, 401)
            response = self.client.get(path, headers=self.auth)
            self.assertEqual(response.status_code, 200)
            response.close()
        self.path.joinpath('auth.json').unlink()
        self.assertEqual(self.client.get('/api/state', headers=self.auth).status_code, 401)

    def test_csrf_and_origin(self):
        self.assertEqual(self.post('/api/brightness', {'brightness': '10'}, self.auth).status_code, 403)
        for origin, status in [('http://localhost', 200), ('http://localhost:80', 200), ('http://evil.test', 403), ('null', 403), ('http://localhost.evil.test', 403)]:
            headers = dict(self.headers, Origin=origin)
            self.assertEqual(self.post('/api/brightness', {'brightness': '10'}, headers).status_code, status)

    def test_slow_request_body_does_not_hold_board_lock(self):
        started = threading.Event()
        release = threading.Event()
        body = b'brightness=42'
        result = []

        class BlockingBody(io.BytesIO):
            def readinto(self, buffer):
                started.set()
                if not release.wait(3):
                    raise TimeoutError('request body was not released')
                return super().readinto(buffer)

        def send_request():
            try:
                with api.app.test_client() as client:
                    response = client.post(
                        '/api/brightness', headers=self.headers,
                        content_type='application/x-www-form-urlencoded',
                        environ_overrides={'wsgi.input': BlockingBody(body), 'CONTENT_LENGTH': str(len(body))},
                    )
                    result.append(response.status_code)
            except Exception as error:
                result.append(error)

        worker = threading.Thread(target=send_request, daemon=True)
        worker.start()
        try:
            self.assertTrue(started.wait(2), 'request did not start reading its body')
            acquired = api.board_lock.acquire(timeout=1)
            try:
                self.assertTrue(acquired, 'body read held the board lock')
                self.assertTrue(worker.is_alive(), 'request finished before the body was released')
            finally:
                if acquired:
                    api.board_lock.release()
        finally:
            release.set()
            worker.join(3)
        self.assertFalse(worker.is_alive(), 'request did not finish after releasing the body')
        self.assertEqual(result, [200])
        self.assertEqual(self.board.brightness, 42)

    def test_invalid_inputs_do_not_mutate(self):
        cases = [('/api/brightness', {'brightness': '256'}), ('/api/font', {'font': 'unknown'}),
                 ('/api/textanimation', {'animation': 'scrolling', 'lineNum': '0', 'speed': 'nan'}),
                 ('/api/setcontent', {'content': 'evil', 'lineNum': '0', 'checked': 'true'}),
                 ('/api/weather', {'unit': 'f', 'zip': 'x', 'city': 'x' * 513}),
                 ('/api/bgcolor', {'color': 'solid', 'red': '1', 'green': '2', 'blue': '-1'}),
                 ('/api/xlsettings', {'lineCount': '2'}), ('/api/boardtype', {'boardType': 'other'}),
                 ('/api/webpagesettings', {'settings': '{invalid'})]
        before = json.loads(json.dumps(self.board.settingsSnapshot()))
        for path, data in cases:
            with self.subTest(path=path):
                self.assertEqual(self.post(path, data).status_code, 400)
                self.assertEqual(self.board.settingsSnapshot(), before)

    def test_brightness_save_reload_and_encoded_text(self):
        self.assertEqual(self.post('/api/brightness', {'brightness': '42'}).status_code, 200)
        self.assertEqual(self.board.strip.displayed_brightness, 42)
        self.assertEqual(self.post('/api/setcustomtext', {'text': 'A&B + 50% ☀'}).status_code, 200)
        self.assertEqual(self.post('/api/settings', {'action': 'save'}).status_code, 200)
        self.board.brightness = 7
        self.board.customText = ''
        self.assertEqual(self.post('/api/settings', {'action': 'load'}).status_code, 200)
        state = self.client.get('/api/state', headers=self.auth).get_json()
        self.assertEqual(state['brightness'], 42)
        self.assertEqual(state['customText'], 'A&B + 50% ☀')

    def test_pending_xl_line_count_preserves_active_geometry(self):
        self.board.pendingBoardConfig = {'boardType': 'xl', 'lineCount': 1}
        self.assertEqual(self.post('/api/xlsettings', {'lineCount': '2'}).status_code, 200)
        self.assertEqual(self.board.pendingBoardConfig['lineCount'], 2)
        self.assertEqual(self.board.lineCount, 1)

    def test_page_settings_persist_and_board_change(self):
        page = {'title': 'Hello & welcome', 'mainBGColor': 'rgb(1, 2, 3)'}
        self.assertEqual(self.post('/api/webpagesettings', {'settings': json.dumps(page)}).status_code, 200)
        self.assertEqual(self.client.get('/api/webpagesettings', headers=self.auth).get_json(), page)
        self.assertEqual(json.loads((self.path / 'webpage.json').read_text()), page)
        self.assertFalse((self.path / 'webpagesettings.txt').exists())
        self.assertEqual(self.post('/api/boardtype', {'boardType': 'xl'}).status_code, 200)
        self.assertEqual(self.board.pending, 'xl')
        self.assertEqual(self.board.boardType, 'normal')


if __name__ == '__main__':
    unittest.main()

class PresetApiTest(unittest.TestCase):
    setUp = ApiTest.setUp
    post = ApiTest.post
    def test_presets_auth_validation_references_and_schedules(self):
        self.assertEqual(self.client.get('/api/presets').status_code, 401)
        self.assertEqual(self.post('/api/presets', {'action':'save', 'name':'X'}, self.auth).status_code, 403)
        self.assertEqual(self.post('/api/presets', {'action':'save', 'name':' '}).status_code, 400)
        response = self.post('/api/presets', {'action':'save', 'name':'<img src=x>'})
        self.assertEqual(response.status_code, 200)
        preset_id = response.json['presets'][0]['id']
        self.assertEqual(response.json['presets'][0]['name'], '<img src=x>')
        self.assertEqual(self.post('/api/presets', {'action':'default', 'id':preset_id}).status_code, 200)
        self.assertEqual(self.post('/api/presets', {'action':'delete', 'id':preset_id}).status_code, 400)
        self.assertEqual(self.post('/api/presets', {'action':'default', 'id':''}).status_code, 200)
        self.assertEqual(self.post('/api/presets', {'action':'schedule', 'preset':preset_id, 'time':'25:00', 'days':'[0]', 'enabled':'true'}).status_code, 400)
        response = self.post('/api/presets', {'action':'schedule', 'preset':preset_id, 'time':'12:30', 'days':'[0,1]', 'enabled':'false'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post('/api/presets', {'action':'delete', 'id':preset_id}).status_code, 400)
        self.assertEqual(self.post('/api/presets', {'action':'delete_schedule', 'id':response.json['schedules'][0]['id']}).status_code, 200)
        self.assertEqual(self.post('/api/presets', {'action':'delete', 'id':preset_id}).status_code, 200)
