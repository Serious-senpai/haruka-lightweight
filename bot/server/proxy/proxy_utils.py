from __future__ import annotations

from typing import Mapping

from multidict import CIMultiDictProxy


def forward_client_headers(source: CIMultiDictProxy[str]) -> Mapping[str, str]:
    headers = {}
    excluded_headers = set(s.casefold() for s in ["host"])
    for key, value in source.items():
        if key.casefold() not in excluded_headers:
            headers[key] = value

    return headers
