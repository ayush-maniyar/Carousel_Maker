import logging
import os
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

SUPADATA_BASE_URL = "https://api.supadata.ai/v1"
SUPABASE_TABLE = "transcripts"


class TranscriptUnavailable(Exception):
    """Raised when native captions do not exist and AI consent is required."""


def _supadata_headers() -> dict[str, str]:
    api_key = os.getenv("SUPADATA_API_KEY")
    if not api_key:
        raise RuntimeError("SUPADATA_API_KEY is not configured on the backend.")
    return {"x-api-key": api_key, "Accept": "application/json"}


def _cache_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def _cache_headers() -> dict[str, str]:
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }


def get_cached_transcript(video_id: str) -> dict[str, Any] | None:
    if not _cache_configured():
        return None

    url = f"{os.environ['SUPABASE_URL'].rstrip('/')}/rest/v1/{SUPABASE_TABLE}"
    try:
        response = requests.get(
            url,
            params={
                "video_id": f"eq.{video_id}",
                "select": "video_id,language,transcript_text,source",
                "limit": "1",
            },
            headers=_cache_headers(),
            timeout=10,
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None
    except Exception:
        logger.exception("Transcript cache lookup failed for video ID %s", video_id)
        return None


def cache_transcript(video_id: str, language: str, transcript_text: str, source: str) -> None:
    if not _cache_configured():
        return

    url = f"{os.environ['SUPABASE_URL'].rstrip('/')}/rest/v1/{SUPABASE_TABLE}"
    payload = {
        "video_id": video_id,
        "language": language or "und",
        "transcript_text": transcript_text,
        "source": source,
    }
    try:
        response = requests.post(
            url,
            params={"on_conflict": "video_id,language"},
            headers=_cache_headers(),
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
    except Exception:
        # A cache outage must not prevent a user from generating a carousel.
        logger.exception("Transcript cache write failed for video ID %s", video_id)


def _poll_supadata_job(job_id: str) -> dict[str, Any]:
    headers = _supadata_headers()
    for _ in range(60):
        time.sleep(2)
        response = requests.get(
            f"{SUPADATA_BASE_URL}/transcript/{job_id}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        status = result.get("status")
        if status == "completed":
            return result.get("result") or result
        if status == "failed":
            error = result.get("error") or {}
            raise TranscriptUnavailable(str(error.get("message") or "Transcript generation failed."))
    raise TimeoutError("Supadata transcript job took too long. Please try again.")


def fetch_supadata_transcript(video_url: str, mode: str) -> dict[str, Any]:
    response = requests.get(
        f"{SUPADATA_BASE_URL}/transcript",
        params={"url": video_url, "text": "true", "mode": mode},
        headers=_supadata_headers(),
        timeout=45,
    )

    if response.status_code == 202:
        job = response.json()
        result = _poll_supadata_job(job["jobId"])
    else:
        try:
            result = response.json()
        except ValueError:
            result = {}

        if response.status_code >= 400:
            error_code = result.get("error")
            message = result.get("message") or "Supadata could not retrieve this transcript."
            if mode == "native" and error_code == "transcript-unavailable":
                raise TranscriptUnavailable(message)
            raise RuntimeError(f"Supadata request failed ({response.status_code}): {message}")

    content = result.get("content", "")
    if isinstance(content, list):
        content = " ".join(
            item.get("text", "") for item in content if isinstance(item, dict)
        )
    transcript_text = str(content).strip()
    if not transcript_text:
        if mode == "native":
            raise TranscriptUnavailable("No native captions are available for this video.")
        raise RuntimeError("Supadata returned an empty transcript.")

    return {
        "text": transcript_text,
        "language": result.get("lang") or "und",
        "available_languages": result.get("availableLangs") or [],
    }


def get_video_transcript(video_id: str, video_url: str, allow_ai_fallback: bool = False) -> dict[str, Any]:
    cached = get_cached_transcript(video_id)
    if cached and cached.get("transcript_text"):
        return {
            "text": cached["transcript_text"],
            "language": cached.get("language") or "und",
            "source": cached.get("source") or "cache",
            "cached": True,
            "available_languages": [],
        }

    if allow_ai_fallback:
        # The frontend only sends this after native mode reported no captions.
        # Do not repeat the native request: that would spend another credit.
        result = fetch_supadata_transcript(video_url, mode="generate")
        source = "ai_generated"
    else:
        try:
            result = fetch_supadata_transcript(video_url, mode="native")
            source = "native"
        except TranscriptUnavailable:
            return {
                "status": "ai_consent_required",
                "message": "No existing captions were found. AI transcription may use additional Supadata credits. Do you want to continue?",
            }

    cache_transcript(video_id, result["language"], result["text"], source)
    return {
        "text": result["text"],
        "language": result["language"],
        "source": source,
        "cached": False,
        "available_languages": result["available_languages"],
    }
