# maps-routing-us-il — Illinois: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 239 MB for Illinois
  (3,285,623 nodes, 4,503,472 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf illinois-latest.osm.pbf --out us-il-routing.hfroute --bbox -91.52,36.97,-87.49,42.51
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-il.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/illinois-latest.osm.pbf`
(363,165,932 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `illinois-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4965` when last checked.
