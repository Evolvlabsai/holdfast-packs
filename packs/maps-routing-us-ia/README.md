# maps-routing-us-ia — Iowa: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 74 MB for Iowa
  (965,421 nodes, 1,320,413 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf iowa-latest.osm.pbf --out us-ia-routing.hfroute --bbox -96.64,40.37,-90.14,43.51
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-ia.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/iowa-latest.osm.pbf`
(134,409,988 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `iowa-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4965` when last checked.
