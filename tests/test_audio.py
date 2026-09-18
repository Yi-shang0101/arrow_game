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
                         {'countdown', 'failure', 'success', 'blocked', 'fly'})

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

    def test_effect_methods_are_safe_after_audio_shutdown(self):
        self.app.audio.stop_countdown()
        self.app.audio.stop_music()
        self.app.audio.play_effect('fly')
        self.app.audio.start_countdown()
        self.app.audio.stop_countdown()
        self.assertIsNone(self.app.audio.countdown_channel)

if __name__ == '__main__':
    unittest.main()
