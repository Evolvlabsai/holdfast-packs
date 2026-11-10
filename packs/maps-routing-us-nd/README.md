# maps-routing-us-nd — North Dakota: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 38 MB for North Dakota
  (430,400 nodes, 553,454 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf north-dakota-latest.osm.pbf --out us-nd-routing.hfroute --bbox -104.05,45.93,-96.55,49.01
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-nd.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/north-dakota-latest.osm.pbf`
(128,299,496 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `north-dakota-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4965` when last checked.
