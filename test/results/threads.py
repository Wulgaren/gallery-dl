# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import threads


__tests__ = (
{
    "#url"     : "https://www.threads.com/@threads/post/C30eveaOmoJ",
    "#category": ("", "threads", "post"),
    "#class"   : threads.ThreadsPostExtractor,
},

{
    "#url"     : "https://www.threads.com/t/C30eveaOmoJ",
    "#category": ("", "threads", "post"),
    "#class"   : threads.ThreadsPostExtractor,
},

{
    "#url"     : "https://www.threads.com/share/BACpWLLKkO",
    "#category": ("", "threads", "share"),
    "#class"   : threads.ThreadsShareExtractor,
},

)
