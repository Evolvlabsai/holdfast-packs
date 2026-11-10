# maps-routing-us-hi — Hawaii: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 13 MB for Hawaii
  (167,499 nodes, 210,792 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf hawaii-latest.osm.pbf --out us-hi-routing.hfroute --bbox -160.26,18.9,-154.8,22.24
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-hi.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/hawaii-latest.osm.pbf`
(27,653,711 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `hawaii-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
