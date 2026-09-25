"""Comprehensive Unit and Integration Test Suite for Video Workflow Studio."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from config import settings, Settings
from skills.film_skills import (
    ShotType,
    CameraMovement,
    LightingStyle,
    OpticsLenses,
    ColorScience,
    TransitionType,
    FilmPromptBuilder,
    DEFAULT_NEGATIVE_PROMPT,
)
from pipeline.storyboard import (
    Storyboard,
    Scene,
    SceneStatus,
    CharacterProfile,
    DialogueLine,
    ScreenplayScene,
    Screenplay,
    TransitionConfig,
)
from pipeline.video_gen import UseApiGoogleFlowClient, VideoGenerationEngine
from pipeline.audio_gen import AudioEngine
from pipeline.editor import VideoEditor
from pipeline.director import DirectorAgent
from pipeline.youtube_publisher import YouTubePublisher


class TestStoryboardDataModels(unittest.TestCase):
    """Test Storyboard, Scene, and Screenplay Pydantic data models."""

    def test_character_profile_creation(self):
        char = CharacterProfile(
            character_id="hero",
            name="NEO",
            role="Protagonist",
            appearance="Tall, black trenchcoat",
            wardrobe_visual_dna="Latex suit, dark sunglasses",
            voice_and_cadence="Monotone, calm",
            backstory="Hacker who discovered the truth",
            internal_conflict="Belief in prophecy vs doubt",
            prompt_anchor="Neo in sleek black sunglasses and trenchcoat",
        )
        self.assertEqual(char.character_id, "hero")
        self.assertEqual(char.name, "NEO")
        self.assertIn("sunglasses", char.prompt_anchor)

    def test_scene_metadata_field(self):
        scene = Scene(
            scene_number=1,
            title="Shot 01",
            action_description="Opening shot",
        )
        self.assertIsInstance(scene.metadata, dict)
        scene.metadata["mediaGenerationId"] = "gen_12345"
        self.assertEqual(scene.metadata["mediaGenerationId"], "gen_12345")

    def test_storyboard_serialization_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "test_storyboard.json"
            char = CharacterProfile(
                character_id="hero",
                name="DETECTIVE KANE",
                role="Protagonist",
                appearance="Gaunt build",
                wardrobe_visual_dna="Charcoal trench",
                voice_and_cadence="Low rasp",
                backstory="Origin story",
                internal_conflict="Justice vs Revenge",
                prompt_anchor="Kane in charcoal trench",
            )
            screenplay = Screenplay(
                title="Neon Rain",
                logline="A detective hunts a rogue AI",
                characters=[char],
                scenes=[
                    ScreenplayScene(
                        scene_number=1,
                        slugline="EXT. ROOFTOP - NIGHT",
                        action="Rain falls on Kane's shoulders.",
                        dialogues=[DialogueLine(character="KANE", line="It never stops.")],
                        sound_cues=["SOUND: Thunderclap"],
                    )
                ],
            )
            scene = Scene(
                scene_number=1,
                title="Shot 01",
                slugline_ref="EXT. ROOFTOP - NIGHT",
                duration_seconds=8.0,
                action_description="Kane standing on the ledge",
                visual_prompt="Kane on a neon rooftop in the rain",
                metadata={"mediaGenerationId": "id_abc"},
            )
            sb = Storyboard(
                project_id="proj_test_01",
                title="Neon Rain",
                logline="A detective hunts a rogue AI",
                total_target_duration=8.0,
                screenplay=screenplay,
                scenes=[scene],
            )
            sb.save(file_path)
            self.assertTrue(file_path.exists())

            loaded = Storyboard.load(file_path)
            self.assertEqual(loaded.project_id, "proj_test_01")
            self.assertEqual(len(loaded.scenes), 1)
            self.assertEqual(loaded.scenes[0].metadata.get("mediaGenerationId"), "id_abc")
            self.assertEqual(loaded.screenplay.title, "Neon Rain")
            self.assertIn("NEON RAIN", loaded.screenplay.format_screenplay_transcript())
            self.assertIn("DETECTIVE KANE", loaded.screenplay.format_character_bible_markdown())
            self.assertIn("Shot 01", loaded.format_breakdown_markdown())


class TestFilmSkills(unittest.TestCase):
    """Test cinematography grammar and prompt builder."""

    def test_film_prompt_builder(self):
        prompt = FilmPromptBuilder.build_prompt(
            subject_action="Detective walks down wet alleyway",
            shot_type=ShotType.WIDE_SHOT,
            camera_movement=CameraMovement.SLOW_PUSH_IN,
            lighting=LightingStyle.NEON_CYBER_NOIR,
            lens=OpticsLenses.ANAMORPHIC_35MM,
            color_science=ColorScience.KODAK_VISION3_35MM,
            visual_dna="Matte black Kevlar cowl",
            environmental_atmosphere="Heavy rain, cyan reflections",
        )
        self.assertIn("Wide Shot", prompt)
        self.assertIn("35mm anamorphic", prompt)
        self.assertIn("Matte black Kevlar cowl", prompt)
        self.assertIn("Slow, creeping cinematic push-in", prompt)
        self.assertIn("High-contrast cyber noir", prompt)
        self.assertIn("Kodak Vision3 500T", prompt)
        self.assertIn("Heavy rain", prompt)
        self.assertIn("24fps", prompt)


class TestUseApiGoogleFlowClient(unittest.TestCase):
    """Test useapi.net Google Flow API v1 client edge cases and robustness."""

    def setUp(self):
        self.client = UseApiGoogleFlowClient(api_token="test_token_123", base_url="https://api.useapi.net/v1/google-flow")

    def test_configured_status(self):
        self.assertTrue(self.client.is_configured)
        unconfigured = UseApiGoogleFlowClient(api_token="")
        self.assertFalse(unconfigured.is_configured)

    def test_headers_trim_whitespace(self):
        client = UseApiGoogleFlowClient(api_token="  token_with_spaces  ")
        headers = client._headers()
        self.assertEqual(headers["Authorization"], "Bearer token_with_spaces")
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_aspect_ratio_normalization(self):
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"jobid": "job_123"}
            mock_post.return_value = mock_resp

            with patch("requests.get") as mock_get:
                poll_resp = MagicMock()
                poll_resp.status_code = 200
                poll_resp.json.return_value = {
                    "status": "completed",
                    "response": {"media": [{"videoUrl": "https://gcs.com/video.mp4", "mediaGenerationId": "mid_1"}]},
                }
                mock_get.return_value = poll_resp

                # Test 16:9 mapping to landscape
                self.client.generate_video(prompt="Test", aspect_ratio="16:9", max_wait_seconds=5, poll_interval=1)
                posted_body = mock_post.call_args[1]["json"]
                self.assertEqual(posted_body["aspectRatio"], "landscape")

                # Test 9:16 mapping to portrait
                self.client.generate_video(prompt="Test", aspect_ratio="9:16", max_wait_seconds=5, poll_interval=1)
                posted_body = mock_post.call_args[1]["json"]
                self.assertEqual(posted_body["aspectRatio"], "portrait")

    def test_upload_asset_validation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            empty_file = Path(tmp_dir) / "empty.png"
            empty_file.touch()

            # Empty file should fail validation
            res = self.client.upload_asset(empty_file)
            self.assertIsNone(res)

            # Nonexistent file should fail
            nonexistent = Path(tmp_dir) / "missing.png"
            res = self.client.upload_asset(nonexistent)
            self.assertIsNone(res)

    @patch("requests.post")
    def test_upload_asset_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"mediaGenerationId": "mid_asset_999"}
        mock_post.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            img = Path(tmp_dir) / "frame.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\nfakeimagecontent")

            gen_id = self.client.upload_asset(img)
            self.assertEqual(gen_id, "mid_asset_999")

    @patch("requests.post")
    def test_create_character_with_email(self, mock_post):
        self.client.email = "director@studio.ai"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"character": "user:123-char:456"}
        mock_post.return_value = mock_resp

        char_ref = self.client.create_character("HERO", ["mid_1", "mid_2"], "Notes")
        self.assertEqual(char_ref, "user:123-char:456")
        sent_body = mock_post.call_args[1]["json"]
        self.assertEqual(sent_body["email"], "director@studio.ai")
        self.assertEqual(sent_body["imageReference_1"], "mid_1")
        self.assertEqual(sent_body["imageReference_2"], "mid_2")

    @patch("requests.post")
    def test_extend_video_with_email(self, mock_post):
        self.client.email = "director@studio.ai"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"jobid": "job_ext_123"}
        mock_post.return_value = mock_resp

        with patch("requests.get") as mock_get:
            poll_resp = MagicMock()
            poll_resp.status_code = 200
            poll_resp.json.return_value = {
                "status": "completed",
                "response": {"media": [{"videoUrl": "https://gcs/ext.mp4", "mediaGenerationId": "mid_ext"}]},
            }
            mock_get.return_value = poll_resp

            res = self.client.extend_video("mid_orig", "Extend prompt", max_wait_seconds=5, poll_interval=1)
            self.assertEqual(res["videoUrl"], "https://gcs/ext.mp4")
            sent_body = mock_post.call_args[1]["json"]
            self.assertEqual(sent_body["email"], "director@studio.ai")

    @patch("requests.post")
    def test_concatenate_videos(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"encodedVideo": "ZmFrZXZpZGVv"}  # base64 for 'fakevideo'
        mock_post.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "concat.mp4"
            success = self.client.concatenate_videos(["mid_1", "mid_2"], out_file)
            self.assertTrue(success)
            self.assertTrue(out_file.exists())
            self.assertEqual(out_file.read_bytes(), b"fakevideo")

    def test_duration_snapping(self):
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"jobid": "job_dur"}
            mock_post.return_value = mock_resp

            with patch("requests.get") as mock_get:
                poll_resp = MagicMock()
                poll_resp.status_code = 200
                poll_resp.json.return_value = {
                    "status": "completed",
                    "response": {"media": [{"videoUrl": "https://gcs/dur.mp4"}]},
                }
                mock_get.return_value = poll_resp

                self.client.generate_video(prompt="Test", duration=3, max_wait_seconds=2, poll_interval=1)
                self.assertEqual(mock_post.call_args[1]["json"]["duration"], 4)

                self.client.generate_video(prompt="Test", duration=5, max_wait_seconds=2, poll_interval=1)
                self.assertEqual(mock_post.call_args[1]["json"]["duration"], 6)

                self.client.generate_video(prompt="Test", duration=7, max_wait_seconds=2, poll_interval=1)
                self.assertEqual(mock_post.call_args[1]["json"]["duration"], 8)

                self.client.generate_video(prompt="Test", duration=9, max_wait_seconds=2, poll_interval=1)
                self.assertEqual(mock_post.call_args[1]["json"]["duration"], 10)

                self.client.generate_video(prompt="Test", duration=15, max_wait_seconds=2, poll_interval=1)
                self.assertEqual(mock_post.call_args[1]["json"]["duration"], 10)

                self.client.generate_video(prompt="Test", duration="invalid", max_wait_seconds=2, poll_interval=1)
                self.assertEqual(mock_post.call_args[1]["json"]["duration"], 8)

    def test_aspect_ratio_normalization_extended(self):
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"jobid": "job_ar"}
            mock_post.return_value = mock_resp

            with patch("requests.get") as mock_get:
                poll_resp = MagicMock()
                poll_resp.status_code = 200
                poll_resp.json.return_value = {
                    "status": "completed",
                    "response": {"media": [{"videoUrl": "https://gcs/ar.mp4"}]},
                }
                mock_get.return_value = poll_resp

                self.client.generate_video(prompt="Test", aspect_ratio="1:1", max_wait_seconds=2, poll_interval=1)
                self.assertEqual(mock_post.call_args[1]["json"]["aspectRatio"], "1:1")

                self.client.generate_video(prompt="Test", aspect_ratio="square", max_wait_seconds=2, poll_interval=1)
                self.assertEqual(mock_post.call_args[1]["json"]["aspectRatio"], "1:1")

                self.client.generate_video(prompt="Test", aspect_ratio="4:3", max_wait_seconds=2, poll_interval=1)
                self.assertEqual(mock_post.call_args[1]["json"]["aspectRatio"], "4:3")

                self.client.generate_video(prompt="Test", aspect_ratio="3:4", max_wait_seconds=2, poll_interval=1)
                self.assertEqual(mock_post.call_args[1]["json"]["aspectRatio"], "3:4")

    def test_upload_asset_size_limit_and_email_encoding(self):
        self.client.email = "director+vip@studio.ai"
        with tempfile.TemporaryDirectory() as tmp_dir:
            huge_img = Path(tmp_dir) / "huge.png"
            with open(huge_img, "wb") as f:
                f.seek(21 * 1024 * 1024)
                f.write(b"\0")
            res = self.client.upload_asset(huge_img)
            self.assertIsNone(res)

            huge_vid = Path(tmp_dir) / "huge.mp4"
            with open(huge_vid, "wb") as f:
                f.seek(101 * 1024 * 1024)
                f.write(b"\0")
            res = self.client.upload_asset(huge_vid)
            self.assertIsNone(res)

            with patch("requests.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"mediaGenerationId": "mid_enc"}
                mock_post.return_value = mock_resp

                valid_img = Path(tmp_dir) / "valid.png"
                valid_img.write_bytes(b"\x89PNG\r\n\x1a\nvalid")
                self.client.upload_asset(valid_img)
                called_url = mock_post.call_args[0][0]
                self.assertIn("director%2Bvip%40studio.ai", called_url)

    def test_polling_failure_schemas(self):
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"jobid": "job_fail"}
            mock_post.return_value = mock_resp

            with patch("requests.get") as mock_get:
                poll_resp = MagicMock()
                poll_resp.status_code = 200
                poll_resp.json.return_value = {
                    "status": "in_progress",
                    "response": {"failureReasons": ["Safety violation in prompt"]},
                }
                mock_get.return_value = poll_resp

                with self.assertRaises(RuntimeError) as ctx:
                    self.client.generate_video("Prompt", max_wait_seconds=2, poll_interval=1)
                self.assertIn("Safety violation", str(ctx.exception))

            with patch("requests.get") as mock_get:
                poll_resp = MagicMock()
                poll_resp.status_code = 200
                poll_resp.json.return_value = {"error": "Quota exhausted"}
                mock_get.return_value = poll_resp

                with self.assertRaises(RuntimeError) as ctx:
                    self.client.generate_video("Prompt", max_wait_seconds=2, poll_interval=1)
                self.assertIn("Quota exhausted", str(ctx.exception))

            with patch("requests.get") as mock_get:
                poll_resp = MagicMock()
                poll_resp.status_code = 401
                poll_resp.text = "Unauthorized"
                mock_get.return_value = poll_resp

                with self.assertRaises(RuntimeError) as ctx:
                    self.client.generate_video("Prompt", max_wait_seconds=2, poll_interval=1)
                self.assertIn("401", str(ctx.exception))

    def test_extend_video_empty_media_raises(self):
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"jobid": "job_ext_empty"}
            mock_post.return_value = mock_resp

            with patch("requests.get") as mock_get:
                poll_resp = MagicMock()
                poll_resp.status_code = 200
                poll_resp.json.return_value = {
                    "status": "completed",
                    "response": {"media": []},
                }
                mock_get.return_value = poll_resp

                with self.assertRaises(RuntimeError) as ctx:
                    self.client.extend_video("mid_123", "Prompt", max_wait_seconds=2, poll_interval=1)
                self.assertIn("no media items", str(ctx.exception))


class TestFFmpegPipelineExecution(unittest.TestCase):
    """Test actual local FFmpeg executions (synthetic generator, last-frame extraction, stitching)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.work_dir = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_synthetic_clip_and_last_frame_extraction(self):
        engine = VideoGenerationEngine(provider="useapi")
        scene = Scene(
            scene_number=1,
            title="Test Scene",
            duration_seconds=2.0,
            action_description="Test action",
        )
        clip_path = self.work_dir / "scene_01.mp4"
        last_frame_path = self.work_dir / "scene_01_last_frame.png"

        engine._generate_synthetic_clip(scene, clip_path, aspect_ratio="16:9")
        self.assertTrue(clip_path.exists())
        self.assertGreater(clip_path.stat().st_size, 1000)

        ok = engine.extract_last_frame(clip_path, last_frame_path)
        self.assertTrue(ok)
        self.assertTrue(last_frame_path.exists())
        self.assertGreater(last_frame_path.stat().st_size, 500)

    def test_audio_engine_ambient_bed(self):
        audio_engine = AudioEngine()
        out_audio = self.work_dir / "test_ambient.aac"
        ok = audio_engine._generate_ambient_bed(out_audio, duration=3.0)
        self.assertTrue(ok)
        self.assertTrue(out_audio.exists())
        self.assertGreater(out_audio.stat().st_size, 1000)

    def test_editor_stitching_direct_and_xfade(self):
        engine = VideoGenerationEngine()
        editor = VideoEditor()

        # Generate 2 test clips
        scene1 = Scene(
            scene_number=1,
            title="Clip 1",
            duration_seconds=2.0,
            action_description="Act 1",
            transition_to_next=TransitionConfig(transition_type=TransitionType.DISSOLVE, duration_seconds=0.5),
        )
        scene2 = Scene(
            scene_number=2,
            title="Clip 2",
            duration_seconds=2.0,
            action_description="Act 2",
            transition_to_next=TransitionConfig(transition_type=TransitionType.HARD_CUT),
        )
        c1 = self.work_dir / "c1.mp4"
        c2 = self.work_dir / "c2.mp4"
        engine._generate_synthetic_clip(scene1, c1, "16:9")
        engine._generate_synthetic_clip(scene2, c2, "16:9")
        scene1.output_clip_path = str(c1)
        scene2.output_clip_path = str(c2)

        sb = Storyboard(
            project_id="test_stitch",
            title="Stitch Test",
            total_target_duration=4.0,
            scenes=[scene1, scene2],
        )

        final_out = self.work_dir / "final_master.mp4"
        result = editor.stitch_storyboard(sb, final_out, use_transitions=True)
        self.assertTrue(result.exists())
        self.assertGreater(result.stat().st_size, 5000)

    def test_editor_safe_none_transitions_and_get_duration(self):
        engine = VideoGenerationEngine()
        editor = VideoEditor()

        c1 = self.work_dir / "c_none_1.mp4"
        scene1 = Scene(
            scene_number=1,
            title="Clip None 1",
            duration_seconds=2.0,
            action_description="Act 1",
        )
        engine._generate_synthetic_clip(scene1, c1, "16:9")
        scene1.output_clip_path = str(c1)
        # Explicitly set transition_to_next to None
        scene1.transition_to_next = None

        # Verify get_clip_duration reads actual duration or falls back
        dur = editor.get_clip_duration(c1)
        self.assertAlmostEqual(dur, 2.0, delta=0.5)

        missing = self.work_dir / "missing_file_xyz.mp4"
        self.assertEqual(editor.get_clip_duration(missing), 8.0)

        sb = Storyboard(
            project_id="test_none_trans",
            title="None Trans Test",
            scenes=[scene1],
        )
        out_f = self.work_dir / "test_none_master.mp4"
        res = editor.stitch_storyboard(sb, out_f, use_transitions=True)
        self.assertTrue(res.exists())


class TestFastAPIServer(unittest.TestCase):
    """Test FastAPI mini-endpoints using TestClient."""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from server import app
        cls.client = TestClient(app)

    def test_health_check(self):
        resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("ffmpeg_available", data)

    def test_storyboard_lifecycle(self):
        # 1. Create storyboard
        req_payload = {
            "concept": "A detective investigating a glowing neon cipher in the rain",
            "total_duration": 16.0,
            "clip_duration": 8.0,
            "aspect_ratio": "16:9",
            "genre": "Cyberpunk Noir",
        }
        res = self.client.post("/api/v1/storyboard/create", json=req_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        project_id = data["project_id"]
        self.assertIsNotNone(project_id)
        self.assertEqual(data["scene_count"], 2)

        # 2. Retrieve storyboard
        res_get = self.client.get(f"/api/v1/storyboard/{project_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["project_id"], project_id)

        # 3. Retrieve screenplay
        res_screenplay = self.client.get(f"/api/v1/screenplay/{project_id}")
        self.assertEqual(res_screenplay.status_code, 200)
        self.assertIn("transcript", res_screenplay.json())

        # 4. Retrieve characters
        res_chars = self.client.get(f"/api/v1/characters/{project_id}")
        self.assertEqual(res_chars.status_code, 200)
        self.assertGreaterEqual(len(res_chars.json()["characters"]), 1)

        # 5. Render without generated clips should return 400 Bad Request
        res_render = self.client.post(f"/api/v1/render/{project_id}", json={"use_transitions": True, "include_soundtrack": True})
        self.assertEqual(res_render.status_code, 400)

    def test_route_aliases_and_default_post_bodies(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)

        req_payload = {
            "concept": "A detective in neon cyber noir",
            "total_duration": 8.0,
            "clip_duration": 8.0,
            "aspect_ratio": "16:9",
        }
        res = self.client.post("/api/v1/storyboard/create", json=req_payload)
        self.assertEqual(res.status_code, 200)
        proj_id = res.json()["project_id"]

        # Alias routes
        res_alias_bible = self.client.get(f"/api/v1/character-bible/{proj_id}")
        self.assertEqual(res_alias_bible.status_code, 200)

        res_root_bible = self.client.get(f"/character-bible/{proj_id}")
        self.assertEqual(res_root_bible.status_code, 200)

        res_root_sb = self.client.get(f"/storyboard/{proj_id}")
        self.assertEqual(res_root_sb.status_code, 200)

        res_root_sp = self.client.get(f"/screenplay/{proj_id}")
        self.assertEqual(res_root_sp.status_code, 200)

        # Empty body POST to render endpoint (should parse defaults, then 400 due to unrendered clips)
        res_empty_render = self.client.post(f"/api/v1/render/{proj_id}")
        self.assertEqual(res_empty_render.status_code, 400)

        # Empty body POST to publish endpoint (should parse defaults, then 400 due to unrendered master)
        res_empty_pub = self.client.post(f"/api/v1/publish/{proj_id}")
        self.assertEqual(res_empty_pub.status_code, 400)


class TestVideoGenerationEngineEdgeCases(unittest.TestCase):
    """Test VideoGenerationEngine provider routing, fallback, and error handling."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.work_dir = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_last_frame_path_returns_false(self):
        engine = VideoGenerationEngine()
        nonexistent = self.work_dir / "does_not_exist.mp4"
        out_frame = self.work_dir / "frame.png"
        self.assertFalse(engine.extract_last_frame(nonexistent, out_frame))

    def test_unconfigured_useapi_falls_back_to_synthetic_clip(self):
        engine = VideoGenerationEngine(provider="useapi")
        # Ensure client reports unconfigured
        engine.useapi_client.api_token = ""
        scene = Scene(
            scene_number=1,
            title="Fallback Scene",
            duration_seconds=2.0,
            action_description="Fallback action",
        )
        clip = engine.generate_scene_clip(scene, self.work_dir, aspect_ratio="16:9", dry_run=False)
        self.assertTrue(clip.exists())
        self.assertEqual(scene.status, SceneStatus.COMPLETED)
        self.assertTrue(Path(scene.last_frame_path).exists())

    def test_exception_in_useapi_generation_triggers_synthetic_fallback(self):
        engine = VideoGenerationEngine(provider="useapi")
        engine.useapi_client.api_token = "valid_fake_token"
        with patch.object(engine.useapi_client, "generate_video", side_effect=RuntimeError("Google Flow server unavailable")):
            scene = Scene(
                scene_number=2,
                title="Error Fallback Scene",
                duration_seconds=2.0,
                action_description="Error fallback action",
            )
            clip = engine.generate_scene_clip(scene, self.work_dir, aspect_ratio="16:9", dry_run=False)
            self.assertTrue(clip.exists())
            self.assertEqual(scene.status, SceneStatus.FAILED)
            self.assertIn("Google Flow server unavailable", scene.error_message)
            self.assertTrue(Path(scene.output_clip_path).exists())

    def test_continuity_chaining_propagation(self):
        engine = VideoGenerationEngine()
        scene1 = Scene(scene_number=1, title="Shot 1", duration_seconds=1.0, action_description="Scene 1")
        scene2 = Scene(scene_number=2, title="Shot 2", duration_seconds=1.0, action_description="Scene 2", chain_from_previous_last_frame=True)
        sb = Storyboard(project_id="test_chain", title="Chain Test", scenes=[scene1, scene2])

        engine.generate_all_scenes(sb, self.work_dir, dry_run=True)
        self.assertIsNotNone(scene1.last_frame_path)
        self.assertTrue(Path(scene1.last_frame_path).exists())
        self.assertEqual(scene2.reference_image_path, scene1.last_frame_path)

    def test_direct_genai_error_handling(self):
        engine = VideoGenerationEngine(provider="genai", api_key="fake_key")
        mock_op = MagicMock()
        mock_op.done = True
        mock_op.error = "Safety policy violation"
        mock_op.response = None

        mock_models = MagicMock()
        mock_models.generate_videos.return_value = mock_op
        engine.genai_client = MagicMock()
        engine.genai_client.models = mock_models
        engine.genai_client.operations.get.return_value = mock_op

        scene = Scene(
            scene_number=1,
            title="GenAI Error Scene",
            duration_seconds=2.0,
            action_description="Prompt error test",
        )
        clip = engine.generate_scene_clip(scene, self.work_dir, aspect_ratio="16:9", dry_run=False)
        self.assertTrue(clip.exists())
        self.assertEqual(scene.status, SceneStatus.FAILED)
        self.assertIn("Safety policy violation", scene.error_message)

    def test_single_scene_rerender_continuity_propagation(self):
        from server import _bg_generate, active_storyboards
        scene1 = Scene(
            scene_number=1,
            title="Shot 1",
            duration_seconds=1.0,
            action_description="Scene 1",
        )
        fake_last_frame = self.work_dir / "scene_01_last_frame.png"
        fake_last_frame.write_bytes(b"fakepngcontent")
        scene1.last_frame_path = str(fake_last_frame)

        scene2 = Scene(
            scene_number=2,
            title="Shot 2",
            duration_seconds=1.0,
            action_description="Scene 2",
            chain_from_previous_last_frame=True,
        )
        sb = Storyboard(project_id="test_rerender_proj", title="Rerender Chain", scenes=[scene1, scene2])
        active_storyboards["test_rerender_proj"] = sb

        with patch("pipeline.video_gen.VideoGenerationEngine.generate_scene_clip"):
            _bg_generate("test_rerender_proj", scene_number=2, dry_run=True)
            self.assertEqual(scene2.reference_image_path, str(fake_last_frame))


class TestYouTubePublisherEdgeCases(unittest.TestCase):
    """Test YouTubePublisher SEO generation and upload safeguards."""

    def test_seo_metadata_generation(self):
        publisher = YouTubePublisher()
        sb = Storyboard(
            project_id="seo_test",
            title="Cyberpunk Rain Odyssey",
            logline="A detective tracks a neural ghost.",
            genre="Cyberpunk Noir",
            scenes=[
                Scene(scene_number=1, title="Cold Open", timecode_start="00:00", action_description="Intro"),
                Scene(scene_number=2, title="Alleyway Chase", timecode_start="00:08", action_description="Action"),
            ],
        )
        meta = publisher.generate_seo_metadata(sb)
        self.assertIn("Cyberpunk Rain Odyssey", meta["title"])
        self.assertIn("00:00 - Cold Open", meta["description"])
        self.assertIn("00:08 - Alleyway Chase", meta["description"])
        self.assertIn("AI Video", meta["tags"])
        self.assertEqual(meta["categoryId"], "1")

    def test_upload_missing_video_raises_file_not_found(self):
        publisher = YouTubePublisher()
        sb = Storyboard(project_id="missing_vid", title="Ghost")
        with self.assertRaises(FileNotFoundError):
            publisher.upload_video(Path("nonexistent_video.mp4"), sb)

    def test_upload_dry_run_returns_mock_id(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dummy_vid = Path(tmp_dir) / "dummy.mp4"
            dummy_vid.write_bytes(b"dummy_video_stream")
            publisher = YouTubePublisher()
            sb = Storyboard(project_id="mock_pub", title="Mock Video")
            vid_id = publisher.upload_video(dummy_vid, sb, dry_run=True)
            self.assertEqual(vid_id, "dry-run-video-id-xyz")


class TestDirectorAgentEdgeCases(unittest.TestCase):
    """Test DirectorAgent scene math and screenplay guards."""

    def test_scene_math_calculation(self):
        self.assertEqual(Storyboard.calculate_scene_count(8.0, 8.0), 1)
        self.assertEqual(Storyboard.calculate_scene_count(32.0, 8.0), 4)
        self.assertEqual(Storyboard.calculate_scene_count(60.0, 8.0), 8)
        self.assertEqual(Storyboard.calculate_scene_count(0.0, 8.0), 1)

    def test_decompose_with_empty_screenplay_scenes(self):
        director = DirectorAgent()
        empty_screenplay = Screenplay(
            title="Empty",
            logline="Test",
            characters=[],
            scenes=[],
        )
        shots = director._decompose_to_shots(
            screenplay=empty_screenplay,
            num_shots=2,
            total_duration=16.0,
            clip_duration=8.0,
            aspect_ratio="16:9",
            char_image=None,
        )
        self.assertEqual(len(shots), 2)
        self.assertEqual(shots[0].scene_number, 1)
        self.assertEqual(shots[1].scene_number, 2)


class TestMainCLIWorkflow(unittest.TestCase):
    """Test CLI execution flows including single scene re-render and continuity propagation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.work_dir = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_single_scene_rerender_with_continuity(self):
        from main import run_pipeline
        import argparse

        job_id = "test_cli_chain"
        job_file = settings.jobs_dir / f"{job_id}.json"

        last_frame_file = self.work_dir / "scene_01_last_frame.png"
        last_frame_file.write_bytes(b"frame_bytes")

        s1 = Scene(scene_number=1, title="Shot 1", duration_seconds=8.0, action_description="Scene 1", last_frame_path=str(last_frame_file))
        s2 = Scene(scene_number=2, title="Shot 2", duration_seconds=8.0, action_description="Scene 2", chain_from_previous_last_frame=True)
        sb = Storyboard(project_id=job_id, title="CLI Test", scenes=[s1, s2])
        sb.save(job_file)

        mock_args = argparse.Namespace(
            job_id=job_id,
            re_render_scene=2,
            dry_run=True,
            stitch_only=False,
            publish_youtube=False,
            privacy="private",
            duration=16.0,
            mode="short",
            concept="Test",
            title="Test",
            genre="Noir",
            aspect="16:9",
            character_image=None,
            environment_image=None,
            show_screenplay=False,
            show_characters=False,
            review_storyboard=False,
            provider="useapi",
            useapi_model="veo-3.1-fast",
            serve=False,
            port=8080,
        )

        with patch("pipeline.editor.VideoEditor.stitch_storyboard") as mock_stitch, \
             patch("pipeline.audio_gen.AudioEngine.generate_soundtrack_for_storyboard") as mock_audio:
            mock_stitch.return_value = self.work_dir / f"{job_id}_master.mp4"
            mock_audio.return_value = None
            run_pipeline(mock_args)

        updated_sb = Storyboard.load(job_file)
        self.assertEqual(updated_sb.scenes[1].reference_image_path, str(last_frame_file))
        if job_file.exists():
            job_file.unlink()


if __name__ == "__main__":
    unittest.main()
