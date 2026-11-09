#!/usr/bin/env python3
"""TODO (not implemented): build the per-state offline routing graph.

Running this script exits 2 and prints the plan below.

Manifest entry: ``maps-routing-us-md`` -- Hosted, ~450 MB for Maryland, monthly,
ODbL, ``staleAfterDays`` 90.

THE BLOCKER (open question for the owner)
-----------------------------------------
The routing graph builder is ``tools/Holdfast.RouteBuild`` in the **private**
``holdfast-app`` repo. This repo is public and its Actions cannot read a private
sibling without a cross-repo token, and even with one, building a graph here
would mean compiling private code in public CI.

Three ways out, none chosen:

1. **Publish RouteBuild as a release binary** on the private repo and download
   it here with a token, or publish it on a public repo of its own. Simplest to
   run; means shipping a binary whose source the public repo cannot show, which
   sits badly with a repo whose whole point is auditable content.
2. **Build the graph in the private repo's CI** and have that workflow upload it
   to this repo's release and open the manifest PR. Keeps the tool private; the
   private repo then needs write access here, so the trust boundary moves.
3. **Use the upstream engine's own packaging** -- GraphHopper's or Valhalla's
   stock graph builder in a container -- and keep RouteBuild for app-side
   queries only. Most reproducible for outsiders, and it pins the engine choice,
   which the spec has not made ("GraphHopper or Valhalla").

Until one is picked, ``maps-routing-us-md`` stays a placeholder entry and this
script refuses to run. **This is the one pack whose pipeline cannot be finished
inside this repo as things stand.**

INPUTS
------
1. ``https://download.geofabrik.de/north-america/us/<state>-latest.osm.pbf``
   (Maryland: 216,810,553 bytes as of 2026-11-09), with its ``.osm.pbf.md5``
   sibling. Geofabrik publishes md5, not sha256.
2. Freshness: ``<state>-updates/state.txt`` carries ``timestamp=`` and
   ``sequenceNumber=``; ``check_upstream.py`` reads it, so a rebuild only
   happens when the extract really moved.
3. The engine's own config (profiles: foot, car; the spec wants walking first).

STEPS
-----
1. Conditional download of the .pbf, verify the md5.
2. Run the graph builder for the chosen engine:
   - GraphHopper: ``java -jar graphhopper-web.jar import config.yml`` ->
     a ``graph-cache/`` directory;
   - Valhalla: ``valhalla_build_config`` + ``valhalla_build_tiles`` ->
     a tile tree + ``valhalla_tiles.tar``.
3. Pack the result into ONE file, because the manifest gives a pack one URL and
   the app downloads one file per pack: a tar (Valhalla already does this) or a
   zip of ``graph-cache/``. The app must then unpack it during install, which is
   a **new step the app does not have today** -- its install path writes one
   data file and swaps it atomically. Flagged for the app side.
4. Record the OSM extract timestamp in the pack so the app can show what the
   routing data is as of.

OUTPUT
------
``dist/<region>-routing.<tar|zip>`` (extension decided with step 3), uploaded to
a release, then ``update_manifest.py --id maps-routing-<region>``.

Note the ``format`` field: the manifest's enum is ``hfdb | pmtiles | zim |
gguf``. A routing graph is none of those. The seed catalog in the app currently
calls it ``pmtiles``, which is **wrong** -- the app would hand it to MapLibre.
Either a ``graph`` (or ``ghgraph`` / ``valhalla``) format value is added to the
app's enum and to ``schema/manifest.schema.json``, with ``minAppVersion`` raised
on this pack, or the routing pack cannot ship. Flagged in README.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import util  # noqa: E402


def main() -> int:
    util.info(__doc__ or "")
    util.info("")
    util.fail(
        "build_routing.py is a TODO stub and builds nothing. It is blocked on where "
        "tools/Holdfast.RouteBuild runs and on the missing 'graph' format value "
        "(see README.md, Open questions).",
        code=2,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
