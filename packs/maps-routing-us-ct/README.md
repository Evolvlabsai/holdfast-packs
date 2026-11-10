# maps-routing-us-ct — Connecticut: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 65 MB for Connecticut
  (845,453 nodes, 1,068,893 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf connecticut-latest.osm.pbf --out us-ct-routing.hfroute --bbox -73.73,40.98,-71.78,42.06
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-ct.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/connecticut-latest.osm.pbf`
(217,494,509 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `connecticut-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
