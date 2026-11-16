# core — Core (required)

Quick cards, prep checklists, library documents and the per-state map overlays.
The one pack the app installs on first run and will not let the user remove.

- **Hosting:** ours (GitHub Releases). ~80 MB budgeted in the spec.
- **Format:** `hfdb` (SQLite + FTS5).
- **Cadence:** weekly, driven by the overlays rather than the text.
- **`staleAfterDays`:** 7.

## Build

The release build uses the app's PackTool, which also writes the embeddings
the offline AI searches. `check_content.py` turns the card files into the JSON
it reads (reviewed cards only):

```bash
python scripts/check_content.py --cards-json dist/cards.json
dotnet run --project ../holdfast-app/tools/Holdfast.PackTool -c Release -- build-hfdb \
  --id core --name Core --version 2026.11.16 --region US-MD \
  --cards dist/cards.json --docs packs/core/sources/docs \
  --embed-model <minilm-l6-v2.onnx> --embed-vocab <minilm-vocab.txt> --out dist/core.hfdb
```

`build_core.py` builds the same cards and documents without embeddings (CI
smoke builds and local checks):

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
sources/cards/<id>.md                quick cards, one file each (CONTRIBUTING.md)
sources/skills/<id>/                 survival skills: skill.md and its drawings
sources/docs/*.md                    library documents
sources/overlays/us-md-*.geojson     map overlays for one region
```

A document's first `# ` heading is its title, a `Source:` line becomes the
citation, the file name stem is its `doc_id`, and the path relative to `docs/`
is the `location` a search hit cites. Overlay features must carry
`properties.kind` in {`rally`, `water`, `medical`, `shelter`, `fuel`} and
`properties.name`; the writer rejects the pack otherwise.

## Review status

- **Quick cards: reviewed.** The first six cards passed medical review on
  2026-11-11 and ten more (choking to lost outdoors) on 2026-11-16, all
  `"draft": false`. `build_core.py` still refuses a card marked
  `"draft": true` without `--allow-draft`, and `update.yml` never passes that
  flag, so a new or edited card must be reviewed again before it can ship.
- **No card gives a medicine dose,** and none should.
- **Survival skills** (app 0.5.3 and later) live in `sources/skills/<id>/`
  with their line drawings and ship in Core's optional `skills` table. Older
  apps ignore the table. `test_every_skill_on_main_has_passed_review` is their
  merge gate, the same as for cards.
- **New and changed cards arrive as pull requests** with `status: draft`
  (see `CONTRIBUTING.md`). The test
  `test_every_card_on_main_has_passed_medical_review` keeps them red until a
  maintainer sets `status: reviewed` and the review date, so no draft reaches
  main. Home shows the first six cards by `order`; app 0.5.2 build 30 and
  later link to the full list.
- **No map overlays ship.** The invented `SAMPLE — ` points near Annapolis
  and Baltimore were removed on 2026-11-11 (Core 2026.11.12). Overlays come
  back only from a real per-state source (see the open question below).
- **The documents are abridged** summaries of federal guidance.

## Open question

Real overlays need a per-state source for shelters, hospitals, fuel and water
points, and a refresh cadence. The spec lists this as an open question and it is
still open: Maryland publishes emergency data through MEMA and MD iMAP, but
whether any of it is a stable, machine-readable feed we can poll weekly has not
been checked.
