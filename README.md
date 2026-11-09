# holdfast-packs

Public content repository for **Holdfast**, an offline survival and
emergency-prep app. It holds the signed pack catalog the app reads, the build
scripts for the packs we produce, and the pipeline that keeps them current.

The app itself lives in the private `holdfast-app` repository. It knows exactly
two things about content: the catalog URL and one Ed25519 public key. Everything
else — what packs exist, where they are hosted, how big they are — is decided
here, so moving a pack never needs an app release.

> Licensing: code is MIT; our own writing (quick cards, documents, overlays) is
> CC BY-NC 4.0. Third-party packs keep their own licences. See [`LICENSE`](LICENSE).

Large third-party content (Wikipedia, OpenStreetMap, AI models) is not stored
here. The manifest points the app straight at its upstream host.

---

## Layout

```
manifest.json                 the signed catalog: the app installs nothing not listed here
manifest.json.sig             detached Ed25519 signature — NOT committed; CI makes it
schema/manifest.schema.json   JSON Schema for the catalog, matching the app's parser
packs/<id>/README.md          what the pack is, where it comes from, what is unresolved
packs/<id>/pack.meta.json     pipeline metadata: hosting, upstream to watch, size threshold
packs/<id>/sources.json       for PDF packs: the documents, with verification status
packs/<id>/sources/           for hand-written packs: cards, docs, overlays
packs/maps-roads-us-md/regions/*.json   one file per state: bbox, maxzoom, licence
scripts/                      the pipeline (Python 3.12, stdlib + 4 pinned packages)
tests/                        pytest
site/index.html               the Pages landing page
.github/workflows/            update (weekly), validate (on PR), publish (on main)
```

Nothing built is committed. Pack files live on GitHub Releases and the manifest
points at them.

## The trust model

This is the part worth reading twice.

1. **The catalog is the only source of truth.** The app installs nothing that
   `manifest.json` does not list.
2. **Only a signed catalog is trusted.** The app verifies a detached Ed25519
   signature over the manifest's *exact bytes* against a public key compiled
   into the app. A bad or missing signature means the catalog is ignored and the
   last good one is kept — the app does not fall back to "unsigned but
   probably fine".
3. **Only a checksum-verified file is installed.** Every entry carries `size`
   and `sha256`. A download that does not match is discarded, whichever mirror
   served it, and the pack already on the phone is left untouched.
4. **The signing key lives in one place.** The `HOLDFAST_SIGNING_KEY` secret of
   this repository. It is read by exactly one workflow, `publish.yml`, which
   runs only on `main`. The weekly update job never signs: it opens a pull
   request, and a human merging it is what causes a signature to exist.
5. **Placeholders are safe to publish.** Nine of the eleven launch entries are
   not built yet. Their entries carry `https://example.invalid/PLACEHOLDER/…` and a
   `sha256` of 64 zeros, so the Packs screen can list them while every download
   from them fails verification. `validate_manifest.py` names each one on every
   run, so they can never go quiet.

Because the signature covers exact bytes, **reformatting `manifest.json`
invalidates it**. `update_manifest.py` deletes the stale `.sig` whenever it
edits, `validate.yml` fails a PR that introduces CRLF or a BOM, and the manifest
is always written the same way: two-space indent, UTF-8, LF, one trailing
newline.

## Packs

Eleven catalog entries cover launch: the ten packs of the spec, with the
offline AI split into two packs (the answer model and the source matcher),
which the app shows as one row. Core is required; everything else is opt-in.

| Pack | Contents | Source | Hosting | Size |
| --- | --- | --- | --- | --- |
| `core` (required) | Quick cards, checklists, radio frequencies, local overlays | FEMA, CDC, NOAA, Red Cross guidance | Releases | ~80 MB |
| `medical` | First aid, Where There Is No Doctor, WikiMed mini | Hesperian (link only), Kiwix | Releases + linked | ~420 MB |
| `water-food` | Purification, canning, food storage, foraging | CDC, EPA, USDA | Releases | ~160 MB |
| `manuals` | ATP 3-50.21, ATP 4-02.11, FEMA guides | US Army, FEMA | Releases | ~95 MB |
| `maps-roads-us-md` | Streets, trails, points of interest | OpenStreetMap via Protomaps | **Releases** | 214 MB (measured) |
| `maps-topo-us-md` | Contours, hillshade | USGS 3DEP | Releases | ~900 MB |
| `maps-routing-us-md` | Offline directions | OpenStreetMap via Geofabrik | Releases | ~450 MB |
| `shelter-repair` | Repair guides, DIY, knots | iFixit via Kiwix | Linked | 3.3 GiB (measured) |
| `wikipedia-top50k` | Most-read articles | Kiwix | Linked | 6.5 GiB (measured) |
| `offline-ai-model` | Offline AI: answer model (Qwen3-1.7B Q4_K_M) | Hugging Face | Linked | ~1.1 GB |
| `offline-ai-embedder` | Offline AI: source matching (all-MiniLM-L6-v2, ONNX + vocab in a ZIP) | Hugging Face | Releases | ~90 MB |

Nine of the eleven are placeholders: only the two linked Kiwix packs carry real
URLs, sizes and checksums today. Each pack's `README.md` says what is settled
and what is not.

## How updates flow

```
upstream sources ──► weekly Action ──► rebuild changed packs ──► upload to Releases
                                                                       │
        apps fetch manifest ◄── signed manifest ◄── merge ◄── CI ◄── pull request
```

1. The Action reads the Kiwix OPDS catalog, Geofabrik's published timestamps,
   the Protomaps build index and the `ETag` / `Last-Modified` of each government
   PDF. Nothing is downloaded unless it changed.
2. Changed packs we host are rebuilt and uploaded with their real size and
   SHA-256.
3. A pull request updates `manifest.json`.
4. CI checks the schema, every URL and mirror, the checksums, unexpected size
   changes, and `minAppVersion` on any format change.
5. After review and merge, `publish.yml` signs the manifest and publishes it at
   its stable GitHub Pages address.

The workflow also runs by hand — to push refreshed shelter overlays before a
forecast storm, for example.

## One-time setup

The repository already exists at
<https://github.com/Evolvlabsai/holdfast-packs>, with `origin` configured and
one commit. Nothing here has been committed or pushed.

1. **Confirm the repository is public.** GitHub Releases and Pages are free and
   unmetered only for public repos, which is what makes the $0 hosting work.

2. **Generate the signing key — once, ever.**

   ```bash
   python -m venv .venv && . .venv/Scripts/activate      # or bin/activate
   pip install -r scripts/requirements-dev.txt
   python scripts/keygen.py --out "$TMPDIR/holdfast-keys"
   ```

   It refuses to write inside the repository. It prints the public key and the
   path of the private key.

3. **Store the private key** as a repository secret named
   `HOLDFAST_SIGNING_KEY` (Settings → Secrets and variables → Actions → New
   repository secret). Keep one copy in your password manager. Then delete the
   file from disk. Nowhere else, ever.

   Treat it as unrotatable in practice: the public half is compiled into shipped
   apps, so a new key makes every installed copy reject every future manifest
   until those users update the app.

4. **Put the public key and the Pages URL into the app.** In
   `holdfast-app/src/Holdfast.App/Services/HoldfastConfig.cs`, replace the three
   placeholders:

   ```csharp
   public const string ManifestUrl = "https://evolvlabsai.github.io/holdfast-packs/manifest.json";
   public const string SignatureUrl = ManifestUrl + ".sig";
   public const string PublicKeyBase64 = "<the base64 keygen printed>";
   ```

   Until that happens the app rejects every downloaded catalog and keeps its
   built-in seed, which is the intended safe default.

5. **Enable Pages:** Settings → Pages → Build and deployment → Source: **GitHub
   Actions**. The first push to `main` that touches `manifest.json` publishes
   the catalog and its signature.

6. **Protect `main`:** require the `validate` check and at least one review.
   Merging is what authorises a signature, so an unreviewed merge is an
   unreviewed release.

Then confirm the round trip locally before trusting CI:

```bash
python scripts/validate_manifest.py --allow-placeholders --network
python scripts/sign_manifest.py --key-file "$TMPDIR/holdfast-keys/private.key"
python scripts/verify_manifest.py --pub "$TMPDIR/holdfast-keys/public.key"
rm manifest.json.sig
```

## Day to day

| Task | Command |
| --- | --- |
| What moved upstream? | `python scripts/check_upstream.py --verbose` |
| Build the core pack | `python scripts/build_core.py --sources packs/core/sources --id core --out dist/core.hfdb --query "boil water"` |
| Build a PDF pack | `python scripts/build_pdf_pack.py --pack manuals --out dist/manuals.hfdb` |
| Cut a state basemap | `python scripts/extract_maps.py --region us-md --out dist/us-md-roads.pmtiles` |
| Record a rebuilt pack | `python scripts/update_manifest.py --id core --file dist/core.hfdb --url <release asset url> --changes "…"` |
| Re-point a linked pack | `python scripts/update_manifest.py --id shelter-repair --url <new upstream url> --from-url --record-upstream <file name>` |
| Check everything | `python scripts/validate_manifest.py --network --dist dist` |
| Tests | `python -m pytest -q` |

`check_upstream.py` downloads nothing: it reads the Kiwix OPDS catalog, Geofabrik's
`state.txt`, the Protomaps build index and the `ETag` / `Last-Modified` of each
PDF, and compares them with what it saw last time.

The weekly workflow does the same things in order — check, rebuild what changed,
`gh release upload`, edit the manifest, open a pull request — and then stops.

## How to add a state

Everything per-state is one region file plus manifest entries. For Virginia:

1. **Region file** — copy `packs/maps-roads-us-md/regions/us-md.json` to
   `us-va.json` and set `id`, `name`, `region` (`US-VA`) and `bbox`
   (`[min_lon, min_lat, max_lon, max_lat]`). Trim ocean out of the bbox; every
   extra degree of water is paid for in tiles. Check the cost first:

   ```bash
   python scripts/extract_maps.py --region us-va --dry-run
   ```

2. **Pack folders** — `packs/maps-roads-us-va/`, `maps-topo-us-va/`,
   `maps-routing-us-va/`, each with a `README.md` and a `pack.meta.json` copied
   from the Maryland ones (set `id`, `region`, and the Geofabrik `upstream.path`
   for routing).

3. **Manifest entries** — three new packs with `region: "US-VA"`, placeholder
   `url`/`size`/`sha256`, and the same `group`, `license`, `attribution` and
   `staleAfterDays` as Maryland's.

4. **Core overlays** — add `packs/core/sources/overlays/us-va-*.geojson`. Core
   is per-region, so either `core` grows to carry every state's overlays or it
   splits per region. **Undecided** — see Open questions.

5. **Build, upload, record** — `extract_maps.py`, `gh release upload`,
   `update_manifest.py`, then open a pull request.

6. **The app** — `HoldfastConfig` hardcodes Maryland's bbox, centre and pack
   ids. A second state needs that to become a list, which is an app change, not
   a content change.

## Cost

$0 a month. The only fixed costs are the app-store fees (~$124 in year one).

| Item | Where | Cost |
| --- | --- | --- |
| Manifest, signature, schema | GitHub Pages on this repo | free |
| Packs we build (core, medical, water-food, manuals, maps) | GitHub Releases, assets under 2 GB | free |
| Wikipedia, WikiMed, iFixit, Stack Exchange | linked to Kiwix | free |
| AI model | linked to Hugging Face | free |
| CI | GitHub Actions on a public repo | free |

Two things to watch:

- **GitHub's acceptable-use policy** covers releases as a software-distribution
  service, not a CDN. If one pack starts drawing real traffic, add a Cloudflare
  R2 URL to that pack's `mirrors` — R2 has zero egress fees and the free tier
  covers 10 GB. That is a one-line manifest change with no app release, which is
  exactly what the `mirrors` field is for. Budget a few dollars a month if it
  ever happens.
- **Release asset size.** GitHub rejects assets over 2 GB, which is also where
  the manifest's `parts` splitting starts. Nothing we build is near it; the two
  linked ZIMs are far past it, and Kiwix serves them.

## Open questions

Found while building this. The first five are the ones that block packs.

1. **A pack has one `url`, and the spec wants several files in several packs.**
   `medical` is "Hosted + Linked" (our hfdb *and* a Kiwix ZIM), `shelter-repair`
   is "iFixit *and* Stack Exchange", `manuals` wants the extracted text *and*
   the original PDFs for page view. None of those fit one entry. Options per
   pack: split into two ids, host everything ourselves, or add a `components`
   array to a pack entry — which is the clean model and the biggest app change
   (downloader, checksum check, atomic swap, storage accounting). **Decide the
   model once**, not three times.
2. **Resolved: the routing graph has a `format` value.** The enum is now
   `hfdb | pmtiles | zim | hfroute | gguf | onnx | zip`, matching the app's
   `PackFormats`, and `maps-routing-us-md` says `"hfroute"`.
3. **The routing graph is built by hand.** `tools/Holdfast.RouteBuild` is run
   locally and the `.hfroute` file uploaded by hand. It lives in the private
   app repo, so public CI still cannot run it: automating the monthly rebuild
   means publishing it as a binary or building in the private repo and pushing
   here. See `packs/maps-routing-us-md/README.md`.
4. **Roads is Hosted, not Linked.** Neither Protomaps (one ~130 GB planet
   archive) nor Geofabrik (`.osm.pbf` data, not tiles) publishes a per-state
   PMTiles file, so we build and host the extract. Measured: Maryland at
   maxzoom 14 is **214 MB** (the spec guessed 310 MB). The spec's hosting table
   should be corrected.
5. **Topo is two tile types and one `url`.** A PMTiles archive holds one tile
   type; contours are vector and hillshade is raster. Two packs, or contours
   only? See `packs/maps-topo-us-md/README.md`.
6. **Nothing in `packs/core/sources` has been reviewed.** It is the app repo's
   development sample: every quick card is `"draft": true`, the medical figures
   were transcribed by hand, and the overlay points are invented and marked
   `SAMPLE — `. `build_core.py` refuses to build without `--allow-draft` and the
   weekly workflow never passes it. The spec wants a licensed EMT or nurse on
   the medical cards; that has not happened.
7. **No per-state source for shelter and hospital overlays.** The spec's own
   open question, still open. Core claims a weekly cadence it cannot honour
   without one.
8. **Hesperian redistribution is unconfirmed**, so `medical` links to their
   download instead of carrying *Where There Is No Doctor*. Someone has to ask
   them.
9. **Resolved: the AI model is chosen.** Qwen3-1.7B (Apache-2.0) at Q4_K_M,
   run with `/no_think`, linked from Hugging Face as `offline-ai-model`; the
   all-MiniLM-L6-v2 embedder ships as our own ZIP, `offline-ai-embedder`.
   Embeddings are precomputed per `hfdb` pack. Both entries are still
   placeholders until the files are pinned or uploaded.
10. **Two size estimates in the spec are wrong.** `wikipedia-top50k` is 6.5 GiB,
    not 5.2 GB (and the previous edition was 7.8 GiB); `shelter-repair` is
    3.3 GiB for iFixit alone, not 1.2 GB. The Packs screen and storage budget
    need the real numbers.
11. **Two linked packs are over 2 GB and we cannot split them.** The manifest's
    `parts` mechanism only works for files we produce. The app must manage a
    single 6.5 GiB download, with resume, onto a phone filesystem. Confirm on
    real hardware, or ship the 2.7 GiB `nopic` Wikipedia first.
12. **`cdc.gov` and `fsis.usda.gov` block non-browser clients.** Akamai answers
    403 to curl and urllib by TLS fingerprint, not User-Agent, from at least
    some networks — `HEAD` worked from here, a `GET` did not from a different
    egress. FSIS has a GovInfo mirror and `sources.json` uses it; CDC does not.
    Either vendor the one CDC PDF into this repo with its sha256 recorded, or
    find a GovInfo equivalent.
13. **FEMA's long *Are You Ready?* is gone.** Every `fema.gov` path for the 2004
    ~204-page IS-22 edition 404s and IS-22 is retired. `sources.json` uses the
    current 36-page Ready.gov guide. The long edition survives only on
    non-federal mirrors, which this pipeline will not use.
14. **Licensing is settled:** code MIT, our writing CC BY-NC 4.0, with a
    contributor grant so contributions can ship in the app. See [`LICENSE`](LICENSE).
15. **`manifest.json.sig` is not in the repository.** It is produced by
    `publish.yml` and published to Pages. A committed signature goes stale the
    moment anyone edits the manifest, and a stale signature is
    indistinguishable from a tampered one. The spec's layout shows it at the
    root; this is a deliberate deviation.

## The hfdb format

A pack is one plain SQLite file. The schema must match
`HfdbSchema.CreateSql` in the app (`src/Holdfast.Core/Search/LibrarySearch.cs`)
exactly, and `tests/test_hfdb.py` asserts the SQL text so drift fails a test
rather than silently producing packs the app skips.

```sql
meta(key TEXT PRIMARY KEY, value TEXT)              -- id, name, version
docs(doc_id TEXT PRIMARY KEY, title, body, location, source)
docs_fts  -- FTS5 over (title, body), content='docs', tokenize='porter unicode61'
cards(card_id TEXT PRIMARY KEY, sort INTEGER, json TEXT)
overlays(overlay_id TEXT PRIMARY KEY, region TEXT, geojson TEXT)
```

`location` is what a search hit cites: a relative path for a markdown document,
`"p. 14"` for a page of a PDF. Content packs are **not** encrypted; only the
on-device vault is.

## Contributing

Contributions are welcome, especially:

- **Quick cards** — short, step-by-step, with a named source.
- **Regional overlays** — shelters, hospitals, water sources, fuel and rally
  points as GeoJSON, with the data source and its licence.
- **New map regions**, and fixes to the source lists.

Rules:

- Every addition needs a named source and a licence that allows redistribution.
- All changes go through pull-request review. Medical content is reviewed by a
  qualified reviewer before release; every quick card cites its source; no card
  gives a medicine dose.
- Contributions are accepted under the terms in [`LICENSE`](LICENSE): code MIT,
  writing CC BY-NC 4.0, plus a licence to EvolvLabs, LLC to ship them in the app.

See [`.github/pull_request_template.md`](.github/pull_request_template.md) for
the checklist.

## Support the project

Holdfast is free. If it helps you, you can support it through
[GitHub Sponsors](https://github.com/sponsors/Evolvlabsai). Support covers
app-store fees and any hosting overflow.

## Disclaimer

This content is general information, not medical or professional advice. In an
emergency, call 911 when you can.

---

Maintained by [EvolvLabs](https://evolvlabs.ai).

### Note on two replaced files

This repository's first commit contained a `README.md` and a `.gitattributes`.
Both have been rewritten in the working tree and **not committed**, so the
originals are intact in `HEAD` (`git show HEAD:README.md`). What the original
README said and this one keeps: the pack table, the update-flow diagram, the
contributing rules, the Sponsors link, the disclaimer and the maintainer line.
What changed:

- the layout section now matches what is actually here. The original listed
  `overlays/<region>/` at the repository root; overlays live in
  `packs/core/sources/overlays/` instead, because they ship *inside* the Core
  pack and a build script should find a pack's inputs under that pack.
- `manifest.json.sig` is no longer listed as a file in the repository; CI
  produces it (Open question 15).
- roads is marked Hosted rather than Linked (Open question 4), and the three
  measured sizes replace the estimated ones.
- `.gitattributes` keeps `* text=auto` and adds explicit `eol=lf` rules, plus
  `-text` on the manifest and its signature so no checkout can rewrite the bytes
  a signature covers.
