# wikipedia-top50k — Wikipedia: most read

The most-read English articles, text and images.

- **Hosting:** **linked** — straight from Kiwix.
- **Format:** `zim`.
- **Cadence:** when Kiwix publishes.
- **`staleAfterDays`:** 180.
- **Licence:** CC BY-SA 4.0, Wikipedia contributors, packaged by Kiwix.

## Chosen file

`https://download.kiwix.org/zim/wikipedia/wikipedia_en_top_maxi_2026-09.zim`

- 6,991,081,681 bytes (6.5 GiB)
- sha256 `7c08d2a7557ef7e3da751bb429d081e1c7c8971e50fee4fef097021a03ea6b0a`,
  from the publisher's `.zim.sha256` sidecar
- Last-Modified 2026-09-18; both verified live on 2026-11-09

Kiwix calls this selection `top`, not `top 50k`; the pack id keeps the spec's
name. Same selection, other editions:

| Edition | Bytes | What it is |
| --- | --- | --- |
| `wikipedia_en_top_maxi_2026-09.zim` | 6,991,081,681 | full articles with images — **chosen** |
| `wikipedia_en_top_nopic_2026-09.zim` | 2,745,850,723 | full articles, no images |
| `wikipedia_en_top_mini_2026-09.zim` | 296,858,160 | lead sections only |

There is also a separate, much larger `wikipedia_en_top1m_*` family. Not
considered for launch.

## Two things to fix

1. **The size estimate is wrong.** The spec budgets 5.2 GB; the real `maxi` file
   is 6.5 GiB, and the previous (2026-06) edition was 7.8 GiB. The Packs screen
   and the storage budget need the real number, and it moves between editions by
   more than a gigabyte — which is why `pack.meta.json` sets a 35% drift
   threshold for this pack rather than the default 25%.
2. **It is over 2 GB and we do not host it.** The manifest's `parts` splitting
   only works for files we produce; Kiwix serves one 6.5 GiB file. So the app has
   to manage a single >2 GB download with resume, on a phone, onto a filesystem
   that may not accept a file that size. Confirm that on real hardware before
   this pack ships, or ship `nopic` (2.7 GiB) first and treat `maxi` as the
   upgrade.
