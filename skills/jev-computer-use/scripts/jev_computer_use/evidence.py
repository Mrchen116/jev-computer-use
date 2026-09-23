"""Bounded excerpts from original observations; no model or desktop access."""

import re


def read_sources(archive, source_ids, query="", offset=0, max_chars=6000):
    if not 1 <= len(source_ids) <= 12:
        raise ValueError("Choose between 1 and 12 source IDs")
    if offset < 0 or not 500 <= max_chars <= 12000:
        raise ValueError("Use a nonnegative offset and max_chars between 500 and 12000")
    limit = min(max_chars, 12000 // len(source_ids))
    results = []
    for source_id in source_ids:
        source = archive[source_id]
        text = source["text"]
        start = min(offset, len(text))
        matches = (
            [m.start() for m in re.finditer(re.escape(query), text, re.I)]
            if query
            else []
        )
        next_match = next((pos for pos in matches if pos >= offset), None)
        found = not query or next_match is not None
        if query and found:
            start = max(0, next_match - min(600, limit // 4))
        end = min(len(text), start + limit) if found else start
        results.append(
            {
                **{k: source[k] for k in ("source_id", "url", "title")},
                "text": text[start:end],
                "start": start,
                "end": end,
                "total_chars": len(text),
                "truncated": start != 0 or end != len(text),
                "query_found": found if query else None,
                "match_offsets": matches[:30],
                "match_count": len(matches),
            }
        )
    return results
