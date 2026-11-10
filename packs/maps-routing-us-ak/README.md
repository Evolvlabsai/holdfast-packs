# maps-routing-us-ak — Alaska: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. 18 MB for Alaska
  (219,130 nodes, 275,963 edges, built 2026-11-09).
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.
- **Format:** `hfroute`, a single-file routing graph the app opens with
  `Holdfast.Routing`.

**Antimeridian:** the bbox is clipped at -180. Web Mercator tile ranges and a PMTiles bbox cannot wrap, so the western Aleutians west of 180 degrees (the Rat and Near Islands: Attu, Agattu, Shemya, Kiska, Amchitka, Semisopochnoi) are not in this pack.

## How it is built: by hand, outside public CI

Exactly as for Maryland (see `packs/maps-routing-us-md/README.md` for why public
CI cannot run it). With `tools/Holdfast.RouteBuild` from the `holdfast-app` repo:

```
dotnet run --project tools/Holdfast.RouteBuild -c Release -- --pbf alaska-latest.osm.pbf --out us-ak-routing.hfroute --bbox -180.0,51.2,-129.97,71.4
```

`--bbox` takes its value as a separate argument. The box is the region file's
(`packs/maps-roads-us-md/regions/us-ak.json`).

## Upstream

`https://download.geofabrik.de/north-america/us/alaska-latest.osm.pbf`
(144,211,221 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from `alaska-updates/state.txt` —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
