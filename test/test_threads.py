#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2026 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gallery_dl.extractor.threads import ThreadsPostExtractor  # noqa E402


class TestThreads(unittest.TestCase):

    def test_decode_shortcode(self):
        self.assertEqual(
            ThreadsPostExtractor.decode_shortcode("C30eveaOmoJ"),
            "3311406829887187465",
        )

    def test_extract_files_image(self):
        post = {
            "image_versions2": {
                "candidates": [
                    {"url": "https://example.org/small.jpg", "width": 320,
                     "height": 320},
                    {"url": "https://example.org/large.jpg", "width": 1440,
                     "height": 1440},
                ],
            },
            "original_width": 1440,
            "original_height": 1440,
            "media_type": 19,
            "pk": "1",
        }

        files = ThreadsPostExtractor.extract_files(post)

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["url"], "https://example.org/large.jpg")
        self.assertEqual(files[0]["type"], "image")
        self.assertEqual(files[0]["extension"], "jpg")

    def test_extract_files_carousel_and_video(self):
        post = {
            "carousel_media": [
                {
                    "pk": "11",
                    "media_type": 19,
                    "image_versions2": {
                        "candidates": [
                            {"url": "https://example.org/image.jpg",
                             "width": 1080, "height": 720},
                        ],
                    },
                    "original_width": 1080,
                    "original_height": 720,
                },
                {
                    "pk": "12",
                    "media_type": 2,
                    "video_duration": 7.25,
                    "has_audio": True,
                    "video_versions": [
                        {"url": "https://example.org/video-low.mp4",
                         "width": 640, "height": 360},
                        {"url": "https://example.org/video-high.mp4",
                         "width": 1920, "height": 1080},
                    ],
                    "original_width": 1920,
                    "original_height": 1080,
                },
            ],
        }

        files = ThreadsPostExtractor.extract_files(post)

        self.assertEqual(len(files), 2)
        self.assertEqual(files[0]["type"], "image")
        self.assertEqual(files[0]["num"], 1)
        self.assertEqual(files[1]["type"], "video")
        self.assertEqual(files[1]["url"], "https://example.org/video-high.mp4")
        self.assertEqual(files[1]["num"], 2)
        self.assertEqual(files[1]["duration"], 7.25)
        self.assertEqual(files[1]["extension"], "mp4")

    def test_post_text_fallback(self):
        post = {
            "caption": None,
            "text_post_app_info": {
                "text_fragments": {
                    "fragments": [
                        {"plaintext": "Hello"},
                        {"plaintext": " world"},
                    ],
                },
            },
        }

        self.assertEqual(ThreadsPostExtractor._post_text(post), "Hello world")

    def test_has_video_and_prefer_post(self):
        image_post = {
            "image_versions2": {"candidates": [{"url": "https://e/x.jpg"}]},
        }
        video_post = {
            "video_versions": [{"url": "https://e/x.mp4"}],
        }
        truncated = {
            "media_type": 8,
            "carousel_media": [{
                "pk": "1",
                "video_versions": [{"url": "https://e/a.mp4", "width": 1,
                                    "height": 1}],
            }],
        }
        full = {
            "media_type": 8,
            "carousel_media": [
                {
                    "pk": "1",
                    "video_versions": [{"url": "https://e/a.mp4", "width": 1,
                                        "height": 1}],
                },
                {
                    "pk": "2",
                    "video_versions": [{"url": "https://e/b.mp4", "width": 1,
                                        "height": 1}],
                },
            ],
        }

        self.assertFalse(ThreadsPostExtractor._has_video(image_post))
        self.assertTrue(ThreadsPostExtractor._has_video(video_post))
        self.assertTrue(ThreadsPostExtractor._prefer_post(video_post, image_post))
        self.assertFalse(ThreadsPostExtractor._prefer_post(image_post, video_post))
        self.assertTrue(ThreadsPostExtractor._carousel_incomplete(truncated))
        self.assertFalse(ThreadsPostExtractor._carousel_incomplete(full))
        self.assertTrue(ThreadsPostExtractor._prefer_post(full, truncated))
        self.assertFalse(ThreadsPostExtractor._prefer_post(truncated, full))

    def test_auth_fallback_after_graphql_failure(self):
        video_post = {
            "pk": "3969586254656068720",
            "code": "DcWzaq2DFxw",
            "media_type": 2,
            "user": {"username": "babbyang.g", "pk": "123"},
            "video_versions": [
                {"url": "https://example.org/video.mp4", "width": 1080,
                 "height": 1920},
            ],
        }

        class DummyExtractor(ThreadsPostExtractor):
            def __init__(self):
                self.post_shortcode = "DcWzaq2DFxw"
                self.post_id = "3969586254656068720"
                self._logged_in = True
                self.log = type("Log", (), {"debug": lambda *a: None})()

            def _post_data(self, lsd, logged_in=False, fatal=True):
                return {}

            def _media_info_post(self, fatal=True):
                return video_post

            def _profile_post_data(self, user_id, lsd, fatal=True):
                return {}

        ext = DummyExtractor()
        post = ext._auth_fallback_post({}, "lsd-token")
        files = ThreadsPostExtractor.extract_files(post)

        self.assertEqual(post, video_post)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["type"], "video")


if __name__ == "__main__":
    unittest.main()
