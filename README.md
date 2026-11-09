# Holdfast Packs

**Open content for the Holdfast offline survival app.** This repo holds the signed catalog of every content pack, the scripts that build them, and the pipeline that keeps them current. The app itself lives in a separate, private repo.

> Status: design phase. Holdfast is a working name.

---

## What's here

- **`manifest.json`:** the catalog of every pack the app can download, with versions, sizes, checksums and URLs.
- **`manifest.json.sig`:** an Ed25519 signature. The app ignores any manifest that isn't signed with the project key.
- **Build scripts** for the packs we host (quick cards, manuals, overlays, topo, routing).
- **A weekly GitHub Action** that checks upstream sources, rebuilds what changed, and opens a pull request.
- **GitHub Releases** hosting the pack files we build.

Large third-party content (Wikipedia, OpenStreetMap extracts, AI models) is not stored here. The manifest points the app straight to its upstream host.

## Packs

| Pack | Contents | Source | Hosting | License |
| --- | --- | --- | --- | --- |
| Core (required) | Quick cards, checklists, radio frequencies, local overlays | FEMA, CDC, NOAA, Red Cross guidance | Releases | Ours; sources public domain |
| Medical | First aid, Where There Is No Doctor, WikiMed mini | Hesperian, Kiwix | Releases + linked | Hesperian terms; CC BY-SA |
| Water & Food | Purification, canning, food storage, foraging basics | CDC, EPA, USDA | Releases | Public domain |
| Survival manuals | ATP 3-50.21, field first aid, FEMA guides | US Army, FEMA | Releases | Public domain |
| Maps: roads | Streets, trails, points of interest | OpenStreetMap | Linked | ODbL |
| Maps: topo | Contours, hillshade | USGS | Releases | Public domain |
| Maps: routing | Offline directions | OpenStreetMap | Releases | ODbL |
| Shelter & Repair | Repair guides, DIY, knots | iFixit, Stack Exchange via Kiwix | Linked | CC BY-NC-SA, CC BY-SA |
| Wikipedia top 50k | Most-read articles | Kiwix | Linked | CC BY-SA |
| Offline AI | Local model + embeddings | Hugging Face | Linked | Model license |

## How updates flow

```
upstream sources ──► weekly Action ──► rebuild changed packs ──► upload to Releases
                                                                       │
        apps fetch manifest ◄── signed manifest ◄── merge ◄── CI ◄── pull request
```

1. The Action checks the Kiwix catalog, Geofabrik dates and checksums, and `ETag` / `Last-Modified` headers on government sources.
2. Changed packs are rebuilt and uploaded with their size and SHA-256.
3. A pull request updates `manifest.json`.
4. CI checks the schema, every URL and mirror, checksums, and unexpected size changes.
5. After review and merge, the manifest is signed and published at its stable URL on GitHub Pages.

The workflow can also be run by hand, for example to push refreshed shelter overlays before a storm.

## Repository layout

```
manifest.json            Signed catalog of every pack
manifest.json.sig        Ed25519 signature
schema/                  JSON Schema for the manifest
packs/<id>/              Sources list and build script for each pack we host
overlays/<region>/       Rally points, shelters, hospitals, water, fuel (GeoJSON)
.github/workflows/       update.yml (scheduled) and validate.yml (CI)
```

## Manifest entry

```json
{
  "id": "maps-roads-us-md",
  "name": "Maryland: roads",
  "group": "maps",
  "region": "US-MD",
  "version": "2026.11.01",
  "published": "2026-11-01",
  "format": "pmtiles",
  "size": 325058560,
  "sha256": "<64 hex chars>",
  "url": "https://github.com/<org>/holdfast-packs/releases/download/<tag>/us-md-roads.pmtiles",
  "mirrors": [],
  "staleAfterDays": 90,
  "license": "ODbL-1.0",
  "attribution": "© OpenStreetMap contributors",
  "changes": "Latest OSM data: new roads, closures, points of interest",
  "minAppVersion": "1.0.0"
}
```

Files over 2 GB are split into numbered parts, each with its own checksum.

## Contributing

Contributions are welcome, especially:

- **Quick cards:** short, step-by-step, with a named source.
- **Regional overlays:** shelters, hospitals, water sources, fuel and rally points as GeoJSON, with the data source and its license.
- **New map regions** and fixes to source lists.

Rules:

- Every addition needs a named source and a license that allows redistribution.
- All changes go through pull request review. Medical content is reviewed by a qualified reviewer before release.
- Contributions are accepted under the content license below.

## Licenses

- Content written for this repo: **[TBD: CC BY-SA 4.0 or CC0]**.
- Build scripts and pipeline code: **[TBD]**.
- Third-party content keeps its own license, listed per pack in the manifest and shown in the app.

## Support the project

Holdfast is free. If it helps you, you can support it through [GitHub Sponsors](https://github.com/sponsors/<org>). Support covers app-store fees and hosting.

## Disclaimer

This content is general information, not medical or professional advice. In an emergency, call 911 when you can.

---

Maintained by [EvolvLabs](https://evolvlabs.ai).
