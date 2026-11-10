# maps-routing-us-va — Virginia: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 177 MB for Virginia
  (2,107,109 nodes, 2,643,004 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf virginia-latest.osm.pbf --out us-va-routing.hfroute --bbox -83.68,36.54,-75.24,39.47
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-va.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/virginia-latest.osm.pbf`
(429,447,424 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `virginia-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
