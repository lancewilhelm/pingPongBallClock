import unittest
from unittest.mock import patch
import test_runtime
led = test_runtime.led

class TemporalTests(unittest.TestCase):
    def setUp(self):
        test_runtime.RuntimeTest.setUp(self)
        self.t = 100.0
        self.patches = [patch.object(led.time, 'monotonic_ns', side_effect=lambda: round(self.t * 1_000_000_000)), patch.object(led.time, 'sleep')]
        for p in self.patches: p.start(); self.addCleanup(p.stop)
        self.background = self.board.balls[6][0]
        self.foreground = self.board.balls[6][1]
        self.board.bgColor = ['animation', 'rainbowCycle']
        self.board.textColor = ['solid', 1]
    def render(self, advance=0):
        self.t += advance
        self.board.updateBoardColors()
    def test_elapsed_time_and_startup(self):
        self.render()
        self.assertEqual(self.background.color, self.board.wheel(1))
        self.render(.01)
        self.assertEqual(self.background.color, self.board.wheel(1))
        self.render(.021)
        self.assertEqual(self.background.color, self.board.wheel(2))
        self.render(.09)
        self.assertEqual(self.background.color, self.board.wheel(5))
    def test_both_layers_share_elapsed_time(self):
        self.foreground.text = True
        self.board.textColor = ['animation', 'rainbowCycle']
        self.render()
        self.render(.15)
        self.assertEqual(self.background.color, self.board.wheel(6))
        self.assertEqual(self.foreground.color, self.board.wheel(6))
    def test_stall_skips_to_current_phase(self):
        self.render()
        self.render(3.0)
        self.assertEqual(self.background.color, self.board.wheel(101))
    def test_switching_restarts_timer_without_changing_phase(self):
        self.render()
        self.board.bgColor = ['solid', 5]
        self.render(.3)
        self.board.bgColor = ['animation', 'rainbowCycle']
        self.render(.3)
        self.assertEqual(self.background.color, self.board.wheel(2))
        self.render(.01)
        self.assertEqual(self.background.color, self.board.wheel(2))
    def test_switching_rainbow_type_restarts_its_timer(self):
        self.render()
        self.board.bgColor = ['animation', 'rainbow']
        self.render(.3)
        expected = self.board.wheel((6 * led.PIXEL_RATIO + 2) % 256)
        self.assertEqual(self.background.color, expected)
        self.render(.01)
        self.assertEqual(self.background.color, expected)

    def test_new_text_mask_is_colored_without_waiting_for_tick(self):
        self.render()
        self.foreground.text = True
        self.board.textDisplayChanged = self.board.bgDisplayChanged = True
        self.board.textColor = ['animation', 'rainbowCycle']
        self.render(.001)
        self.assertEqual(self.foreground.color, self.board.wheel(1))
        self.assertEqual(self.background.color, self.board.wheel(1))
    def test_breathing_does_not_set_rainbow_phase(self):
        self.board.textColor = ['animation', 'breathing']
        self.render()
        self.render(.15)
        self.assertEqual(self.background.color, self.board.wheel(6))

    def test_each_layer_restarts_its_own_timer(self):
        self.foreground.text = True
        self.board.textColor = ['animation', 'rainbowCycle']
        self.render()
        self.board.textColor = ['solid', 1]
        self.render(.15)
        self.board.textColor = ['animation', 'rainbowCycle']
        self.render(.15)
        self.assertEqual(self.background.color, self.board.wheel(11))
        self.assertEqual(self.foreground.color, self.board.wheel(2))

    def test_writing_character_does_not_flush_pixel_buffer(self):
        with patch.object(self.board.strip, 'show') as show:
            self.board.writeChar(1, 1, '8')
        show.assert_not_called()

    def test_rainbow_does_not_block_other_work(self):
        self.board.textColor = ['animation', 'rainbowCycle']
        self.render()
        led.time.sleep.assert_not_called()

if __name__ == '__main__': unittest.main(verbosity=2)
