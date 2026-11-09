# medical — Medical

First-aid cards, *Where There Is No Doctor*, and WikiMed.

- **Hosting:** mixed, which is the problem below. ~420 MB budgeted.
- **Cadence:** monthly.
- **`staleAfterDays`:** 30.

## Not built

The hosted half (first-aid cards and public-domain first-aid text) builds with
`scripts/build_core.py` once a `sources/` directory exists here. The manifest
entry is a placeholder until it does.

## Hesperian: linked, never hosted

*Where There Is No Doctor* is free to read but copyrighted. The spec is explicit:
confirm redistribution terms before hosting, and until then link to Hesperian's
own download instead. **Nobody has confirmed anything.** So this pack must not
carry the text, and the Packs screen should send the user to
<https://hesperian.org/books-and-resources/>.

## WikiMed — chosen file

Verified live on 2026-11-09 against `download.kiwix.org`:

| Edition | File | Bytes |
| --- | --- | --- |
| **mini (chosen)** | `wikipedia_en_medicine_mini_2026-10.zim` | 174,350,854 |
| nopic | `wikipedia_en_medicine_nopic_2026-10.zim` | 1,047,708,415 |
| maxi | `wikipedia_en_medicine_maxi_2026-10.zim` | 1,864,210,320 |

`mini` is lead sections only, about 166 MiB, which fits the spec's 420 MB budget
alongside the hosted half. `nopic` is where to go if lead sections prove too thin
in use; it alone blows the budget.

sha256 of the mini file, read from the publisher's own `.zim.sha256` sidecar:
`c66f27274775870cec7e0c230c7e7626d367633b1f26c4a74499c249ddac0822`

## OPEN QUESTION — "Hosted + Linked" does not fit one manifest entry

The spec's pack table calls this pack *Hosted + Linked*. A manifest entry has
exactly one `url` and one `format`, so one entry cannot be both an `hfdb` we
host and a `zim` from Kiwix. Three ways out:

1. **Two pack ids** — `medical` (hosted hfdb) and `medical-wikimed` (linked
   zim), shown together on the Packs screen. Honest, cheap, costs one more row
   and a hint that they belong together.
2. **Hosted only** — extract what we need from WikiMed into our own hfdb.
   Re-hosting CC BY-SA content is allowed with attribution, but it is ~1 GB of
   our release storage and a monthly rebuild.
3. **A `components` array on a pack entry** — several files per pack. The
   cleanest model and the largest app change: it touches the downloader, the
   checksum check, the atomic swap and the storage accounting.

Option 1 is the cheapest thing that is true. **Not decided.** Until it is, the
WikiMed facts sit in `pack.meta.json` under `companions` and nothing links to
them.
