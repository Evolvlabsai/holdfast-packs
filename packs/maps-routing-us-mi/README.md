# maps-routing-us-mi — Michigan: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 228 MB for Michigan
  (3,069,688 nodes, 4,148,448 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf michigan-latest.osm.pbf --out us-mi-routing.hfroute --bbox -90.42,41.69,-82.41,48.23
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-mi.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/michigan-latest.osm.pbf`
(317,258,877 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `michigan-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4966` when last checked.
