import json
from typing import Any


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_product_anchor(anchors: list) -> dict | None:
    for anchor in anchors:
        if anchor.get("type") != 35:
            continue
        try:
            outer = json.loads(anchor["extra"])
            inner_raw = outer[0]["extra"]
            product = json.loads(inner_raw)

            categories = product.get("categories", [])
            if isinstance(categories, list):
                category_path = [c.get("title") or c.get("name") for c in categories if isinstance(c, dict)]
            elif isinstance(categories, str):
                category_path = [s.strip() for s in categories.split(">")]
            else:
                category_path = []

            return {
                "product_id": product.get("product_id"),
                "title": product.get("title"),
                "short_title": product.get("elastic_title"),
                "seller_id": product.get("seller_id"),
                "currency": product.get("currency"),
                "category_path": category_path,
                "seo_url": product.get("seo_url"),
            }
        except (KeyError, IndexError, json.JSONDecodeError, TypeError):
            continue
    return None


def extract_video(raw: dict) -> dict:
    scope = raw.get("__DEFAULT_SCOPE__", {})
    item = scope.get("webapp.video-detail", {}).get("itemInfo", {}).get("itemStruct", {})
    seo = scope.get("seo.abtest", {})

    stats_v2 = item.get("statsV2") or item.get("stats", {})

    author = item.get("author", {})
    author_stats = item.get("authorStatsV2") or item.get("authorStats", {})

    music = item.get("music", {})

    hashtags = [c["title"] for c in item.get("challenges", []) if c.get("title")]

    product = _parse_product_anchor(item.get("anchors", []))

    return {
        "video_id": item.get("id"),
        "url": seo.get("canonical"),
        "description": item.get("desc"),
        "created_at": item.get("createTime"),
        "duration_s": item.get("video", {}).get("duration"),
        "location": item.get("locationCreated"),
        "is_ad": item.get("isAd", False),
        "is_ecom": bool(item.get("isECVideo", 0)),
        "stats": {
            "plays":    _int(stats_v2.get("playCount")),
            "likes":    _int(stats_v2.get("diggCount")),
            "comments": _int(stats_v2.get("commentCount")),
            "shares":   _int(stats_v2.get("shareCount")),
            "saves":    _int(stats_v2.get("collectCount")),
            "reposts":  _int(stats_v2.get("repostCount")),
        },
        "hashtags": hashtags,
        "suggested_words": item.get("suggestedWords", []),
        "music": {
            "id":       music.get("id"),
            "title":    music.get("title"),
            "author":   music.get("authorName"),
            "original": music.get("original", False),
        },
        "author": {
            "id":          author.get("id"),
            "handle":      author.get("uniqueId"),
            "name":        author.get("nickname"),
            "sec_uid":     author.get("secUid"),
            "bio":         author.get("signature"),
            "verified":    author.get("verified", False),
            "is_seller":   author.get("ttSeller", False),
            "private":     author.get("privateAccount", False),
            "followers":   _int(author_stats.get("followerCount")),
            "following":   _int(author_stats.get("followingCount")),
            "total_likes": _int(author_stats.get("heartCount")),
            "video_count": _int(author_stats.get("videoCount")),
        },
        "product": product,
    }
