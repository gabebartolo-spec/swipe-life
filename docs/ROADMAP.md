# Swipe Life — Roadmap to the first playable (birth to 18)

Goal: a **playable Android APK** that covers one life from birth to 18. It includes the cards, the stats, the age-gated
between-year menu (GDD §6.7), the clay cut-out home scene (§10.4) and autosave (§8.3). At 18 the life ends on a
"to be continued" summary. The deck holds about 200 unique cards for ages 0–17 (§12.3). One life draws 76 of
them (19 years × 4).

Rules for every milestone:
- Each milestone is its own branch and PR to `main`, and CI must be green.
- Exit criteria are things the director sees on the phone or in a capture.
- The GDD wins over this file. If they conflict, ask the director.

## Status (2026-11-03) — start here
| Milestone | State |
|---|---|
| M0 Foundations | Done (#9) |
| M1 Card engine | Done (#10) |
| M2 Swipe UI and stats | Done (#11) |
| M3 Life rules | Done (#12) |
| M4 Between-year menu | Done (#13) |
| M5 Clay home scene | In progress (#16, #18, #20, #22, #23): dollhouse one room at a time, modular clay people. Exit (director approves captures per age band) not met yet. |
| M6 ~200 cards | Done (#28, #31): 343 cards across every age band; the 1,000-life sim draws every age-band card. |
| Careers, teen phase (§6.8) | Done (#17, #19, #21, #24, #25): Career menu, 12 careers, 120 work and juvie cards. |
| M7 Release candidate | Not started. |

Open with the director:
- Card rewrites: the director may fill in the "Your rewrite" column of the card doc
  (https://claude.ai/artifact/GttfUkHETGzrYHbmESQvfS). Copy any rewrites into `data/cards/sample.json`.
- The 10 actions in `data/actions/actions.json` are placeholders, also open for rewrite.

Where the code lives:
- Rules: `scripts/cards/` (`card_db.gd` loader/validator, `deck.gd`, `life_rules.gd`). State and save: `scripts/autoload/`.
- Menu: `scripts/menu/action_db.gd`, `scripts/ui/year_menu.gd`. Main loop: `scripts/main.gd`.
- Clay cut-out art pipeline: `tools/blender/build_clay_girl.py --cutout`, `tools/blender/render_cutouts.py`,
  `shaders/clay_cutout.gdshader`, demo `scenes/proto/clay_cutout.tscn`.

How to run and check (Godot 4.7.2):
- Tests: `godot --headless --path . --script res://tests/run_tests.gd` (run `--import` first after new class_names).
- Lint before pushing: `gdformat` and `gdlint` (max line 100).
- Debug launch args after `--`: `--autoplay`, `--set=age=8,stress=95,...` (new life only; delete
  `%APPDATA%/Godot/app_userdata/Swipe Life/life.json` first or the save resumes).
- Capture frames: `--write-movie <dir>/f.png --fixed-fps 10 --quit-after 200 -- --autoplay`.

Builds:
- Android: CI workflow builds the debug APK and signed AAB (keystore kept outside the repo, never commit it).
- Web (itch.io): private Restricted page https://veniceissinking.itch.io/swipe-life, channel `html5`.
  Update: `godot --headless --path . --export-release "Web" build/web/index.html`, then
  `butler push build/web veniceissinking/swipe-life:html5 --userversion <ver>`. The director owns the butler login.

## M0 Foundations
- Merge or close PR #7. Either way, keep the clay cut-out pipeline: `tools/blender/build_clay_girl.py --cutout`,
  `tools/blender/render_cutouts.py` and `shaders/clay_cutout.gdshader`.
- Add the autoloads `GameState` (stats, age, quarter, flags, super like) and `SaveSystem`.
- Add the data folders `data/cards/` and `data/actions/` (§12.2).
- **Exit:** CI is green, and the APK boots to an empty three-region layout (§10.5): dollhouse ~45%, stat strip,
  card.

## M1 Card engine
- Card JSON schema (`docs/CARD_SCHEMA.md`, approved). Fields:
  - id, age range, weight;
  - conditions on stats or flags;
  - left / right / up choices, each with effects, a risk and a death chance (§3.4, §5.3b).
- Write a loader and validator, plus a CI check that fails on a bad card file.
- Build a deck that draws by age, conditions and weight, with no repeats within a life.
- **Exit:** about 10 sample cards play, and a headless test simulates 100 lives without errors.

## M2 Swipe UI and stats
- Card dragged by touch to the left, right or up, with a preview of the choice while dragging, and snap-back if released early.
- Super like, limited to one per year (§3.3).
- Stat strip showing the visible stats as bars and Money as a number. Karma stays hidden (§4.3–4.4).
- Year loop: 4 cards, then the menu, then age +1 (§2).
- **Exit:** on the phone, swipe through 3 years and see the stats change.

## M3 Life rules
- Death from Health reaching 0 and from risky cards (§5.3a–b). Old age does not apply before 18.
- Stress feedback, plus any stat interactions the director sets (§4.5, ask first).
- Autosave when the menu closes (§8.3), and resume on launch.
- Life summary screen, shown at death or at 18.
- **Exit:**
  - Killing the app mid-year resumes the game at the last year boundary.
  - A risky card can end a life.

## M4 Between-year menu (age-gated)
- Data-driven actions with age gates (§6.7) and their costs: money, time and Stress (§6.5–6.6).
- Tabs appear as they unlock: Activities, People, Shop, Job board.
- Unlock ages set by the director (GDD §6.7): Activities 5, People 10, Jobs 14, Shop 18.
- **Exit:** a 3-year-old sees almost nothing; a 15-year-old sees clubs, study and a part-time job.

## M5 Clay home scene
- Build an isometric dollhouse from prerendered clay cut-out pieces (§10.1, §10.4).
- Make 4 character sets: baby, child, teen and 18. Each gets idle motion and reactions copied from proven clips.
- Items bought in the menu appear in the scene (§10.2).
- **Exit:** the director approves captures at each age band. I check every frame before sending.

## M6 Content: about 200 cards, ages 0–17
- Write the cards in batches by age band: 0–2, 3–5, 6–9, 10–12, 13–15 and 16–17, about 30–40 cards per band.
- Tone is mostly grounded, with some absurd cards (§7.2). Settings are generic (§7.1). The cards are original
  writing.
- Each band goes to the director as a readable list before it merges.
- **Exit:** a headless sim of 1,000 lives shows that every card is reachable, no life gets stuck, and stat ranges
  stay sane.

## Careers, teen phase (ages 14–17)
- Data, rules and tests: `data/careers/`, `scripts/careers/`, spec `docs/CAREERS.md`.
- Career menu in the Jobs tab; work drama, romance, special-career and juvie cards in `data/cards/`.
- **Exit:** the sim holds at least 6 kinds of job across 100 lives and every career is reachable (tests).

## M7 Age-18 release candidate
- Balance pass using the sim's numbers.
- Build a signed AAB with the existing CI signing setup and install it through internal testing.
- **Exit:** the director plays a full life, birth to 18, on the phone and signs off.

## Out of scope before 18
Adult careers, old age (§5.3c), legacy (§9.3), achievements and unlocks (§9.1–9.2), monetisation (§11).

## Order
- Critical path: M1 → M2 → M3.
- M4 starts after M2.
- M5 (art) runs alongside M1–M4.
- M6 writing starts once the director approves the M1 schema.
- M7 comes last.
