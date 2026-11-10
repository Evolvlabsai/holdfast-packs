# maps-routing-us-tn — Tennessee: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 116 MB for Tennessee
  (1,505,222 nodes, 1,875,372 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf tennessee-latest.osm.pbf --out us-tn-routing.hfroute --bbox -90.32,34.98,-81.64,36.68
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-tn.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/tennessee-latest.osm.pbf`
(191,353,641 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `tennessee-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
