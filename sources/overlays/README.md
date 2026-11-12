# Hospital and shelter overlays

Input for `scripts/build_overlays.py`, which builds one `overlays-us-xx` pack per
state (hospitals and designated shelters as map pins).

| File | What it is |
| --- | --- |
| `hospital-locations.csv` | Cache: CMS facility id → latitude, longitude, and where the location came from (`census` = US Census Bureau geocoder, `osm` = OpenStreetMap hospital matched by name near the ZIP code). The builder only looks up hospitals that are not in here yet, then rewrites the file. Commit it after a build. |
| `hospital-fixes.csv` | Hand-entered locations. They override the cache. Use them for the hospitals listed in `dist/overlays/overlays-unplaced.csv`. |

## Sources

- **Hospitals:** CMS *Hospital General Information* (data.cms.gov, dataset
  `xubh-q36u`). Public domain. CMS refreshes it every quarter.
- **Shelters:** FEMA National Shelter System facilities (`gis.fema.gov`,
  `NSS/FEMA_NSS` layer 5). Public domain. These are buildings designated as
  shelters. The list does **not** say which are open; every shelter pin carries
  "It may not be open. Check local radio or news."
- **Some hospital locations:** OpenStreetMap, ODbL-1.0. The packs therefore say
  "© OpenStreetMap contributors", as the road maps already do.

Left out on purpose: shelter contact names, phones and e-mails; inactive
shelters; points outside their state's bounding box. Shelters whose latitude and
longitude were loaded the wrong way round (all of Wisconsin, in November 2026)
are swapped back.

## Status (2026-11-11)

First build: 5,122 hospitals and 69,737 shelters across the 50 states and DC.
232 hospitals could not be placed yet. **Not in the catalog yet.** The app must
first show the "may not be open" warning on a tapped pin, and its first-run
setup must skip packs it cannot use. That is app 0.5.2. Publish the
`overlays-us-xx` entries (with `minAppVersion` 0.5.2) once 0.5.2 is live on both
stores.

## Build

```bash
python scripts/build_overlays.py --out dist/overlays                 # downloads, every state
python scripts/build_overlays.py --out dist/overlays --region us-md  # one state
python scripts/build_overlays.py --out dist/overlays --offline       # reuse .cache/overlays
```
