# water-food — Water & Food

Purification, home canning, food storage, foraging basics.

- **Hosting:** ours. ~160 MB budgeted.
- **Format:** `hfdb`, built from public-domain PDFs.
- **Cadence:** monthly.
- **`staleAfterDays`:** 30.

## Build

```bash
python scripts/build_pdf_pack.py --pack water-food --out dist/water-food.hfdb --query "boil"
```

The builder downloads each PDF in `sources.json` conditionally (an unchanged
file is never re-fetched), extracts text page by page, and writes one searchable
document per page with `location` set to `"p. N"`, so a hit can cite a page
number the way the spec requires.

## Sources

Every entry in `sources.json` carries `"verified": false` until a human has
opened the URL and confirmed it is the right document from the right publisher.
`build_pdf_pack.py` refuses to build while any entry is unverified. That is the
gate on purpose: these are documents people act on in an emergency, and a URL
that looks plausible is not the same as the right file.

All of it is US Government work and therefore public domain — hostable and
modifiable, credited anyway.

## Note

Much of this material is tabular (USDA canning process times by jar size and
altitude). Per-page extraction flattens tables into prose: searchable, but close
to unreadable. If the canning tables matter in the UI they want hand-transcribing
into quick cards or markdown rather than extracting.
