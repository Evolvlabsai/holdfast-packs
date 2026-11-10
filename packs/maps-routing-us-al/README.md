# maps-routing-us-al — Alabama: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 93 MB for Alabama
  (1,135,994 nodes, 1,441,799 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf alabama-latest.osm.pbf --out us-al-routing.hfroute --bbox -88.48,30.14,-84.88,35.01
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-al.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/alabama-latest.osm.pbf`
(151,825,646 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `alabama-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
