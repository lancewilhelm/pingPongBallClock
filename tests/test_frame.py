import base64
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_runtime import ROOT, led, storage


class FrameTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name)
        self.path.joinpath('auth.json').write_text(json.dumps({'username': 'tester', 'password': 'secret'}))
        for target, name in ((led, 'CODE_DIR'), (storage, 'STATE_DIR')):
            patcher = patch.object(target, name, self.path)
            patcher.start()
            self.addCleanup(patcher.stop)
        with patch.dict(sys.modules, {'LEDUtils': led}):
            spec = importlib.util.spec_from_file_location('frame_api_under_test', ROOT / 'code/flaskUtils.py')
            self.api = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.api)
        self.client = self.api.app.test_client()
        token = base64.b64encode(b'tester:secret').decode()
        self.auth = {'Authorization': 'Basic ' + token}

    def make_board(self, board_type):
        settings = json.loads((ROOT / 'code/settings.example.json').read_text())
        settings.update(boardType=board_type, lineCount=1, brightness=73)
        storage.save_state('settings.json', settings, storage.device_settings)
        board = led.PingPongBoard()
        self.api.PPB = board
        return board

    def test_layouts_colors_and_orientation(self):
        for board_type, height, width, bottom_col, top_hole in (
            ('normal', 7, 20, 3, 17), ('xl', 13, 23, 6, 17)
        ):
            with self.subTest(board_type=board_type):
                board = self.make_board(board_type)
                board.writeBallColor(bottom_col, 0, 0x123456)
                board.writeBallColor(0, height - 1, 0xABCDEF)
                board.writeBallColor(0, 0, 0xFFFFFF)
                response = self.client.get('/api/frame', headers=self.auth)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
                frame = response.get_json()
                self.assertEqual(set(frame), {'boardType', 'brightness', 'rows'})
                self.assertEqual((frame['boardType'], frame['brightness']), (board_type, 73))
                self.assertEqual(len(frame['rows']), height)
                self.assertTrue(all(len(row) == width for row in frame['rows']))
                self.assertEqual(frame['rows'][0][0], 0xABCDEF)
                self.assertEqual(frame['rows'][-1][bottom_col], 0x123456)
                self.assertIsNone(frame['rows'][-1][0])
                self.assertIsNone(frame['rows'][0][top_hole])
                self.assertEqual(sum(cell is not None for row in frame['rows'] for cell in row),
                                 128 if board_type == 'normal' else 257)
                board.writeBallColor(bottom_col, 0, 0x010203)
                self.assertEqual(frame['rows'][-1][bottom_col], 0x123456)
                self.assertEqual(self.client.get('/api/frame', headers=self.auth).get_json()['rows'][-1][bottom_col], 0x010203)

    def test_authentication_and_pending_layout(self):
        board = self.make_board('normal')
        self.assertEqual(self.client.get('/api/frame').status_code, 401)
        self.assertEqual(self.client.get('/api/frame', headers={'Authorization': 'Basic invalid'}).status_code, 401)
        board.changeBoardType('xl')
        self.assertEqual(board.pendingBoardConfig['boardType'], 'xl')
        frame = self.client.get('/api/frame', headers=self.auth).get_json()
        self.assertEqual(frame['boardType'], 'normal')
        self.assertEqual((len(frame['rows']), len(frame['rows'][0])), (7, 20))


if __name__ == '__main__':
    unittest.main()
