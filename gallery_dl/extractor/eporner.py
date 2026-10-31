# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.eporner.com/"""

from .common import Extractor, GalleryExtractor, Message
from .. import text


class EpornerVideoExtractor(Extractor):
    """Extractor for videos from eporner.com"""
    category = "eporner"
    subcategory = "video"
    root = "https://www.eporner.com"
    filename_fmt = "{id}.{extension}"
    pattern = (r"(?:https?://)?(?:[\w-]+\.)?eporner\.com"
               r"/(video-|embed/|hd-porn/)(\w+)(?:/([\w-]+))?")
    example = "https://pl.eporner.com/video-VIDEOID/SLUG/"

    def items(self):
        # yt-dlp's Eporner extractor only matches 'eporner.com' and
        # 'www.eporner.com', so normalize locale subdomains like 'pl.'
        kind, video_id, slug = self.groups
        url = f"{self.root}/{kind}{video_id}/"
        if slug:
            url += slug + "/"

        data = {
            "id"       : video_id,
            "extension": "mp4",
        }
        yield Message.Directory, "", data
        yield Message.Url, "ytdl:" + url, data


class EpornerGalleryExtractor(GalleryExtractor):
    """Extractor for image galleries from eporner.com"""
    category = "eporner"
    root = "https://www.eporner.com"
    pattern = (r"(?:https?://)?(?:www\.)?eporner\.com"
               r"/gallery/(\w+)(?:/([\w-]+))?")
    example = "https://www.eporner.com/gallery/GID/SLUG/"

    def __init__(self, match):
        url = f"{self.root}/gallery/{match[1]}/{match[2]}/"
        GalleryExtractor.__init__(self, match, url)

    def metadata(self, page):
        if page.find("Age Verification<", 0, 240) >= 0:
            raise self.exc.AuthRequired("Age Verification", "gallery")
        title = text.extr(page, "<title>", " - EPORNER</title>")
        if title.endswith(" Photo Gallery"):
            title = title[:-14]

        return {
            "gallery_id": self.groups[0],
            "title"     : text.unescape(title),
            "slug"      : text.extr(
                page, "/gallery/", '/"').rpartition("/")[2],
            "description": text.unescape(text.extr(
                page, 'name="description" content="', '"')),
            "tags": text.extr(
                page, 'EP.ads.keywords = "', '"').split(","),
        }

    def images(self, page):
        album = text.extr(
            page, 'class="photosgrid gallerygrid"', "id='gallerySlideBox'")

        results = []
        for url in text.extract_iter(album, ' src="', '"'):
            url, _, ext = url.rpartition(".")
            # Preview images have a resolution suffix.
            # E.g. "11208293-image-3_296x1000.jpg".
            # The same name, but without the suffix, leads to the full image.
            url = url[:url.rfind("_")]
            name = url[url.rfind("/")+1:]
            results.append((f"{url}.{ext}", {"id": name[:name.find("-")]}))
        return results
