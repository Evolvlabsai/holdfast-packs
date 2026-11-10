# maps-routing-us-ga — Georgia: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 170 MB for Georgia
  (2,272,635 nodes, 2,845,600 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf georgia-latest.osm.pbf --out us-ga-routing.hfroute --bbox -85.61,30.35,-80.83,35.01
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-ga.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/georgia-latest.osm.pbf`
(358,492,132 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `georgia-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
