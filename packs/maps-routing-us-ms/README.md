# maps-routing-us-ms — Mississippi: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 53 MB for Mississippi
  (665,263 nodes, 835,315 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf mississippi-latest.osm.pbf --out us-ms-routing.hfroute --bbox -91.66,30.17,-88.09,35.0
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-ms.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/mississippi-latest.osm.pbf`
(95,207,384 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `mississippi-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4966` when last checked.
