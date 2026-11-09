# manuals — Survival manuals

ATP 3-50.21, field first aid, FEMA *Are You Ready?*

- **Hosting:** ours. ~95 MB budgeted.
- **Format:** `hfdb`, built from public-domain PDFs.
- **Cadence:** monthly.
- **`staleAfterDays`:** 30.

## Build

```bash
python scripts/build_pdf_pack.py --pack manuals --out dist/manuals.hfdb --query "shelter"
```

## Sources

See `sources.json`. Every entry is `"verified": false` until someone has opened
it; the builder will not run until they are.

Two practical warnings:

- **Army publication URLs move.** `armypubs.army.mil` reorganises, and some
  federal hosts reject `HEAD` or a non-browser `User-Agent`. An unreachable URL
  here is a routine finding, not a crisis: `validate_manifest.py --network`
  reports it and the pack keeps serving its last good build until someone
  re-points it.
- **Some Army PDFs are scans.** Per-page text extraction gets nothing from an
  image-only page. `build_pdf_pack.py` counts pages with no extractable text and
  fails the whole build if nothing extracted at all. It deliberately does no
  OCR: OCR errors in a survival manual are worse than a missing page.

## Open question

The spec says "original PDF kept for page view" so the app can show the page a
citation points at. That is a second file per pack, and a manifest entry has one
`url` — the same shape of problem as `medical`. Either the PDFs ride inside the
hfdb as blobs (simple, and it roughly doubles the pack), or packs grow a
`components` list, or page view falls back to showing the extracted text. Not
decided.
