# maps-routing-us-sd — South Dakota: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 29 MB for South Dakota
  (347,018 nodes, 463,323 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf south-dakota-latest.osm.pbf --out us-sd-routing.hfroute --bbox -104.06,42.47,-96.43,45.95
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-sd.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/south-dakota-latest.osm.pbf`
(50,326,649 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `south-dakota-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4965` when last checked.
