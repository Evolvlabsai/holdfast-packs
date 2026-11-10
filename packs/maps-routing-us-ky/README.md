# maps-routing-us-ky — Kentucky: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 89 MB for Kentucky
  (1,027,677 nodes, 1,267,394 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf kentucky-latest.osm.pbf --out us-ky-routing.hfroute --bbox -89.58,36.49,-81.96,39.15
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-ky.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/kentucky-latest.osm.pbf`
(155,180,792 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `kentucky-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4966` when last checked.
