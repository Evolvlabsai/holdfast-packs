# maps-routing-us-nv — Nevada: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 73 MB for Nevada
  (790,698 nodes, 1,071,468 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf nevada-latest.osm.pbf --out us-nv-routing.hfroute --bbox -120.01,35.0,-114.03,42.01
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-nv.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/nevada-latest.osm.pbf`
(124,132,717 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `nevada-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4966` when last checked.
