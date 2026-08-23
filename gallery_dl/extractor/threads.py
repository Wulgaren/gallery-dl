# -*- coding: utf-8 -*-

# Copyright 2026 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.threads.com/"""

from .common import Extractor, Message
from .. import exception, text, util

BASE_PATTERN = r"(?:https?://)?(?:www\.)?threads\.(?:com|net)"
_SHORTCODE_ALPHABET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789-_"
)
_POST_QUERY_ID = "26935506582720108"
_POST_QUERY_NAME = "BarcelonaPermalinkMobilePostColumnPageQuery"
_PROFILE_POSTS_QUERY_ID = "6232751443445612"
_PROFILE_POSTS_QUERY_NAME = "BarcelonaProfileThreadsTabQuery"
_POST_QUERY_VARS = {
    "__relay_internal__pv__BarcelonaHasInlineReplyComposerrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasDearAlgoConsumptionrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaIsLoggedInrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasEventBadgerelayprovider":
        False,
    "__relay_internal__pv__BarcelonaThreadsWebCachingImprovements"
    "relayprovider":
        False,
    "__relay_internal__pv__BarcelonaIsSearchDiscoveryEnabledrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasCommunitiesrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasGameScoreSharerelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasPublicViewCountCardrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasCommunityEntityCardrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasScorecardCommunityrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasMusicrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasMessagingrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasGhostPostEmojiActivationrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaOptionalCookiesEnabledrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasDearAlgoWebProductionrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaIsCrawlerrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaHasCommunityTopContributorsrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaCanSeeSponsoredContentrelayprovider":
        False,
    "__relay_internal__pv__BarcelonaShouldShowFediverseM075Features"
    "relayprovider":
        False,
    "__relay_internal__pv__BarcelonaIsInternalUserrelayprovider":
        False,
}


class ThreadsPostExtractor(Extractor):
    """Extractor for Threads posts"""
    category = "threads"
    subcategory = "post"
    root = "https://www.threads.net"
    cookies_names = ("sessionid",)
    directory_fmt = ("{category}", "{username}")
    filename_fmt = "{post_shortcode}_{num}.{extension}"
    archive_fmt = "{post_id}_{num}"
    pattern = (BASE_PATTERN +
               r"/(?:@[^/?#]+/post|t)/([A-Za-z0-9_-]+)"
               r"(?:/[^?#]*)?(?:[?#].*)?$")
    example = "https://www.threads.com/@threads/post/C30eveaOmoJ"

    def __init__(self, match):
        Extractor.__init__(self, match)
        self.post_shortcode = match[1]
        self.post_id = self.decode_shortcode(self.post_shortcode)
        self._logged_in = False

    def _init(self):
        self._logged_in = self._has_auth_cookies()

    def items(self):
        page = self.request(self._page_url()).text
        lsd = self._extract_lsd(page)
        post = self._post_data(lsd)

        if self._logged_in and (
                not self._has_video(post) or self._carousel_incomplete(post)):
            post = self._auth_fallback_post(post, lsd)
        elif not self._logged_in and self._carousel_incomplete(post):
            self.log.warning(
                "Carousel may be incomplete. Use authenticated cookies "
                "to download all slides")

        data = self.metadata(post)
        files = self.extract_files(post)
        if not files:
            self.log.info("Post contains no downloadable media")
            return

        data["count"] = len(files)
        yield Message.Directory, "", data

        for file in files:
            file.update(data)
            yield Message.Url, file["url"], file

    def metadata(self, post):
        user = post.get("user") or {}
        info = post.get("text_post_app_info") or {}

        return {
            "post_id"      : str(post.get("pk") or self.post_id),
            "post_shortcode": post.get("code") or self.post_shortcode,
            "post_url"     : self._post_url(user.get("username")),
            "username"     : user.get("username") or "",
            "user_id"      : str(user.get("pk") or user.get("id") or ""),
            "full_name"    : user.get("full_name") or "",
            "is_verified"  : user.get("is_verified"),
            "date"         : self.parse_timestamp(post.get("taken_at")),
            "description"  : self._post_text(post),
            "text"         : self._post_text(post),
            "reply_count"  : info.get("direct_reply_count"),
            "repost_count" : info.get("repost_count"),
            "quote_count"  : info.get("quote_count"),
            "like_count"   : post.get("like_count"),
            "media_type"   : post.get("media_type"),
        }

    def _page_url(self):
        return f"https://www.threads.com/t/{self.post_shortcode}"

    def _post_url(self, username=None):
        if username:
            return f"https://www.threads.com/@{username}/post/{self.post_shortcode}"
        return self._page_url()

    def _post_data(self, lsd, logged_in=False, fatal=True):
        variables = dict(_POST_QUERY_VARS)
        variables["postID"] = self.post_id
        if logged_in:
            variables["__relay_internal__pv__BarcelonaIsLoggedIn"
                      "relayprovider"] = True
            variables["__relay_internal__pv__BarcelonaOptionalCookiesEnabled"
                      "relayprovider"] = True

        data = self.request_json(
            self.root + "/api/graphql",
            method="POST",
            fatal=fatal,
            headers={
                "Accept"            : "*/*",
                "Accept-Language"   : "en-US,en;q=0.9",
                "Content-Type"      : "application/x-www-form-urlencoded; "
                                      "charset=UTF-8",
                "Origin"            : self.root,
                "Referer"           : self._page_url(),
                "Sec-Fetch-Site"    : "same-origin",
                "X-Asbd-Id"         : "129477",
                "X-FB-Friendly-Name": _POST_QUERY_NAME,
                "X-FB-Lsd"          : lsd,
                "X-IG-App-Id"       : "238260118697367",
            },
            data={
                "lsd"      : lsd,
                "variables": util.json_dumps(variables),
                "doc_id"   : _POST_QUERY_ID,
            },
        )

        post = data.get("data", {}).get("media")
        if post:
            return post

        errors = data.get("errors") or ()
        if errors:
            self.log.debug("Threads API errors: %s", errors)
        if fatal:
            raise exception.StopExtraction("Unable to retrieve post data")
        return {}

    def _auth_fallback_post(self, post, lsd):
        user_id = post.get("user", {}).get("pk") or post.get("user", {}).get("id")

        # Threads GraphQL often returns only the first carousel slide.
        # Instagram media info returns the full carousel_media list.
        info_post = self._media_info_post(fatal=False)
        if self._prefer_post(info_post, post):
            self.log.debug("Using Instagram media-info data")
            return info_post

        auth_post = self._post_data(lsd, logged_in=True, fatal=False)
        if self._prefer_post(auth_post, post):
            self.log.debug("Using authenticated permalink data")
            return auth_post

        if user_id:
            auth_post = self._profile_post_data(str(user_id), lsd, fatal=False)
            if self._prefer_post(auth_post, post):
                self.log.debug("Using authenticated profile-post data")
                return auth_post

        return post

    def _media_info_post(self, fatal=True):
        """Fetch full media via Instagram's media info API."""
        csrf = self._csrf_token()
        data = self.request_json(
            f"https://www.instagram.com/api/v1/media/{self.post_id}/info/",
            fatal=fatal,
            headers={
                "Accept"            : "*/*",
                "Referer"           : self._page_url(),
                "Sec-Fetch-Site"    : "same-site",
                "X-Asbd-Id"         : "129477",
                "X-CSRFToken"       : csrf,
                "X-IG-App-Id"       : "238260118697367",
                "X-Requested-With"  : "XMLHttpRequest",
            },
        )
        if not data:
            return {}
        items = data.get("items") or ()
        return items[0] if items else {}

    def _csrf_token(self):
        for domain in (".threads.com", ".instagram.com",
                       "www.threads.com", "www.instagram.com"):
            for cookie in self.cookies:
                if cookie.name == "csrftoken" and cookie.domain == domain:
                    return cookie.value or ""
        for cookie in self.cookies:
            if cookie.name == "csrftoken":
                return cookie.value or ""
        return ""

    def _profile_post_data(self, user_id, lsd, fatal=True):
        data = self.request_json(
            self.root + "/api/graphql",
            method="POST",
            fatal=fatal,
            headers={
                "Accept"            : "*/*",
                "Accept-Language"   : "en-US,en;q=0.9",
                "Content-Type"      : "application/x-www-form-urlencoded; "
                                      "charset=UTF-8",
                "Origin"            : self.root,
                "Referer"           : self._post_url(),
                "Sec-Fetch-Site"    : "same-origin",
                "X-Asbd-Id"         : "129477",
                "X-FB-Friendly-Name": _PROFILE_POSTS_QUERY_NAME,
                "X-FB-Lsd"          : lsd,
                "X-IG-App-Id"       : "238260118697367",
            },
            data={
                "lsd"      : lsd,
                "variables": util.json_dumps({"userID": user_id}),
                "doc_id"   : _PROFILE_POSTS_QUERY_ID,
            },
        )

        for thread in data.get("data", {}).get("mediaData", {}).get("threads", ()):
            for item in thread.get("thread_items", ()):
                candidate = item.get("post") or {}
                if candidate.get("code") == self.post_shortcode:
                    return candidate

        return {}

    @staticmethod
    def decode_shortcode(shortcode):
        value = 0
        for letter in shortcode:
            value = value * 64 + _SHORTCODE_ALPHABET.index(letter)
        return str(value)

    @staticmethod
    def extract_files(post):
        files = []
        entries = post.get("carousel_media") or (post,)

        for num, entry in enumerate(entries, 1):
            file = ThreadsPostExtractor._extract_file(entry, num)
            if file:
                files.append(file)

        return files

    @staticmethod
    def _has_video(post):
        if not post:
            return False
        for entry in post.get("carousel_media") or (post,):
            if entry.get("video_versions"):
                return True
        return False

    @staticmethod
    def _carousel_incomplete(post):
        """True when GraphQL likely truncated a carousel to one slide."""
        if not post or post.get("media_type") != 8:
            return False
        return len(post.get("carousel_media") or ()) < 2

    @staticmethod
    def _prefer_post(candidate, current):
        if not candidate:
            return False
        cand_files = len(ThreadsPostExtractor.extract_files(candidate))
        curr_files = len(ThreadsPostExtractor.extract_files(current))
        if cand_files != curr_files:
            return cand_files > curr_files
        if ThreadsPostExtractor._has_video(candidate):
            return not ThreadsPostExtractor._has_video(current)
        return False

    @staticmethod
    def _extract_file(entry, num):
        data = {
            "media_id"  : str(entry.get("pk") or entry.get("id") or ""),
            "media_type": entry.get("media_type"),
            "num"       : num,
        }

        if versions := entry.get("video_versions"):
            best = max(
                versions,
                key=lambda v: ((v.get("width") or 0) * (v.get("height") or 0),
                               len(v.get("url") or "")),
            )
            data.update({
                "url"      : best["url"],
                "width"    : best.get("width") or entry.get("original_width"),
                "height"   : best.get("height") or entry.get("original_height"),
                "duration" : entry.get("video_duration"),
                "has_audio": entry.get("has_audio"),
                "type"     : "video",
            })
        else:
            candidates = (entry.get("image_versions2") or {}).get("candidates") or ()
            if not candidates:
                return None

            best = max(
                candidates,
                key=lambda c: ((c.get("width") or 0) * (c.get("height") or 0),
                               len(c.get("url") or "")),
            )
            data.update({
                "url"   : best["url"],
                "width" : best.get("width") or entry.get("original_width"),
                "height": best.get("height") or entry.get("original_height"),
                "type"  : "image",
            })

        text.nameext_from_url(data["url"], data)
        if not data["extension"]:
            data["extension"] = "mp4" if data["type"] == "video" else "jpg"
        return data

    @staticmethod
    def _post_text(post):
        if text_ := (post.get("caption") or {}).get("text"):
            return text_

        fragments = (
            (post.get("text_post_app_info") or {})
            .get("text_fragments", {})
            .get("fragments") or ()
        )
        return "".join(fragment.get("plaintext") or "" for fragment in fragments)

    @staticmethod
    def _extract_lsd(page):
        token = text.extr(page, '"LSD",[],{"token":"', '"')
        return token or text.extr(page, '"token":"', '"')

    def _has_auth_cookies(self):
        return (
            self.cookies_check(self.cookies_names, ".threads.net", True) or
            self.cookies_check(self.cookies_names, ".threads.com", True) or
            self.cookies_check(self.cookies_names, ".instagram.com", True)
        )


class ThreadsShareExtractor(Extractor):
    """Extractor for Threads share links"""
    category = "threads"
    subcategory = "share"
    root = "https://www.threads.net"
    pattern = BASE_PATTERN + r"/share/([A-Za-z0-9_-]+)/?(?:[?#].*)?$"
    example = "https://www.threads.com/share/BACpWLLKkO"

    def items(self):
        url = text.ensure_http_scheme(self.url)
        # Browser UA returns SPA HTML without redirect; crawler UA gets 302.
        location = self.request_location(
            url,
            headers={"User-Agent": "facebookexternalhit/1.1"},
            notfound="URL",
        )
        if not location:
            raise exception.AbortExtraction("Unable to resolve share URL")
        yield Message.Queue, location, {"_extractor": ThreadsPostExtractor}
