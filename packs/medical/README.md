# medical — Medical

Public-domain US Government first-aid and emergency-health texts, searchable
offline, one search document per PDF page so every hit cites a page.

- **Hosting:** hosted (GitHub Releases hfdb).
- **Builder:** `scripts/build_pdf_pack.py --pack medical`, reading
  [`sources.json`](sources.json).
- **Cadence:** monthly.
- **`staleAfterDays`:** 30.

## Clinician review comes first

Every document in `sources.json` carries a `reviewNote`: *Medical content.
Clinician review required before release.* Several sources are old (the
largest is the 2003 edition of a USPHS manual), so doses, drug choices and
phone numbers in them may be out of date. The pack builds; it is **not
releasable** until a clinician has been through it, and nothing from it may
become a quick card without that review.

## What is in it

All verified on 2026-11-09 with a plain `urllib` download.

| Document | Publisher | Pages |
| --- | --- | --- |
| *The Ship's Medicine Chest and Medical Aid at Sea* (2003) | US Public Health Service, Office of the Surgeon General | 410 (380 with text) |
| *Extreme Heat: A Prevention Guide* | CDC, National Center for Environmental Health | 13 |
| *Fast Facts: Protecting Yourself from Cold Stress* | CDC / NIOSH | 2 |
| *Emergency Wound Care After a Natural Disaster* (2017) | CDC | 1 |
| *You Can Prevent Carbon Monoxide Exposure* (2017) | CDC, National Center for Environmental Health | 1 |
| *Coping with Stress After a Traumatic Event* (2008) | CDC, National Center for Injury Prevention and Control | 2 |

The Ship's Medicine Chest carries the weight: it is written for someone with
no doctor available, which is the situation this pack is for. The CDC sheets
are short but cover the things that kill or hurt people after a disaster:
heat, cold, dirty wounds, generator carbon monoxide, and stress.

Army first aid (ATP 4-02.11) and survival (ATP 3-50.21) live in the `manuals`
pack and are not duplicated here. What was tried and left out, and why, is in
the `_notes` of `sources.json` (a mislabelled CDC cold guide, SAMHSA and OSHA
hosts that 403 scripted downloads, a CAC-gated Army hygiene manual).

## Not in it

### Hesperian: linked, never hosted

*Where There Is No Doctor* is free to read but copyrighted. It stays out of
this pack until Hesperian gives written permission to redistribute it.
**Nobody has asked yet.** Until then the Packs screen should send the user to
<https://hesperian.org/books-and-resources/>.

American Red Cross and American Heart Association material is excluded for
the same reason.

### WikiMed: a separate linked pack, later

WikiMed (Kiwix ZIM of Wikipedia's medical articles, CC BY-SA 4.0) is planned as
its own linked pack (working id `medical-wikimed`) once the app can read ZIM
files. A manifest entry has exactly one `url` and one `format`, so it cannot
ride inside this hfdb entry. Verified live on 2026-11-09 against
`download.kiwix.org`:

| Edition | File | Bytes |
| --- | --- | --- |
| **mini (chosen)** | `wikipedia_en_medicine_mini_2026-10.zim` | 174,350,854 |
| nopic | `wikipedia_en_medicine_nopic_2026-10.zim` | 1,047,708,415 |
| maxi | `wikipedia_en_medicine_maxi_2026-10.zim` | 1,864,210,320 |

sha256 of the mini file, read from the publisher's own `.zim.sha256` sidecar:
`c66f27274775870cec7e0c230c7e7626d367633b1f26c4a74499c249ddac0822`

These facts sit in `pack.meta.json` under `companions` until that pack exists.

## Manifest

`manifest.json` still carries a placeholder entry for `medical`. It gets a real
url, size and sha256 when a reviewed build is released, not before.
