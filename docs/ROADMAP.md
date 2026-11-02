# Swipe Life — Roadmap to the first playable (birth to 18)

Goal: a **playable Android APK** that covers one life from birth to 18. It includes the cards, the stats, the age-gated
between-year menu (GDD §6.7), the clay cut-out home scene (§10.4) and autosave (§8.3). At 18 the life ends on a
"to be continued" summary. The deck holds about 200 unique cards for ages 0–17 (§12.3). One life draws 76 of
them (19 years × 4).

Rules for every milestone:
- Each milestone is its own branch and PR to `main`, and CI must be green.
- Exit criteria are things the director sees on the phone or in a capture.
- The GDD wins over this file. If they conflict, ask the director.

## M0 Foundations
- Merge or close PR #7. Either way, keep the clay cut-out pipeline: `tools/blender/build_clay_girl.py --cutout`,
  `tools/blender/render_cutouts.py` and `shaders/clay_cutout.gdshader`.
- Add the autoloads `GameState` (stats, age, quarter, flags, super like) and `SaveSystem`.
- Add the data folders `data/cards/` and `data/actions/` (§12.2).
- **Exit:** CI is green, and the APK boots to an empty three-region layout (§10.5): dollhouse ~45%, stat strip,
  card.

## M1 Card engine
- Propose the JSON card schema to the director (§13.1). Fields:
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
- The director sets the unlock ages (§13.2). Example only: toys and pocket money at 5, clubs and study at 10, a part-time job and crushes at 14, everything at 18.
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
