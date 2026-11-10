# maps-routing-us-ma — Massachusetts: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 117 MB for Massachusetts
  (1,493,339 nodes, 1,955,471 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf massachusetts-latest.osm.pbf --out us-ma-routing.hfroute --bbox -73.51,41.23,-69.92,42.89
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-ma.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/massachusetts-latest.osm.pbf`
(311,670,184 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `massachusetts-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
