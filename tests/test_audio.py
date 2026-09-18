import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
from pathlib import Path
import unittest
import pygame
from main import App, AudioManager

ROOT = Path(__file__).resolve().parents[1]

class AudioTests(unittest.TestCase):
    def setUp(self):
        self.app = App(save_path=None)
        self.app.draw()

    def tearDown(self):
        pygame.quit()

    def test_all_user_audio_assets_are_present(self):
        audio_dir = ROOT / 'assets' / 'audio'
        expected = set(AudioManager.MUSIC.values()) | set(AudioManager.EFFECTS.values())
        self.assertTrue(expected)
        self.assertTrue(all((audio_dir / name).is_file() for name in expected))
        self.assertEqual(set(AudioManager.EFFECTS),
                         {'countdown', 'failure', 'success', 'blocked', 'fly', 'button'})

    def test_music_and_state_effect_routing(self):
        self.assertTrue(self.app.audio.enabled)
        self.assertEqual(self.app.game.state, 'MENU')
        self.app.action('start'); self.app.draw()
        self.assertEqual(self.app.game.state, 'READY')
        self.app.action('begin'); self.app.draw()
        self.assertEqual(self.app.game.state, 'PLAYING')
        self.assertEqual(self.app.audio.current_music, 'game')
        self.assertIsNotNone(self.app.audio.countdown_channel)
        self.app.game.update(36); self.app.draw()
        self.assertEqual(self.app.game.state, 'GAME_OVER')
        self.assertIsNone(self.app.audio.countdown_channel)
        self.assertEqual(self.app.audio.current_music, 'menu')

    def test_success_sound_stops_before_result_button_action(self):
        self.app.game.progress.record(0, 10)
        self.app.game.state = 'LEVEL_CLEAR'
        self.app.game.grade = 'A'
        self.app.draw()
        channel = self.app.audio.result_channel
        self.assertIsNotNone(channel)
        self.assertTrue(channel.get_busy())
        button = self.app.buttons['continue']
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=button.center))
        self.assertIsNone(self.app.audio.result_channel)
        self.assertFalse(channel.get_busy())
        self.assertEqual(self.app.game.state, 'READY')

    def test_failure_sound_stops_before_retry_button(self):
        self.app.game.state = 'GAME_OVER'
        self.app.game.failure_reason = 'mistakes'
        self.app.draw()
        channel = self.app.audio.result_channel
        self.assertIsNotNone(channel)
        button = self.app.buttons['restart']
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=button.center))
        self.assertIsNone(self.app.audio.result_channel)
        self.assertFalse(channel.get_busy())
        self.assertEqual(self.app.game.state, 'READY')

    def test_button_sound_is_loaded_and_safe(self):
        self.assertIn('button', self.app.audio.effects)
        self.app.audio.play_effect('button')
        self.app.audio.stop_result()
        self.app.audio.stop_countdown()

if __name__ == '__main__':
    unittest.main()
