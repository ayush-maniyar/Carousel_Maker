import unittest
from unittest.mock import Mock, patch

import transcript_service as service


class TranscriptServiceTests(unittest.TestCase):
    @patch.object(service, "fetch_supadata_transcript")
    @patch.object(service, "get_cached_transcript")
    def test_cache_hit_never_calls_supadata(self, cached, fetch):
        cached.return_value = {
            "transcript_text": "A previously saved transcript with enough text.",
            "language": "en",
            "source": "ai_generated",
        }

        result = service.get_video_transcript("abcdefghijk", "https://youtu.be/abcdefghijk")

        self.assertTrue(result["cached"])
        self.assertEqual(result["source"], "ai_generated")
        fetch.assert_not_called()

    @patch.object(service, "_issue_consent_token", return_value="one-time-token")
    @patch.object(service, "fetch_supadata_transcript", side_effect=service.TranscriptUnavailable())
    @patch.object(service, "get_cached_transcript", return_value=None)
    def test_native_missing_requests_consent_without_ai_call(self, cached, fetch, issue):
        result = service.get_video_transcript("abcdefghijk", "https://youtu.be/abcdefghijk")

        self.assertEqual(result["status"], "ai_consent_required")
        self.assertEqual(result["consent_token"], "one-time-token")
        fetch.assert_called_once_with("https://youtu.be/abcdefghijk", mode="native")
        issue.assert_called_once_with("abcdefghijk")

    @patch.object(service, "_consume_consent_token", side_effect=service.ConsentError("invalid"))
    @patch.object(service, "fetch_supadata_transcript")
    @patch.object(service, "get_cached_transcript", return_value=None)
    def test_invalid_consent_token_never_calls_ai(self, cached, fetch, consume):
        with self.assertRaises(service.ConsentError):
            service.get_video_transcript(
                "abcdefghijk",
                "https://youtu.be/abcdefghijk",
                consent_token="bad-token",
            )
        fetch.assert_not_called()

    @patch.object(service, "_release_generation_lock")
    @patch.object(service, "cache_transcript")
    @patch.object(
        service,
        "fetch_supadata_transcript",
        return_value={"text": "A sufficiently long generated transcript.", "language": "en", "available_languages": []},
    )
    @patch.object(service, "_acquire_generation_lock", return_value="lock-owner")
    @patch.object(service, "_consume_consent_token")
    @patch.object(service, "get_cached_transcript", return_value=None)
    def test_valid_consent_generates_and_caches_once(
        self, cached, consume, acquire, fetch, cache, release
    ):
        result = service.get_video_transcript(
            "abcdefghijk",
            "https://youtu.be/abcdefghijk",
            consent_token="valid-token",
        )

        self.assertEqual(result["source"], "ai_generated")
        self.assertFalse(result["cached"])
        fetch.assert_called_once_with("https://youtu.be/abcdefghijk", mode="generate")
        cache.assert_called_once()
        release.assert_called_once_with("abcdefghijk", "lock-owner")

    @patch.object(service, "_wait_for_cached_transcript", return_value={
        "transcript_text": "Shared transcript from the request already in progress.",
        "language": "en",
        "source": "ai_generated",
    })
    @patch.object(service, "_acquire_generation_lock", return_value=None)
    @patch.object(service, "_consume_consent_token")
    @patch.object(service, "fetch_supadata_transcript")
    @patch.object(service, "get_cached_transcript", return_value=None)
    def test_concurrent_request_reuses_shared_cache(
        self, cached, fetch, consume, acquire, wait
    ):
        result = service.get_video_transcript(
            "abcdefghijk",
            "https://youtu.be/abcdefghijk",
            consent_token="second-user-token",
        )

        self.assertTrue(result["cached"])
        fetch.assert_not_called()
        wait.assert_called_once()

    @patch.object(service, "_cache_get")
    def test_cache_prefers_requested_language_then_falls_back(self, cache_get):
        fallback = {"transcript_text": "Cached English transcript.", "language": "en"}
        cache_get.side_effect = [None, fallback]

        result = service.get_cached_transcript("abcdefghijk", "fr")

        self.assertEqual(result, fallback)
        self.assertEqual(cache_get.call_args_list[0].args, ("abcdefghijk", "fr"))
        self.assertEqual(cache_get.call_args_list[1].args, ("abcdefghijk",))

    @patch.object(service.time, "sleep")
    @patch.object(service, "_supadata_headers", return_value={})
    @patch.object(service.requests, "get")
    def test_poll_retries_temporary_server_error(self, get, headers, sleep):
        temporary = Mock(status_code=503)
        completed = Mock(status_code=200)
        completed.json.return_value = {
            "status": "completed",
            "result": {"content": "Recovered transcript", "lang": "en"},
        }
        get.side_effect = [temporary, completed]

        result = service._poll_supadata_job("job-123")

        self.assertEqual(result["content"], "Recovered transcript")
        self.assertEqual(get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
