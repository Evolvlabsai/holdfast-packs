# maps-routing-us-mo — Missouri: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 144 MB for Missouri
  (1,823,224 nodes, 2,368,080 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf missouri-latest.osm.pbf --out us-mo-routing.hfroute --bbox -95.78,35.99,-89.09,40.62
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-mo.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/missouri-latest.osm.pbf`
(200,631,633 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `missouri-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4965` when last checked.
