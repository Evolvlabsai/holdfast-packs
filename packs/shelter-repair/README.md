# shelter-repair — Shelter & Repair

Repair guides, DIY, knots, basic electrical.

- **Hosting:** **linked** — straight from Kiwix. We host nothing and pay nothing.
- **Format:** `zim`, read on the phone with libzim.
- **Cadence:** when Kiwix publishes.
- **`staleAfterDays`:** 180.

## Chosen file

`https://download.kiwix.org/zim/ifixit/ifixit_en_all_2025-12.zim`

- 3,570,695,757 bytes
- sha256 `9bb5f3408707fd0300c6ef47a425c3217187f144cd9154a928183816aa72eead`,
  read from the publisher's own `.zim.sha256` sidecar
- Last-Modified 2025-12-23; both verified live on 2026-11-09
- CC BY-NC-SA 3.0

English iFixit has not been rebuilt since 2025-12, although other languages have
2026-03 builds. `check_upstream.py` watches the Kiwix OPDS catalog for the book
name `ifixit_en_all` and will report the next edition.

Kiwix publishes `.zim.sha256`, `.zim.md5` and `.zim.meta4` siblings for these
files even though the HTML directory listing hides them, which is how
`update_manifest.py --from-url` gets a real checksum without downloading 3.3 GiB.

## Licence watch

iFixit is **non-commercial** (CC BY-NC-SA). Fine for a free app, per the spec. It
stops being fine the moment anything is sold or bundled into a paid product —
including, arguably, a paid Family sync plan if this pack is part of what that
plan delivers. Worth a second look before any paid tier ships.

## OPEN QUESTION — the spec wants two archives in one pack

The spec describes this pack as "iFixit **and Stack Exchange** ZIMs via Kiwix",
1.2 GB. One manifest entry has one `url`, so only one archive can ship under
this id. Verified candidates for a second (2026-11-09):

| Site | File | Bytes |
| --- | --- | --- |
| DIY | `diy.stackexchange.com_en_all_2026-10.zim` | 2,086,024,326 |
| Outdoors | `outdoors.stackexchange.com_en_all_2026-10.zim` | 141,820,374 |
| Woodworking | `woodworking.stackexchange.com_en_all_2026-10.zim` | 106,657,287 |
| Electronics | `electronics.stackexchange.com_en_all_2026-10.zim` | 4,261,397,539 |

There is **no survival or bushcraft Stack Exchange ZIM** — those sites do not
exist on Stack Exchange. Outdoors is the closest to the use case and is tiny.

Suggestion: `shelter-repair` stays iFixit, and a second id (`shelter-repair-qa`)
carries Outdoors + Woodworking, together about 250 MB. That needs the same
multi-file-per-pack decision as `medical`.

Also note the spec's 1.2 GB estimate is well **under** the real iFixit file alone
(3.3 GiB). The Packs screen's size needs correcting.
