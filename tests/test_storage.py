import json
import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

from test_runtime import led, ROOT
import storage


class StorageTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.legacy = self.root / 'legacy'
        self.legacy.mkdir()
        self.state = self.root / 'state'
        self.settings = json.loads((ROOT / 'code/settings.example.json').read_text())
        self.settings.update(customText='Saved text', brightness=67)
        (self.legacy / 'settings.txt').write_text(json.dumps(self.settings))
        (self.legacy / 'apikeys.txt').write_text('{"openweather":"test-key"}')
        for target, name, value in ((storage, 'STATE_DIR', self.state), (led, 'CODE_DIR', self.legacy)):
            p = patch.object(target, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.board = led.PingPongBoard()

    def test_migration_preserves_legacy_and_values_across_restart(self):
        self.assertEqual(self.board.settingsSnapshot(), self.settings)
        self.assertEqual(self.board.openWeatherKey, 'test-key')
        self.board.customText = 'Updated text'
        self.board.dumpSettings()
        restored = led.PingPongBoard()
        self.assertEqual(restored.customText, 'Updated text')
        self.assertEqual(restored.brightness, 67)
        self.assertEqual(json.loads((self.legacy / 'settings.txt').read_text()), self.settings)
        self.assertEqual(json.loads((self.legacy / 'apikeys.txt').read_text())['openweather'], 'test-key')

    def test_migration_preserves_long_text_and_unbounded_finite_speeds(self):
        legacy = dict(self.settings, customText='x' * 600, animationSpeed=[-1, 150])
        (self.legacy / 'settings.txt').write_text(json.dumps(legacy))
        (self.state / 'settings.json').unlink()
        board = led.PingPongBoard()
        self.assertEqual(board.settingsSnapshot(), legacy)
        board.dumpSettings()
        self.assertEqual(led.PingPongBoard().settingsSnapshot(), legacy)

    def test_migration_preserves_long_legacy_page_title(self):
        page = {'title': 't' * 250, 'mainBGColor': 'rgb(61, 0, 91)'}
        legacy = self.legacy / 'webpagesettings.txt'
        legacy.write_text(json.dumps(page))
        with patch.object(storage, 'CODE_DIR', self.legacy):
            loaded = storage.load_state('webpage.json', 'webpagesettings.txt', storage.page_settings)
            self.assertEqual(loaded, page)
            self.assertEqual(json.loads((self.state / 'webpage.json').read_text()), page)
            self.assertEqual(json.loads(legacy.read_text()), page)

    def test_fresh_install_uses_examples_without_legacy_files(self):
        fresh = self.root / 'fresh'
        fresh.mkdir()
        for name in ('settings.example.json', 'apikeys.example.json', 'webpagesettings.example.json'):
            shutil.copy(ROOT / 'code' / name, fresh / name)
        with patch.object(storage, 'CODE_DIR', fresh), patch.object(led, 'CODE_DIR', fresh), \
                patch.object(storage, 'STATE_DIR', fresh / '.local'):
            board = led.PingPongBoard()
            self.assertEqual(board.openWeatherKey, '')
            self.assertEqual(board.boardType, 'normal')
            self.assertEqual(board.settingsSnapshot(), json.loads((fresh / 'settings.example.json').read_text()))
            page = storage.load_state('webpage.json', 'webpagesettings.txt', storage.page_settings)
            self.assertEqual(page, json.loads((fresh / 'webpagesettings.example.json').read_text()))
            self.assertEqual(json.loads((fresh / '.local/apikeys.json').read_text()), {'openweather': ''})
            self.assertFalse((fresh / 'apikeys.txt').exists())

    def test_corrupt_state_recovers_previous_valid_snapshot(self):
        self.board.customText = 'Second'
        self.board.dumpSettings()
        (self.state / 'settings.json').write_text('{broken')
        restored = led.PingPongBoard()
        self.assertEqual(restored.customText, 'Saved text')
        self.assertEqual(restored.brightness, 67)

    def test_invalid_loaded_settings_do_not_mutate_live_board(self):
        before = self.board.settingsSnapshot()
        bad = dict(before, brightness=999)
        (self.state / 'settings.json').write_text(json.dumps(bad))
        with self.assertRaises((FileNotFoundError, ValueError)):
            self.board.loadSettings(False)
        self.assertEqual(self.board.settingsSnapshot(), before)

    def test_board_change_persists_pending_target_without_rebuilding_strip(self):
        strip = self.board.strip
        geometry = (self.board.num_balls, self.board.num_rows, self.board.num_cols)
        self.board.changeBoardType('xl')
        self.assertEqual(self.board.boardType, 'normal')
        self.assertIs(self.board.strip, strip)
        self.assertEqual((self.board.num_balls, self.board.num_rows, self.board.num_cols), geometry)
        self.assertIsNotNone(self.board.restart_at)
        self.board.customText = 'Still saved'
        self.board.dumpSettings()
        restored = led.PingPongBoard()
        self.assertEqual(restored.boardType, 'xl')
        self.assertEqual((restored.num_balls, restored.num_rows, restored.num_cols), (257, 13, 23))
        self.assertEqual(restored.strip.count, 257 * led.PIXEL_RATIO)
        self.assertEqual(restored.customText, 'Still saved')

    def test_reload_active_board_cancels_pending_restart(self):
        self.board.changeBoardType('xl')
        storage.save_state('settings.json', self.settings, storage.device_settings)
        self.board.loadSettings(False)
        self.assertIsNone(self.board.pendingBoardConfig)
        self.assertIsNone(self.board.restart_at)
        self.assertEqual(self.board.settingsSnapshot()['boardType'], 'normal')
        self.board.dumpSettings()
        self.assertEqual(led.PingPongBoard().boardType, 'normal')

    def test_invalid_board_type_does_not_change_settings(self):
        before = self.board.settingsSnapshot()
        with self.assertRaises(ValueError):
            self.board.changeBoardType('bad')
        self.assertEqual(self.board.settingsSnapshot(), before)
        self.assertIsNone(self.board.restart_at)


if __name__ == '__main__':
    unittest.main()
