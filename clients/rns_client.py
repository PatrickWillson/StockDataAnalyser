"""
RNS results announcements from the Investegate archive (config/rns_config.py): a London listing's final-results
announcements, newest first, and each announcement's page. Announcements never change, so each is cached on disk
(data/cache/rns, gitignored: the archive's terms allow private-investor use with no redistribution); a company's
listing pages are cached for RNS_LISTING_CACHE_DAYS. Requests are at least RNS_MIN_REQUEST_INTERVAL apart.
"""

import logging
import os
import re
import time
from dataclasses import dataclass
from typing import List, Optional

import requests

from config.rns_config import (RNS_BASE_URL, RNS_CACHE_DIR, RNS_LISTING_CACHE_DAYS, RNS_MAX_LISTING_PAGES,
                               RNS_MIN_REQUEST_INTERVAL, RNS_USER_AGENT)
from core.errors import DataSourceError

logger = logging.getLogger(__name__)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The slug of a final (annual) results announcement; interims, trading updates and the like are left out
RESULTS_SLUG = re.compile(
    r"/(?:final-results|full-year-results|preliminary-results|annual-results|audited-results|final-audited-results|"
    r"audited-final-results|preliminary-final-results|results-for-the-year|final-results-for-the-year|"
    r"annual-financial-report|annual-report-and-accounts)[a-z0-9-]*/(\d+)$")
ANNOUNCEMENT_LINK = re.compile(r'href="(https://www\.investegate\.co\.uk/announcement/[^"]+)"')


class RnsRequestError(DataSourceError):
    """The announcement archive could not be read."""


@dataclass(frozen=True)
class RnsAnnouncement:
    """One results announcement: its archive id (increasing with time) and URL."""
    announcement_id: int
    url: str


class RnsClient:
    """Investegate's archive of RNS announcements (no key)."""

    def __init__(self, cache_dir: Optional[str] = None, debug: bool = False):
        self.cache_dir = cache_dir or os.path.join(REPO_ROOT, RNS_CACHE_DIR)
        self.session = requests.Session()
        self.debug = debug
        self._last_request = 0.0

    def _download(self, url: str) -> str:
        wait = RNS_MIN_REQUEST_INTERVAL - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        try:
            response = self.session.get(url, headers={"User-Agent": RNS_USER_AGENT}, timeout=60)
        except requests.exceptions.RequestException as e:
            raise RnsRequestError(f"RNS archive request failed: {type(e).__name__}") from None
        finally:
            self._last_request = time.monotonic()
        if response.status_code == 404:
            return ""
        if response.status_code != 200:
            raise RnsRequestError(f"RNS archive returned status {response.status_code} for {url}")
        return response.content.decode("utf-8", errors="replace")

    def _cached(self, url: str, path: str, max_age_days: Optional[float] = None) -> str:
        if os.path.exists(path) and (max_age_days is None
                                     or time.time() - os.path.getmtime(path) < max_age_days * 86400):
            with open(path, encoding="utf-8") as f:
                return f.read()
        text = self._download(url)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return text

    def results_announcements(self, tidm: str) -> List[RnsAnnouncement]:
        """The listing's final-results announcements, newest first ([] when the archive has no such company)."""
        tidm = tidm.upper()
        if not re.fullmatch(r"[A-Z0-9]{1,6}", tidm):
            return []
        found = {}
        for page in range(1, RNS_MAX_LISTING_PAGES + 1):
            listing = self._cached(f"{RNS_BASE_URL}/company/{tidm}?page={page}",
                                   os.path.join(self.cache_dir, tidm, f"list_{page}.html"), RNS_LISTING_CACHE_DAYS)
            links = ANNOUNCEMENT_LINK.findall(listing)
            for url in links:
                m = RESULTS_SLUG.search(url)
                # only the company's own: every page also links other issuers' latest results (a sidebar)
                if m and f"--{tidm.lower()}/" in url:
                    found[int(m.group(1))] = url
            if not links or f"page={page + 1}" not in listing:
                break
        return [RnsAnnouncement(i, found[i]) for i in sorted(found, reverse=True)]

    def fetch_announcement(self, announcement: RnsAnnouncement) -> str:
        """The announcement's page (HTML), cached for good."""
        return self._cached(announcement.url, os.path.join(self.cache_dir, "announcements",
                                                           f"{announcement.announcement_id}.html"))
