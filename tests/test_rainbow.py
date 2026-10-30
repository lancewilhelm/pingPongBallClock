import unittest
from unittest.mock import patch

import test_runtime

led = test_runtime.led


class RainbowTest(unittest.TestCase):
    setUp = test_runtime.RuntimeTest.setUp

    def test_rainbow_completes_color_wheel_on_each_board_and_strip(self):
        for board_type in ('normal', 'xl'):
            for ratio in (1, 2):
                for method_name, text in (('rainbow', False), ('rainbowText', True),
                                          ('rainbowCycle', False), ('rainbowCycleText', True)):
                    with self.subTest(board_type=board_type, ratio=ratio, animation=method_name):
                        settings = self.board.settingsSnapshot()
                        settings.update(boardType=board_type, lineCount=1)
                        led.storage.save_state('settings.json', settings, led.storage.device_settings)
                        with patch.object(led, 'PIXEL_RATIO', ratio), patch.object(led.time, 'monotonic_ns', side_effect=(i * 30_000_000 for i in range(514))):
                            board = led.PingPongBoard()
                            ball = board.balls[6][0]
                            ball.text = text
                            offset = 6 * ratio if method_name in ('rainbow', 'rainbowText') else 0
                            for frame in range(1, 515):
                                getattr(board, method_name)()
                                if frame in (128, 256, 257, 512, 514):
                                    self.assertEqual(ball.color, board.wheel((offset + frame) % 256),
                                                     f'wrong color at frame {frame}')

    def test_both_layers_advance_one_color_per_frame(self):
        board = led.PingPongBoard()
        background = board.balls[6][0]
        foreground = board.balls[6][1]
        foreground.text = True
        board.bgColor = ['animation', 'rainbowCycle']
        board.textColor = ['animation', 'rainbowCycle']
        with patch.object(led.time, 'monotonic_ns', side_effect=(i * 30_000_000 for i in range(120) for _ in range(2))):
            for _ in range(120):
                board.updateBoardColors()
        self.assertEqual(background.color, board.wheel(120))
        self.assertEqual(foreground.color, board.wheel(120))

    def test_rainbow_keeps_its_color_cycle_when_other_layer_breathes(self):
        for rainbow_on_text in (False, True):
            with self.subTest(rainbow_on_text=rainbow_on_text):
                board = led.PingPongBoard()
                ball = board.balls[6][0]
                ball.text = rainbow_on_text
                board.bgColor = ['animation', 'breathing' if rainbow_on_text else 'rainbowCycle']
                board.textColor = ['animation', 'rainbowCycle' if rainbow_on_text else 'breathing']
                with patch.object(led.time, 'sleep'), patch.object(led.time, 'monotonic_ns', side_effect=(i * 30_000_000 for i in range(120))):
                    for _ in range(120):
                        board.updateBoardColors()
                self.assertEqual(ball.color, board.wheel(120))


if __name__ == '__main__':
    unittest.main()
