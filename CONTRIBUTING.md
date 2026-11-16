# Contributing quick cards and survival skills

Holdfast is a free, offline emergency-prep app. Anyone can suggest a new
**quick card** (short steps for an emergency, like "Stop bleeding") or a new
**survival skill** (a small project with drawings, like a water-jug lantern), or
fix one that is already here.

You do not need to write code. Each card is one text file, and each skill is
one folder.

- **Not comfortable with GitHub?** [Open an issue](../../issues/new/choose) with
  the "Suggest a quick card or skill" form. Describe the idea and name your
  source. A maintainer will turn it into a file.
- **Comfortable with GitHub?** Fork the repo, add or edit a file as shown
  below, and open a pull request.

## The rules

1. **Name a public source.** Every card and skill names where its advice comes
   from: a government agency (CDC, FEMA, Ready.gov, NOAA, National Park
   Service, U.S. Forest Service, U.S. Army), the American Red Cross, the
   American Heart Association, or similar. Do not copy their text word for
   word. Write it in your own plain words.
2. **No medicine doses.** No "mg", "tablets of" or "take two". A check refuses them.
3. **Plain, short sentences.** Someone may read this while scared, in the dark,
   one-handed. Use one action per sentence and everyday words. Use American
   English.
4. **Safety first.** Projects with flame or fuel (categories `light`, `fire`,
   `cooking`, `warmth`) must list at least one warning. Never suggest burning
   anything indoors without saying how to stay safe from fire and carbon
   monoxide.
5. **Your own work only.** Drawings must be your own. By opening a pull
   request, you agree that your writing and drawings are published under this
   repo's writing license, [CC BY-NC 4.0](LICENSE).
6. **Everything is reviewed before it ships.** New and changed content starts
   as `status: draft`. A maintainer has it checked, medical content by a
   clinician, then sets `status: reviewed` and the date. Until then, the pull
   request's checks stay red on purpose and nothing reaches the app.

## A quick card

One file: `packs/core/sources/cards/<id>.md`. The `id` is the file name:
lower-case words joined by hyphens.

```markdown
---
id: choking
title: Choking
lead: Can't cough, speak or breathe? Act now. Have someone call 911.
tone: normal
icon: alert
order: 70
source: American Red Cross choking first aid (adult); American Heart Association
status: draft
---

## Ask: are you choking?

If they can cough hard or speak, let them keep coughing. Stay with them.

## Give 5 back blows

Stand behind them and lean them forward. Hit firmly between the shoulder
blades with the heel of your hand, 5 times.
```

| Field | What to put |
| --- | --- |
| `id` | Same as the file name, for example `heat-stroke` |
| `title` | Up to 40 characters. It is the tile on the Home screen. |
| `lead` | One line under the title, up to 120 characters. Put "call 911" here when it applies. |
| `tone` | `normal`, or `danger` for a red card. Keep red for the few cards where seconds count. |
| `icon` | One of: `alert`, `bolt`, `cold`, `compass`, `drop`, `flame`, `heart`, `info`, `pill`, `plus`, `shelter`, `shield-alert`, `signal`, `sun`, `timer`, `water` |
| `timer` | Optional. `tourniquet` adds the tourniquet timer button. |
| `order` | A whole number that sets its place in the list. The first six show on Home. New cards go at the end. |
| `source` | Where the advice comes from |
| `status` | `draft`. A maintainer changes it to `reviewed`. |
| `reviewed` | Added by the maintainer with the review date, `YYYY-MM-DD` |

**Steps:** each `## ` heading is one step, with one short paragraph under it.
A card has 3 to 8 steps. Keep step titles under 50 characters and step text
under 400. Cards have no pictures.

## A survival skill

One folder: `packs/core/sources/skills/<id>/`, with a `skill.md` and the
drawings it uses.

```markdown
---
id: jug-lantern
title: Water-jug lantern
summary: Turn a headlamp and a jug of water into a lamp that lights a whole room.
category: light
difficulty: easy
time: 2 minutes
order: 10
needs:
  - A headlamp or small flashlight
  - A clear or milky-white plastic jug, full of water
warnings:
  - Use a battery light. Never put a candle or any flame inside a plastic jug.
source: Common preparedness practice; light-safety advice from Ready.gov (power outages)
status: draft
---

## Fill the jug

![A gallon jug filled with water, with the cap on.](fill.svg)

Fill the jug with water and close the cap.

## Strap the light on

![A headlamp strapped around the jug with the bulb facing in.](strap.svg)

Put the headlamp strap around the jug, with the light pointing in at the water.
```

| Field | What to put |
| --- | --- |
| `category` | `light`, `fire`, `cooking`, `water`, `shelter`, `signals`, `sanitation`, `knots` or `warmth` |
| `difficulty` | `easy`, `medium` or `hard` |
| `time` | About how long it takes, for example `10 minutes` |
| `needs` | What you need, one `  - item` per line |
| `warnings` | Safety warnings, one per line. Required for `light`, `fire`, `cooking` and `warmth`. |
| `summary` | One line, up to 160 characters |

The other fields work the same as on a quick card. A skill has 2 to 10 steps.

**Pictures:** a step may start with one picture line,
`![What the picture shows.](file.svg)`. The words in the brackets are read
aloud to people who cannot see the screen, so describe the picture. Every file
in the folder must be used by a step.

### Drawings

Drawings are simple line art, like the app's icons. The app draws them in its
own colors, so they look right in the dark theme.

- An `.svg` file, under 40 KB, with `viewBox="0 0 240 160"`.
- Only `<path>` elements, plus an optional `<title>`. No text, images,
  gradients, scripts or links. Turn text into paths, or leave it out.
- Use lines and curves only (path commands M, L, H, V, C, S, Q, T, Z). No arcs
  (`A`): draw a circle with four curves. Most drawing apps export curves already.
- Draw with strokes, about 3 units wide. Set the look on the `<svg>` element so
  the file previews well on GitHub:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 160"
     fill="none" stroke="#1C1F1A" stroke-width="3"
     stroke-linecap="round" stroke-linejoin="round">
  <title>A gallon jug filled with water</title>
  <path d="M84 52 h72 v92 h-72 z"/>
  <path class="water tint" fill="#2B7BB9" fill-opacity="0.25" stroke="none" d="M86 80 h68 v62 h-68 z"/>
  <path class="water" d="M86 80 h68"/>
  <path class="thin" stroke-width="1.2" d="M92 60 v80"/>
  <path class="accent" d="M120 20 v14"/>
</svg>
```

- A path with no class is a main line. A `class` changes it, with at most one
  color and at most one kind:
  - Colors: `accent` (amber: a flame, a light, the thing to look at) or
    `water` (blue).
  - Kinds: `thin` (a fine detail line: texture, folds, grain, ripples),
    `solid` (filled instead of stroked) or `tint` (a soft see-through fill for
    shadows, water, glow and shading).
  - For example: `class="thin"`, `class="accent tint"`, `class="water thin"`.
- Draw tints first, so the lines sit on top of them. The app draws paths in
  file order.

## Check your work

```bash
python -m pip install -r scripts/requirements-dev.txt
python scripts/check_content.py
python -m pytest -q
```

`check_content.py` explains each problem in one sentence. The test
`test_every_card_on_main_has_passed_medical_review` stays red while a card is
a draft. That is expected: it turns green after review.

## What happens after you open a pull request

1. The `validate` check runs the same checks as above.
2. A maintainer reads it, and may ask for changes.
3. Medical content goes to a clinician. Other content is checked against its
   source.
4. The maintainer sets `status: reviewed` and the date, and merges.
5. The next Core pack release carries it to every phone.
