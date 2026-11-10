# maps-routing-us-nm — New Mexico: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 70 MB for New Mexico
  (765,931 nodes, 1,031,270 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf new-mexico-latest.osm.pbf --out us-nm-routing.hfroute --bbox -109.06,31.33,-103.0,37.01
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-nm.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/new-mexico-latest.osm.pbf`
(136,790,862 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `new-mexico-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4966` when last checked.
