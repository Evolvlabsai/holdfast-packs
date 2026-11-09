# core — Core (required)

Quick cards, prep checklists, library documents and the per-state map overlays.
The one pack the app installs on first run and will not let the user remove.

- **Hosting:** ours (GitHub Releases). ~80 MB budgeted in the spec.
- **Format:** `hfdb` (SQLite + FTS5).
- **Cadence:** weekly, driven by the overlays rather than the text.
- **`staleAfterDays`:** 7.

## Build

```bash
python scripts/build_core.py \
  --sources packs/core/sources \
  --id core --name Core --region US-MD \
  --out dist/core.hfdb --query "boil water"
```

`--query` is a smoke test: it searches the pack it just built through the app's
own FTS5 query path and fails the build if nothing comes back.

## Sources

```
sources/cards.json                   quick cards, in Home-grid order
sources/docs/*.md                    library documents
sources/overlays/us-md-*.geojson     map overlays for one region
```

A document's first `# ` heading is its title, a `Source:` line becomes the
citation, the file name stem is its `doc_id`, and the path relative to `docs/`
is the `location` a search hit cites. Overlay features must carry
`properties.kind` in {`rally`, `water`, `medical`, `shelter`, `fuel`} and
`properties.name`; the writer rejects the pack otherwise.

## DRAFT — nothing here has been reviewed

This content came across from the app repo's development samples
(`holdfast-app/samples/core-sample`). It is a stand-in so the pipeline has
something real to build, and **none of it may ship**:

- **Every quick card is `"draft": true`.** `build_core.py` refuses to build
  without `--allow-draft`, and `update.yml` never passes that flag, so an
  unreviewed card cannot reach a release. The spec wants each card to cite its
  source and be reviewed before release, the medical ones ideally by a licensed
  EMT or nurse. That has not happened. Bleeding and CPR need a clinician.
- **The figures were transcribed by hand** from named public sources (Stop the
  Bleed / ATP 3-50.21, AHA hands-only CPR, American Red Cross, CDC, EPA, USDA
  FSIS, FEMA / Ready.gov) and need checking against the current editions. Bleach
  concentrations and boil times change between editions.
- **No card gives a medicine dose,** and none should.
- **The overlay points are invented.** Every name starts with `SAMPLE — ` and
  every feature carries a `note` saying so. They sit near Annapolis and
  Baltimore and correspond to nothing real.
- **The documents are abridged** summaries of federal guidance.

## Open question

Real overlays need a per-state source for shelters, hospitals, fuel and water
points, and a refresh cadence. The spec lists this as an open question and it is
still open: Maryland publishes emergency data through MEMA and MD iMAP, but
whether any of it is a stable, machine-readable feed we can poll weekly has not
been checked.
