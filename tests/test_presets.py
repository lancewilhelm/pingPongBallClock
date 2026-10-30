import datetime
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import test_runtime
from test_runtime import led, storage
import presets


class PresetTest(unittest.TestCase):
    setUp = test_runtime.RuntimeTest.setUp
    def test_apply_and_scheduled_recovery(self):
        display = presets.snapshot(self.board.settingsSnapshot())
        display['brightness'] = 42
        executions = {'a' * 32: '2026-11-01'}
        with patch.object(self.board.strip, 'setBrightness', side_effect=RuntimeError('hardware')):
            with self.assertRaises(RuntimeError):
                self.board.applyPreset(display, executions)
        persisted = storage.read_json(self.path / 'settings.json')
        self.assertEqual(persisted['brightness'], 42)
        self.assertEqual(persisted['scheduleExecutions'], executions)
        self.assertTrue(persisted['presetApplyPending'])
        recovered = led.PingPongBoard()
        self.assertEqual(recovered.brightness, 42)
        recovered.clearPresetMarker('presetApplyPending')
        recovered.dumpSettings()
        self.assertEqual(storage.read_json(self.path / 'settings.json')['scheduleExecutions'], executions)

    def test_pending_board_and_incompatible_rejected(self):
        display = presets.snapshot(self.board.settingsSnapshot())
        self.board.changeBoardType('normal')
        with self.assertRaises(ValueError):
            self.board.applyPreset(display)
        self.board.changeBoardType('xl')
        self.assertNotIn('boardRestartPending', self.board.settingsSnapshot())
        self.board.boardType = 'normal'
        with self.assertRaises(ValueError):
            self.board.applyPreset(display)

    def test_startup_default_and_simultaneous_schedules(self):
        import importlib
        with patch.dict('sys.modules', {'LEDUtils': led}):
            api = importlib.import_module('flaskUtils')
        first = presets.snapshot(self.board.settingsSnapshot())
        first['brightness'] = 31
        second = dict(first, brightness=72)
        items = [{'id':'a'*32, 'name':'A', 'display':first}, {'id':'b'*32, 'name':'B', 'display':second}]
        schedules = [{'id':'d'*32, 'preset':items[1]['id'], 'time':'01:30', 'days':[6], 'enabled':True},
                     {'id':'c'*32, 'preset':items[0]['id'], 'time':'01:30', 'days':[6], 'enabled':True}]
        presets.save({'presets':items, 'schedules':schedules, 'default':items[1]['id']})
        with patch.object(api, 'PPB', self.board):
            api.initialize_presets()
            self.assertEqual(self.board.brightness, 72)
            api.run_schedules(datetime.datetime(2026,11,1,1,30))
            self.assertEqual(self.board.brightness, 31)
            self.assertEqual(len(self.board.settingsSnapshot()['scheduleExecutions']), 2)
            self.board.brightness = 44
            api.run_schedules(datetime.datetime(2026,11,1,1,30, fold=1))
            self.assertEqual(self.board.brightness, 44)

    def test_definitions_and_days(self):
        item = {'id': 'a'*32, 'name': '<img>', 'display': presets.snapshot(self.board.settingsSnapshot())}
        schedule = {'id': 'b'*32, 'preset': item['id'], 'time':'01:30', 'days':[6], 'enabled':True}
        definitions = {'presets':[item], 'schedules':[schedule], 'default':item['id']}
        presets.save(definitions)
        self.assertEqual(presets.load(), definitions)
        sunday = datetime.datetime(2026,11,1,1,30)
        self.assertEqual(presets.due(definitions, sunday, {}), [schedule])
        self.assertEqual(presets.due(definitions, sunday, {schedule['id']:'2026-11-01'}), [])
        self.assertEqual(presets.due(definitions, sunday - datetime.timedelta(days=1), {}), [])
        self.assertEqual(presets.due(definitions, sunday.replace(hour=3), {}), [])
        definitions['schedules'][0]['time'] = '25:00'
        with self.assertRaises(ValueError): presets.save(definitions)

if __name__ == '__main__': unittest.main()
