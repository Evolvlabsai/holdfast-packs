# maps-routing-us-nh — New Hampshire: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 42 MB for New Hampshire
  (529,097 nodes, 650,736 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf new-hampshire-latest.osm.pbf --out us-nh-routing.hfroute --bbox -72.56,42.69,-70.6,45.31
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-nh.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/new-hampshire-latest.osm.pbf`
(72,521,640 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `new-hampshire-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
