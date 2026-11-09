#!/usr/bin/env python3
"""Stub: the per-state offline routing graph is built by hand, not here.

Running this script exits 2 and prints the steps below.

Manifest entry: ``maps-routing-us-md`` -- format ``hfroute``, Hosted, ~450 MB
for Maryland, monthly, ODbL, ``staleAfterDays`` 90.

HOW IT IS BUILT
---------------
The graph builder is ``tools/Holdfast.RouteBuild`` in the ``holdfast-app``
repo. It is run locally, by hand:

    dotnet run --project tools/Holdfast.RouteBuild -c Release --         --pbf maryland-latest.osm.pbf --out us-md-routing.hfroute         --bbox=-79.49,37.88,-75.05,39.73

and its single output file is uploaded by hand:

    gh release upload maps-<yyyy.mm> us-md-routing.hfroute
    python scripts/update_manifest.py --id maps-routing-us-md         --file us-md-routing.hfroute --url <release asset url> --version <yyyy.mm.dd>

The format problem is solved: the manifest's enum has ``hfroute``, matching the
app's ``PackFormats.HfRoute``, and RouteBuild writes one file the app installs
as-is, with no unpack step.

WHY PUBLIC CI STILL CANNOT RUN IT
---------------------------------
``holdfast-app`` is a **private** repo. This repo is public and its Actions
cannot read a private sibling without a cross-repo token, and even with one,
building a graph here would mean compiling private code in public CI. Ways to
automate it later, none chosen:

1. **Publish RouteBuild as a release binary** and download it here. Simplest to
   run; means shipping a binary whose source the public repo cannot show, which
   sits badly with a repo whose whole point is auditable content.
2. **Build the graph in the private repo's CI** and have that workflow upload it
   to this repo's release and open the manifest PR. Keeps the tool private; the
   private repo then needs write access here, so the trust boundary moves.

Until then the weekly workflow never rebuilds this pack and this script refuses
to run.

INPUTS
------
1. ``https://download.geofabrik.de/north-america/us/<state>-latest.osm.pbf``
   (Maryland: 216,810,553 bytes as of 2026-11-09), with its ``.osm.pbf.md5``
   sibling. Geofabrik publishes md5, not sha256. Verify it before building.
2. Freshness: ``<state>-updates/state.txt`` carries ``timestamp=`` and
   ``sequenceNumber=``; ``check_upstream.py`` reads it, so a rebuild is only
   worth doing when the extract really moved.
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
        "build_routing.py is a stub and builds nothing. The graph is built by hand with "
        "tools/Holdfast.RouteBuild from the private holdfast-app repo, which public CI "
        "cannot run (see packs/maps-routing-us-md/README.md).",
        code=2,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
