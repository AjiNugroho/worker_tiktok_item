# TikTok Video-Detail Extraction Map

Reference for parsing the `__UNIVERSAL_DATA_FOR_REHYDRATION__` blob from a TikTok
web video page. Only fields with analytical value are listed. Everything not
listed here (AB tests, i18n strings, player/bitrate configs, cookie banners,
region lists, download links) is noise — discard it.

Root path for all useful data:
`__DEFAULT_SCOPE__["webapp.video-detail"].itemInfo.itemStruct`
(aliased below as `item`). One extra useful field lives under
`__DEFAULT_SCOPE__["seo.abtest"]`.

---

## 1. Post core

| Field | Path | Example | Notes |
|---|---|---|---|
| video_id | `item.id` | `7615904735782079765` | Primary key. Also in `item.video.id`. |
| description | `item.desc` | `#7suratpilihan` | Raw caption incl. hashtags. |
| created_at | `item.createTime` | `1773230402` | Unix seconds → 2026-03. |
| duration_s | `item.video.duration` | `23` | Seconds. |
| canonical_url | `seo.abtest.canonical` | `https://www.tiktok.com/@semestasikecil/video/7615904735782079765` | Cleanest permalink. |
| location_created | `item.locationCreated` | `ID` | Country of posting. |
| category_type | `item.CategoryType` | `120` | TikTok internal category id. |
| diversification_id | `item.diversificationId` | `10083` | Content-cluster id. |
| is_ad | `item.isAd` | `true` | Promoted post flag. |
| is_ecom_video | `item.isECVideo` | `1` | Has shopping/product anchor. |
| is_aigc | `item.IsAigc` | `false` | AI-generated flag. |

## 2. Engagement stats

Prefer `statsV2` (strings, more current) over `stats` (ints). Same keys.

| Field | Path | Example |
|---|---|---|
| plays | `item.statsV2.playCount` | `6900000` |
| likes | `item.statsV2.diggCount` | `128700` |
| comments | `item.statsV2.commentCount` | `1022` |
| shares | `item.statsV2.shareCount` | `9581` |
| saves | `item.statsV2.collectCount` | `27360` |
| reposts | `item.statsV2.repostCount` | `0` |

Derived metrics worth computing: engagement_rate = (likes+comments+shares+saves)/plays;
save_rate = saves/plays (strong commercial-intent signal for ecom).

## 3. Author

| Field | Path | Example |
|---|---|---|
| author_id | `item.author.id` | `7477416713480045586` |
| handle | `item.author.uniqueId` | `semestasikecil` |
| display_name | `item.author.nickname` | `Semesta Si Kecil` |
| sec_uid | `item.author.secUid` | `MS4wLjAB...` | Needed for profile API calls. |
| bio | `item.author.signature` | `Tempat kecil untuk jiwa...` |
| verified | `item.author.verified` | `false` |
| is_seller | `item.author.ttSeller` | `false` | TikTok Shop seller flag. |
| private | `item.author.privateAccount` | `false` |
| acct_created | `item.author.createTime` | `1740971910` |

### Author stats — use `authorStatsV2` (strings)

| Field | Path | Example |
|---|---|---|
| followers | `item.authorStatsV2.followerCount` | `74800` |
| following | `item.authorStatsV2.followingCount` | `27` |
| total_likes | `item.authorStatsV2.heartCount` | `3300000` |
| video_count | `item.authorStatsV2.videoCount` | `1261` |

## 4. Music / sound

| Field | Path | Example |
|---|---|---|
| music_id | `item.music.id` | `6917617064693828353` |
| title | `item.music.title` | `original sound - feryisraoktaviansyah` |
| author_name | `item.music.authorName` | `ferryisraa` |
| is_original | `item.music.original` | `true` |
| duration_s | `item.music.duration` | `35` |
| is_commerce_music | `item.music.is_commerce_music` | `true` |

## 5. Hashtags / text-extra

Two equivalent sources: `item.challenges[]` and `item.textExtra[]`.

| Field | Path | Example |
|---|---|---|
| hashtag_id | `item.challenges[].id` | `7419280723712049158` |
| hashtag_name | `item.challenges[].title` | `7suratpilihan` |

## 6. Search/SEO signals (useful for keyword intel)

| Field | Path | Notes |
|---|---|---|
| suggested_words | `item.suggestedWords[]` | TikTok's own related-search terms for this post. High value for keyword mining. e.g. `["surat alwaqiah","Al Waqiah","AL MULK",...]` |

## 7. Product anchor (TikTok Shop) — THE ecom payload

Located at `item.anchors[]` where `type == 35`. The product detail is a
**doubly-escaped JSON string** inside `anchors[].extra`. Parse `anchors[].extra`
as JSON, take element `[0]`, then JSON-parse its `.extra` string again to reach
the product object. Fields below are within that inner product object.

| Field | Inner path | Example |
|---|---|---|
| product_id | `product_id` | `1733045696479134905` |
| title | `title` | `Spesial Keutamaan 7 Surah A6 ...` |
| short_title | `elastic_title` | `cuma 16ribuan (PROMO)` |
| price | `price` | `0` (often 0 in anchor; real price needs PDP) |
| currency | `currency` | `IDR` |
| seller_id | `seller_id` | `7496159609552406713` |
| product_status | `product_status` | `90` |
| categories | `categories[]` | `Buku > Kemanusiaan & Ilmu Sosial > Agama & Filsafat` |
| sku_ids | `skus[].sku_id` | `1733045708739740857` |
| cover_image | `cover_url` | full CDN jpeg URL |
| seo_url | `seo_url` | `https://shop-id.tokopedia.com/pdp/1733045696479134905` |
| platform | `platform` | `5` |

Note: the embedded `detail_url`/`schema` carry tracking signatures; the clean
`seo_url` is the one to store.

---

## Minimal extracted record (target schema)

```json
{
  "video_id": "7615904735782079765",
  "url": "https://www.tiktok.com/@semestasikecil/video/7615904735782079765",
  "description": "#7suratpilihan",
  "created_at": 1773230402,
  "duration_s": 23,
  "location": "ID",
  "is_ad": true,
  "is_ecom": true,
  "stats": {
    "plays": 6900000,
    "likes": 128700,
    "comments": 1022,
    "shares": 9581,
    "saves": 27360,
    "reposts": 0
  },
  "hashtags": ["7suratpilihan"],
  "suggested_words": ["surat alwaqiah","al waqiah pembuka rezeki","Al Waqiah","AL MULK","surat al mulk","surat yasin"],
  "music": {
    "id": "6917617064693828353",
    "title": "original sound - feryisraoktaviansyah",
    "author": "ferryisraa",
    "original": true
  },
  "author": {
    "id": "7477416713480045586",
    "handle": "semestasikecil",
    "name": "Semesta Si Kecil",
    "sec_uid": "MS4wLjABAAAABXDnJwbFm7JMOR_bZ7M6iwS3eN2KVACkjVJN0IGP_WKUyk0MXaBNuTUx6L0BbqGC",
    "followers": 74800,
    "total_likes": 3300000,
    "video_count": 1261,
    "verified": false,
    "is_seller": false
  },
  "product": {
    "product_id": "1733045696479134905",
    "title": "Spesial Keutamaan 7 Surah A6 (10*14 cm) ...",
    "short_title": "cuma 16ribuan (PROMO)",
    "seller_id": "7496159609552406713",
    "currency": "IDR",
    "category_path": ["Buku, Majalah, & Audio","Kemanusiaan & Ilmu Sosial","Agama & Filsafat"],
    "seo_url": "https://shop-id.tokopedia.com/pdp/1733045696479134905"
  }
}
```

## Parsing gotchas

- **`statsV2` vs `stats`:** use V2 (string values, more accurate). Cast to int yourself.
- **Product anchor is double-escaped JSON** inside `anchors[].extra` → `[0].extra`. Two `JSON.parse` passes.
- **Price is usually `0` in the anchor.** To get the real price you must hit the PDP (`seo_url` / `product_id`).
- **Image/video CDN URLs are signed** with `x-expires` + `x-signature` and expire in ~days. Don't store as permanent references; re-fetch or store the underlying `uri`/`id`.
- **`playAddr`/`downloadAddr` are blank** in this SSR payload — video binary needs a separate call.
- **Timestamps are Unix seconds**, not ms.
- The whole payload is a single JSON object; `\u002F` sequences are just escaped `/`.