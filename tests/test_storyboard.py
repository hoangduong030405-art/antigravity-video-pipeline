import unittest

from antigravity_video_pipeline.storyboard import StoryboardError, split_prompt, storyboard_from_prompt, validate_storyboard


class StoryboardTests(unittest.TestCase):
    def test_split_prompt_on_sentences(self):
        self.assertEqual(split_prompt("First scene. Second scene!"), ["First scene.", "Second scene!"])

    def test_generated_storyboard_has_requested_scene_count_and_duration(self):
        result = storyboard_from_prompt("One. Two.", scene_count=4, duration=12)
        self.assertEqual(len(result["scenes"]), 4)
        self.assertAlmostEqual(sum(scene["duration"] for scene in result["scenes"]), 12, places=2)

    def test_empty_prompt_is_rejected(self):
        with self.assertRaises(StoryboardError):
            storyboard_from_prompt("   ")

    def test_invalid_scene_is_rejected(self):
        with self.assertRaises(StoryboardError):
            validate_storyboard({"scenes": [{}]}, 10)


if __name__ == "__main__":
    unittest.main()
