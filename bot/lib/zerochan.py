import asyncio
import contextlib
import re
from typing import List, Set

import aiohttp
import yarl
from bs4 import BeautifulSoup


image_url_matcher = re.compile(r"^https://s3\.zerochan\.net/.*?\.(?:jpg|png)$")


async def search(query: str, *, max_results: int = 200, session: aiohttp.ClientSession) -> List[str]:
    """This function is a coroutine

    Search zerochan.net for a list of image URLs.

    Parameters
    -----
    query: ``str``
        The searching query
    max_results: ``int``
        The maximum number of results to return

    Returns
    List[``str``]
        A list of image URLs
    """
    url = yarl.URL.build(scheme="https", host="zerochan.net", path=f"/{query}")
    results: List[str] = []
    results_set: Set[str] = set()
    page = 0

    with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
        while True:
            page += 1
            ext: List[str] = []

            async with session.get(url.with_query(p=page)) as response:
                if response.ok:
                    html = await response.text(encoding="utf-8")
                    soup = BeautifulSoup(html, "html.parser")
                    for img in soup.find_all("img"):
                        image_url: str = img.get("src")
                        if image_url_matcher.fullmatch(image_url) is not None:
                            ext.append(image_url)

            if ext:
                for image in ext:
                    if image not in results_set:
                        results_set.add(image)
                        results.append(image)

                if len(results) >= max_results:
                    return results[:max_results]
            else:
                break

    return results
