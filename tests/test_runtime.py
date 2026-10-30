import importlib
import json
import pathlib
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code'))

class Strip:
    def __init__(self, count, *args):
        self.count = count
        self.pixels = {}
    def begin(self):
        pass
    def setPixelColor(self, index, color):
        if not 0 <= index < self.count:
            raise AssertionError('invalid pixel index')
        self.pixels[index] = color
    def show(self):
        pass
    def setBrightness(self, value):
        pass

hardware = types.ModuleType('rpi_ws281x')
hardware.Color = lambda r, g, b: (r << 16) | (g << 8) | b
hardware.PixelStrip = Strip
hardware.WS2811_STRIP_GRB = 0
requests = types.ModuleType('requests')
requests.RequestException = type('RequestException', (Exception,), {})
requests.get = lambda *args, **kwargs: None
import storage
with tempfile.TemporaryDirectory() as initial_state:
    with patch.object(storage, 'STATE_DIR', pathlib.Path(initial_state)):
        with patch.dict(sys.modules, {'rpi_ws281x': hardware, 'requests': requests}):
            led = importlib.import_module('LEDUtils')

class RuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name)
        settings = json.loads((ROOT / 'code/settings.example.json').read_text())
        settings.update(boardType='xl', lineCount=2, bgColor=['solid', 0], textColor=['solid', 1])
        (self.path / 'settings.txt').write_text(json.dumps(settings))
        (self.path / 'apikeys.txt').write_text('{"openweather":"test"}')
        for target, name in ((led, 'CODE_DIR'), (storage, 'STATE_DIR')):
            patcher = patch.object(target, name, self.path)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.board = led.PingPongBoard()

    def render(self):
        self.board.updateDisplayString()
        self.board.updateBoardColors()
        return {(y, x) for y, row in enumerate(self.board.balls) for x, ball in enumerate(row) if ball.text}

    def test_invalid_ball_addresses_are_not_written(self):
        self.board.colorFill(123, fullwipe=True)
        self.assertTrue(self.board.strip.pixels)
        self.assertTrue(all(0 <= i < self.board.led_count for i in self.board.strip.pixels))

    def test_redraw_removes_old_pixels_and_preserves_other_line(self):
        self.board.displayString = ['888', '42']
        before = self.render()
        self.board.displayString[0] = '1'
        after = self.render()
        self.assertTrue(before - after)
        self.assertEqual({p for p in before if p[0] >= 7}, {p for p in after if p[0] >= 7})
        for y, x in before - after:
            ball = self.board.balls[y][x]
            if ball.ledNum < self.board.num_balls:
                self.assertEqual(self.board.strip.pixels[ball.ledNum * led.PIXEL_RATIO], 0)
        self.board.displayString[1] = ''
        self.assertFalse({p for p in self.render() if p[0] >= 7})

    def test_xl_settings_redraws_unchanged_text_and_content_noop(self):
        with patch.dict(sys.modules, {'LEDUtils': led}):
            api = importlib.import_module('flaskUtils')
        self.board.displayString = ['12', '34']
        before = self.render()
        with patch.object(api, 'PPB', self.board):
            with api.app.test_request_context('/api/setcontent', method='POST',
                    data={'content': 'time', 'lineNum': '0', 'checked': 'true'}):
                api.setContent()
            self.assertEqual(self.render(), before)
            with api.app.test_request_context('/api/xlsettings', method='POST', data={'lineCount': '1'}):
                api.setXLSettings()
            after = self.render()
        self.assertTrue(after)
        self.assertNotEqual(before, after)
        self.assertEqual(self.board.textOrigin[0], [2, 4])
        self.assertFalse({p for p in after if p[0] >= 9})

    def test_load_settings_redraws_unchanged_text_with_new_font_and_origin(self):
        self.board.displayString = ['12', '34']
        before = self.render()
        settings = self.board.settingsSnapshot()
        settings.update(fontName='slanted', lineCount=1)
        storage.save_state('settings.json', settings, storage.device_settings)
        self.board.loadSettings(False)
        after = self.render()
        expected = led.PingPongBoard()
        expected.displayString = ['12', '34']
        expected.updateDisplayString()
        expected_pixels = {(y, x) for y, row in enumerate(expected.balls)
                           for x, ball in enumerate(row) if ball.text}
        self.assertNotEqual(before, after)
        self.assertEqual(after, expected_pixels)

    def test_unknown_unicode_and_zero_speed_are_safe(self):
        self.board.displayString = ['🙂é', '']
        self.assertTrue(self.render())
        self.board.updateTextAnimation(0)

    def test_twinkle_frames_are_time_limited(self):
        ball = self.board.balls[6][0]
        ball.twinkle = True
        ball.twinkleLength = 50
        with patch.object(led.time, 'monotonic', side_effect=[1.0, 1.005, 1.021]):
            self.board.twinkle()
            self.board.twinkle()
            self.assertEqual(ball.twinkleFrame, 1)
            self.board.twinkle()
            self.assertEqual(ball.twinkleFrame, 2)

    def test_weather_is_nonblocking_discards_old_location_and_retries(self):
        started, release = threading.Event(), threading.Event()
        calls = []
        def get(url, params, timeout):
            calls.append(params.copy())
            if len(calls) == 1:
                started.set()
                release.wait(2)
                return types.SimpleNamespace(json=lambda: {'cod': 200, 'main': {'temp': 300}, 'weather': [{'description': 'old'}]})
            return types.SimpleNamespace(json=lambda: {'cod': 401})
        with patch.object(led.requests, 'get', side_effect=get):
            self.board.weather(0)
            self.assertTrue(started.wait(1))
            self.board.weatherZipLocation = 'new'
            self.board.displayString[0] = ''
            self.board.weather(0)
            self.assertEqual(self.board.displayString[0], 'ERROR ')
            self.assertEqual(len(calls), 1)
            release.set()
            deadline = time.monotonic() + 2
            while len(calls) < 2 and time.monotonic() < deadline:
                self.board.weather(0)
                time.sleep(.005)
            self.assertEqual(len(calls), 2)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                self.board.displayString[0] = ''
                self.board.weather(0)
                if self.board.displayString[0] == 'KEY ERROR ':
                    break
                time.sleep(.005)
            self.assertEqual(self.board.displayString[0], 'KEY ERROR ')
            for _ in range(10):
                self.board.weather(0)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[-1]['zip'], 'new')

    def test_weather_malformed_and_network_failures_are_safe(self):
        for payload in ({'cod': 200, 'main': {}}, {'cod': 200, 'main': {'temp': None}, 'weather': []}):
            self.board.weatherResponse = payload
            self.board._weatherConfig = (self.board.openWeatherKey, self.board.weatherZipLocation, self.board.weatherCityLocation)
            self.board._weatherNextAttempt = float('inf')
            self.board.displayString[0] = ''
            self.board.weather(0)
            self.assertEqual(self.board.displayString[0], 'ERROR ')
        self.board.weatherResponse = None
        self.board._weatherNextAttempt = 0
        with patch.object(led.requests, 'get', side_effect=led.requests.RequestException('offline')) as get:
            self.board.weather(0)
            deadline = time.monotonic() + 2
            while self.board._weatherResult is None and time.monotonic() < deadline:
                time.sleep(.005)
            for _ in range(10):
                self.board.weather(0)
            self.assertEqual(get.call_count, 1)

if __name__ == '__main__':
    unittest.main()
