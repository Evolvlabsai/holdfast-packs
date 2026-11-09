# maps-routing-us-md — Maryland: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. ~450 MB for Maryland.
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

The graph is built locally with `tools/Holdfast.RouteBuild` from the
`holdfast-app` repo, from the Geofabrik extract below:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf maryland-latest.osm.pbf --out us-md-routing.hfroute --bbox=-79.49,37.88,-75.05,39.73
```

The result is one `.hfroute` file, uploaded by hand to a release here and
recorded with `update_manifest.py --id maps-routing-us-md`.

`scripts/build_routing.py` is a stub that prints this and exits 2.

### Public CI still cannot run it

`holdfast-app` is a private repo. This repo is public; its Actions cannot read a
private sibling without a cross-repo token, and even with one, building a graph
here means running private code in public CI. So the weekly workflow never
rebuilds this pack, and the monthly refresh is a manual step. Ways to automate
it later, none chosen:

1. publish RouteBuild as a release binary (simplest to run; ships a binary whose
   source the public repo cannot show, which sits badly with a repo whose point
   is auditable content);
2. build the graph in the private repo's CI and have it upload here (keeps the
   tool private; moves the trust boundary, since the private repo then needs
   write access to this one).

### Format: solved

The manifest's `format` enum now has `hfroute`, matching the app's
`PackFormats.HfRoute`, and this entry uses it. RouteBuild writes one file, so
the app installs it as-is with no unpack step. The entry is still a placeholder
(size 0, sha256 of 64 zeros) until a built graph is uploaded.

## Upstream

`https://download.geofabrik.de/north-america/us/maryland-latest.osm.pbf`
(216,810,553 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from
`maryland-updates/state.txt`, which `check_upstream.py` reads —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
