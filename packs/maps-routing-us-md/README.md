# maps-routing-us-md — Maryland: offline routing

Walking and driving directions with no signal.

- **Hosting:** ours, per region. ~450 MB for Maryland.
- **Cadence:** monthly, following the OSM extract.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0, derived from the same OpenStreetMap extract.

## NOT BUILT, and blocked on three things

`scripts/build_routing.py` is a TODO stub that prints its plan and exits 2.

### 1. The builder lives in the private repo

The routing graph builder is `tools/Holdfast.RouteBuild` in the private
`holdfast-app` repo. This repo is public; its Actions cannot read a private
sibling without a cross-repo token, and even with one, building a graph here
means running private code in public CI. Three ways out, set out in the stub:

1. publish RouteBuild as a release binary (simplest to run; ships a binary whose
   source the public repo cannot show, which sits badly with a repo whose point
   is auditable content);
2. build the graph in the private repo's CI and have it upload here (keeps the
   tool private; moves the trust boundary, since the private repo then needs
   write access to this one);
3. use GraphHopper's or Valhalla's own stock builder in a container (most
   reproducible for outsiders; forces the engine choice the spec left open).

**None chosen.** This is the one pack whose pipeline cannot be finished inside
this repo as things stand.

### 2. There is no `format` value for a routing graph

The manifest's `format` enum is `hfdb | pmtiles | zim | gguf`. A routing graph
is none of them. **This entry currently says `"format": "pmtiles"`, which is
wrong.** It matches the placeholder in the app's own built-in seed catalog, and
if it ever carried a real checksum the app would hand a graph archive to
MapLibre. Before this pack can ship:

- add a value (`graph`, or `ghgraph` / `valhalla` if the engine should be
  explicit) to the app's `format` handling and to `schema/manifest.schema.json`;
- raise this pack's `minAppVersion` in the same change, so an older app hides it
  instead of downloading something it cannot open.

The entry is inert meanwhile: its sha256 is 64 zeros, so any download fails its
checksum.

### 3. A graph is a directory and the app installs one file

Both engines produce a tree (`graph-cache/`, or a Valhalla tile tree). Packed as
a tar or zip it is one file, but then the app has to unpack it during install —
and the app's install path writes one data file and renames it into place. That
is a new step on the app side, not a pipeline detail.

## Upstream

`https://download.geofabrik.de/north-america/us/maryland-latest.osm.pbf`
(216,810,553 bytes on 2026-11-09), with `.osm.pbf.md5` beside it. Geofabrik
publishes md5 only, no sha256. Freshness comes from
`maryland-updates/state.txt`, which `check_upstream.py` reads —
`timestamp=2026-11-08T21:21:00Z`, `sequenceNumber=4967` when last checked.
