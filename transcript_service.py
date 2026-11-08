import hashlib
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

SUPADATA_BASE_URL = "https://api.supadata.ai/v1"
SUPABASE_TABLE = "transcripts"
CONSENT_TABLE = "transcript_consents"
LOCK_TABLE = "transcript_generation_locks"
CONSENT_TTL_SECONDS = 600
GENERATION_LOCK_SECONDS = 300
WAIT_FOR_CACHE_SECONDS = 150


class TranscriptUnavailable(Exception):
    """Raised when native captions do not exist and AI consent is required."""


class ConsentError(Exception):
    """Raised when the one-time AI transcription consent token is invalid."""


class CacheUnavailable(Exception):
    """Raised when the transcript cache cannot be checked reliably."""


def _supadata_headers() -> dict[str, str]:
    api_key = os.getenv("SUPADATA_API_KEY")
    if not api_key:
        raise RuntimeError("SUPADATA_API_KEY is not configured on the backend.")
    return {"x-api-key": api_key, "Accept": "application/json"}


def _cache_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def _cache_headers(prefer: str = "return=minimal") -> dict[str, str]:
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    }


def _table_url(table: str) -> str:
    return f"{os.environ['SUPABASE_URL'].rstrip('/')}/rest/v1/{table}"


def _cache_get(video_id: str, preferred_language: str | None = None) -> dict[str, Any] | None:
    if not _cache_configured():
        return None

    params: dict[str, str] = {
        "video_id": f"eq.{video_id}",
        "select": "video_id,language,transcript_text,source",
        "order": "created_at.asc",
        "limit": "1",
    }
    if preferred_language:
        params["language"] = f"eq.{preferred_language}"

    try:
        response = requests.get(
            _table_url(SUPABASE_TABLE), params=params, headers=_cache_headers(), timeout=10
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None
    except Exception as exc:
        logger.exception("Transcript cache lookup failed for video ID %s", video_id)
        # A cache outage must not be mistaken for a cache miss before costly AI generation.
        raise CacheUnavailable(
            "The transcript cache is temporarily unavailable. Please retry shortly."
        ) from exc


def get_cached_transcript(
    video_id: str, preferred_language: str | None = None
) -> dict[str, Any] | None:
    # Prefer the requested language, but fall back to any cached language.
    return _cache_get(video_id, preferred_language) or (
        _cache_get(video_id) if preferred_language else None
    )


def cache_transcript(
    video_id: str,
    language: str,
    transcript_text: str,
    source: str,
    *,
    required: bool = False,
) -> bool:
    """Upsert a transcript and confirm persistence, retrying safely if needed.

    The upsert key is (video_id, language), so repeating the same write is
    idempotent. After any ambiguous failure, read the row back before retrying.
    """
    if not _cache_configured():
        if required:
            raise RuntimeError(
                "Supabase is not configured; refusing to lose an AI-generated transcript."
            )
        return False

    payload = {
        "video_id": video_id,
        "language": language or "und",
        "transcript_text": transcript_text,
        "source": source,
    }
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            response = requests.post(
                _table_url(SUPABASE_TABLE),
                params={"on_conflict": "video_id,language"},
                headers=_cache_headers("resolution=merge-duplicates,return=representation"),
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            rows = response.json()
            if isinstance(rows, list) and any(
                isinstance(row, dict)
                and row.get("video_id") == video_id
                and (row.get("language") or "und") == (language or "und")
                and row.get("transcript_text") == transcript_text
                for row in rows
            ):
                return True
            last_error = RuntimeError(
                "Supabase did not return confirmation of the saved transcript."
            )
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Transcript cache write attempt %s failed for video ID %s",
                attempt + 1,
                video_id,
                exc_info=True,
            )

        # The write may have succeeded even if its response was lost or malformed.
        # Read-after-write prevents unnecessary duplicate work and avoids blind retries.
        try:
            saved = _cache_get(video_id, language or "und")
            if saved and saved.get("transcript_text") == transcript_text:
                return True
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Transcript cache verification attempt %s failed for video ID %s",
                attempt + 1,
                video_id,
                exc_info=True,
            )

        if attempt < 2:
            time.sleep(attempt + 1)

    logger.error("Transcript cache persistence could not be confirmed for video ID %s", video_id)
    if required:
        raise RuntimeError(
            "AI transcription completed, but its transcript could not be confirmed in Supabase. "
            "The result was not marked successful. Please retry after the database issue is resolved."
        ) from last_error
    return False

def _issue_consent_token(video_id: str) -> str:
    if not _cache_configured():
        raise RuntimeError(
            "Persistent consent protection is unavailable. Configure the Supabase cache before enabling AI transcription."
        )

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=CONSENT_TTL_SECONDS)).isoformat()
    response = requests.post(
        _table_url(CONSENT_TABLE),
        headers=_cache_headers(),
        json={"token_hash": token_hash, "video_id": video_id, "expires_at": expires_at},
        timeout=10,
    )
    response.raise_for_status()
    return token


def _consume_consent_token(video_id: str, token: str) -> None:
    if not token or not _cache_configured():
        raise ConsentError("Please approve AI transcription again.")

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    response = requests.patch(
        _table_url(CONSENT_TABLE),
        params={
            "token_hash": f"eq.{token_hash}",
            "video_id": f"eq.{video_id}",
            "consumed_at": "is.null",
            "expires_at": f"gt.{datetime.now(timezone.utc).isoformat()}",
            "select": "token_hash",
        },
        headers=_cache_headers("return=representation"),
        json={"consumed_at": datetime.now(timezone.utc).isoformat()},
        timeout=10,
    )
    response.raise_for_status()
    if not response.json():
        raise ConsentError("Your consent expired or was already used. Please try again.")


def _acquire_generation_lock(video_id: str) -> str | None:
    """Acquire a database-backed lease; a unique video_id allows only one owner."""
    if not _cache_configured():
        raise RuntimeError("Supabase is required to coordinate transcript generation.")

    now = datetime.now(timezone.utc)
    # Remove only an expired lease. The unique key arbitrates simultaneous inserts.
    cleanup = requests.delete(
        _table_url(LOCK_TABLE),
        params={
            "video_id": f"eq.{video_id}",
            "expires_at": f"lt.{now.isoformat()}",
        },
        headers=_cache_headers(),
        timeout=10,
    )
    cleanup.raise_for_status()

    owner = secrets.token_urlsafe(24)
    expires_at = (now + timedelta(seconds=GENERATION_LOCK_SECONDS)).isoformat()
    response = requests.post(
        _table_url(LOCK_TABLE),
        headers=_cache_headers("return=minimal"),
        json={"video_id": video_id, "owner_token": owner, "expires_at": expires_at},
        timeout=10,
    )
    if response.status_code == 409:
        return None
    response.raise_for_status()
    return owner


def _release_generation_lock(video_id: str, owner: str) -> None:
    try:
        response = requests.delete(
            _table_url(LOCK_TABLE),
            params={"video_id": f"eq.{video_id}", "owner_token": f"eq.{owner}"},
            headers=_cache_headers(),
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        logger.exception("Could not release transcript generation lock for video ID %s", video_id)


def _wait_for_cached_transcript(
    video_id: str, preferred_language: str | None
) -> dict[str, Any] | None:
    deadline = time.monotonic() + WAIT_FOR_CACHE_SECONDS
    while time.monotonic() < deadline:
        cached = get_cached_transcript(video_id, preferred_language)
        if cached and cached.get("transcript_text"):
            return cached
        time.sleep(3)
    return None


def _poll_supadata_job(job_id: str) -> dict[str, Any]:
    headers = _supadata_headers()
    deadline = time.monotonic() + 180
    transient_attempt = 0

    while time.monotonic() < deadline:
        time.sleep(2)
        try:
            response = requests.get(
                f"{SUPADATA_BASE_URL}/transcript/{job_id}",
                headers=headers,
                timeout=20,
            )
            if response.status_code == 429 or response.status_code >= 500:
                transient_attempt += 1
                if transient_attempt > 5:
                    response.raise_for_status()
                time.sleep(min(2 ** transient_attempt, 12))
                continue
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict):
                raise RuntimeError("Supadata returned an invalid job response.")
            transient_attempt = 0
        except (requests.Timeout, requests.ConnectionError):
            transient_attempt += 1
            if transient_attempt > 5:
                raise RuntimeError("Could not check the Supadata job after several retries.")
            time.sleep(min(2 ** transient_attempt, 12))
            continue

        status = result.get("status")
        if status == "completed":
            completed = result.get("result") or result
            if not isinstance(completed, dict):
                raise RuntimeError("Supadata returned an invalid completed transcript.")
            return completed
        if status == "failed":
            error = result.get("error") or {}
            message = error.get("message") if isinstance(error, dict) else str(error)
            raise RuntimeError(str(message or "Transcript generation failed."))
        if status not in {"queued", "processing", "pending", None}:
            raise RuntimeError(f"Supadata returned an unknown job status: {status}")

    raise TimeoutError("Supadata transcript job took too long. Please try again.")


def fetch_supadata_transcript(video_url: str, mode: str) -> dict[str, Any]:
    try:
        response = requests.get(
            f"{SUPADATA_BASE_URL}/transcript",
            params={"url": video_url, "text": "true", "mode": mode},
            headers=_supadata_headers(),
            timeout=45,
        )
    except (requests.Timeout, requests.ConnectionError) as exc:
        # Do not blindly retry the generation request: the provider may have accepted it.
        raise RuntimeError("Could not reach Supadata. Please retry shortly.") from exc

    if response.status_code == 202:
        try:
            job = response.json()
            job_id = job.get("jobId") if isinstance(job, dict) else None
            if not job_id:
                raise RuntimeError("Supadata accepted the request but did not return a job ID.")
        except ValueError as exc:
            raise RuntimeError("Supadata returned an invalid job response.") from exc
        result = _poll_supadata_job(str(job_id))
    else:
        try:
            result = response.json()
        except ValueError:
            result = {}

        if response.status_code >= 400:
            error_code = result.get("error") if isinstance(result, dict) else None
            message = result.get("message") if isinstance(result, dict) else None
            message = message or "Supadata could not retrieve this transcript."
            if mode == "native" and error_code == "transcript-unavailable":
                raise TranscriptUnavailable(message)
            response.raise_for_status()
            raise RuntimeError(f"Supadata request failed ({response.status_code}): {message}")

    if not isinstance(result, dict):
        raise RuntimeError("Supadata returned an invalid transcript response.")

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


def _cached_response(cached: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": cached["transcript_text"],
        "language": cached.get("language") or "und",
        "source": cached.get("source") or "cache",
        "cached": True,
        "available_languages": [],
    }


def get_video_transcript(
    video_id: str,
    video_url: str,
    consent_token: str | None = None,
    preferred_language: str | None = None,
) -> dict[str, Any]:
    cached = get_cached_transcript(video_id, preferred_language)
    if cached and cached.get("transcript_text"):
        return _cached_response(cached)

    if consent_token:
        _consume_consent_token(video_id, consent_token)
        owner = _acquire_generation_lock(video_id)
        if owner is None:
            cached = _wait_for_cached_transcript(video_id, preferred_language)
            if cached:
                return _cached_response(cached)
            return {
                "status": "generation_in_progress",
                "message": "Another request is already generating this transcript. Please retry in a moment.",
            }

        try:
            # Recheck after acquiring the lease in case another request just completed.
            cached = get_cached_transcript(video_id, preferred_language)
            if cached and cached.get("transcript_text"):
                return _cached_response(cached)
            result = fetch_supadata_transcript(video_url, mode="generate")
            cache_transcript(video_id, result["language"], result["text"], "ai_generated", required=True)
            return {
                "text": result["text"],
                "language": result["language"],
                "source": "ai_generated",
                "cached": False,
                "available_languages": result["available_languages"],
            }
        finally:
            _release_generation_lock(video_id, owner)

    try:
        result = fetch_supadata_transcript(video_url, mode="native")
        source = "native"
    except TranscriptUnavailable:
        token = _issue_consent_token(video_id)
        return {
            "status": "ai_consent_required",
            "message": "No existing captions were found. AI transcription may use additional Supadata credits. Do you want to continue?",
            "consent_token": token,
        }

    cache_transcript(video_id, result["language"], result["text"], source)
    return {
        "text": result["text"],
        "language": result["language"],
        "source": source,
        "cached": False,
        "available_languages": result["available_languages"],
    }
