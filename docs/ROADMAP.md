# Swipe Life — Roadmap: birth to death

Goal: the full game in GDD §1–§12 — one life from birth to death (§5), adult careers, family, old age, legacy
(§9.3) and replay (§9.1–9.2), about 300 cards (§12.3), on Android.

Stage 1 (M0–M6, careers) built the first playable, birth to 18. Stage 2 (M8–M13) builds adult life to death.
**Balance comes last** (director, 2026-11-03): no tuning until the game is fully featured, or we tune numbers
that will change. Until then the sim checks only for bugs (stuck lives, unreachable cards), not numbers.

Rules for every milestone:
- Each milestone is its own branch and PR to `main`, and CI must be green.
- Exit criteria are things the director sees on the phone or in a capture.
- The GDD wins over this file. If they conflict, ask the director.

## Status (2026-11-05) — start here
| Milestone | State |
|---|---|
| M0 Foundations | Done (#9) |
| M1 Card engine | Done (#10) |
| M2 Swipe UI and stats | Done (#11) |
| M3 Life rules | Done (#12) |
| M4 Between-year menu | Done (#13) |
| M5 Clay home scene | In progress (#16, #18, #20, #22, #23, #29, #32, #39, #40, #44, #45, #47): dollhouse one room at a time, modular clay people. Exit (director approves captures per age band) not met yet. |
| M6 ~200 cards | Done (#28, #31): 343 cards across every age band; the 1,000-life sim draws every age-band card. |
| Careers, teen phase (§6.8) | Done (#17, #19, #21, #24, #25): Career menu, 12 careers, 120 work and juvie cards. |
| M7 Teen release candidate | Phone build only: internal-testing AAB, director plays birth to 18. Balance moved to M13. |
| Personality spectrums (§4.6) | Done (#49): Cautious/Risk-taker and Introvert/Extrovert sliders; cards gate on them and `by_trait` scales outcomes. |
| M8 Adult life core | Done (#58, #59): lives run past 18. Shop items moved to M11. |
| M9 Adult home scene | In progress: eight homes, scene follows housing. |
| M10, M12–M13 | Not started. |
| M11 Ageing and death | Old age death rule in (§5.3c). Grey hair, wrinkles and late-life cards not started. |

Open with the director:
- Card rewrites: round 1 applied (#51). Further rounds come from the card doc
  (https://claude.ai/artifact/5PhAQ7UdkN8LpayG6EACjr); copy them into `data/cards/sample.json`.
- The 9 actions in `data/actions/actions.json` are placeholders, also open for rewrite.

Where the code lives:
- Rules: `scripts/cards/` (`card_db.gd` loader/validator, `deck.gd`, `life_rules.gd`). State and save: `scripts/autoload/`.
- Menu: `scripts/menu/action_db.gd`, `scripts/ui/year_menu.gd`. Main loop: `scripts/main.gd`.
- Clay cut-out art pipeline: `tools/blender/build_clay_girl.py --cutout`, `tools/blender/render_cutouts.py`,
  `shaders/clay_cutout.gdshader`, demo `scenes/proto/clay_cutout.tscn`.
- Modular people (`docs/PEOPLE.md`): Blender `tools/blender/people/` (`body.py`, `render.py`, `clip.py`),
  sprites in `assets/people/<shape>/`, clips in `assets/people/clips/`, `scripts/people/person.gd`,
  `shaders/person_clay.gdshader`, demo `scenes/proto/person_slice.tscn`.

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
- Progress (2026-11-05, hair merged in #47):
  - Done: blush on babies and children only. Even grey hair tint. Symmetric bust; the director approved the size.
    Necks grow with age (child, then teen, then adult). Men broader, women hourglass, fitted tops.
    Arms set away from the torso. Flat adult and teen shoulders, approved by the director.
  - Hair: 33 cuts on 6 shapes merged (#47); about 14 rebuilt on the new body, the rest older versions.
    Open flaws: forehead rim, side lobes, short cuts look alike, ribbed long hair, stuck-on buns and braids.
  - Elderly: face lines, grey hair and a slight stoop on the adult body.
  - Left to do: clothes over the new shoulders, rebuild the remaining hair cuts and fix the flaws the
    director names, baby pacifier.

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

## M7 Teen phone build
- Build a signed AAB with the existing CI signing setup and install it through internal testing.
- **Exit:** the director plays a full life, birth to 18, on the phone. No balance pass (that is M13).

## M8 Adult life core (18+)
- `CardDB.ADULT_LIFE` is on (director, 2026-11-09): lives run past 18 with money, housing, debts, courses, adult
  jobs and adult work cards (docs/ADULT_MONEY.md).
- Shop items moved to M11 (director's split, 2026-11-04).
- Remove the stop at 18: the year loop runs on, 4 cards a year (§2.5), until death (§5).
- Shop tab opens at 18 (§6.7): houses, cars, furniture and items (§6.1), each with a price in data.
- Adult careers on the careers data (§6.8 "adult careers come later"), and courses on the Job board (§6.4).
- Adult card bands 18–24, 25–39 and 40–59 (director, 2026-11-09), written like M6 (a readable list per band before merge).
- **Exit:** a life plays past 18 into the 30s; buying a house and holding an adult job work in the sim.

## M9 Adult home scene
- Director's scope (2026-11-09): eight home looks, the rental and each house in `data/property/houses.json`,
  four rooms each. The scene follows `GameState.housing`; the parents' home keeps the teen rooms.
- Bought items placed in rooms move to M11. Adult and partner figures move to after M5's clothes and hair.
- **Exit:** the director approves captures of each home.

## M10 Relationships and family
- People tab for adults (§6.3): talk, gift, date, argue.
- Partners, children and family members as characters in the life (§9.3 lists siblings and the other parent).
- **Exit:** a life can find a partner and have a child, seen in the sim and in a capture.

## M11 Ageing and death
- Old age death: chance rising each year from about 70 (§5.3c). Done: `LifeRules`, 2% at 70 then +2% a
  year (placeholder until M13); healthy lives die at median 77. Takes effect once M8 removes the stop at 18.
- Ageing details on people: grey hair, wrinkles, baldness (§10.7).
- Remaining cards to the ~300 launch target (§12.3), including late-life bands.
- **Exit:** the 1,000-life sim shows natural deaths spread from 70 onward and no stuck lives.

## M12 Legacy and replay
- Legacy (§9.3): continue as your child with money minus a tax, the house and items, some traits and family.
- Achievements / ribbons (§9.1) and unlockable careers, backgrounds and card sets (§9.2).
- **Exit:** the director dies in one life and plays on as the child, keeping the house; ribbons show.

## M13 Balance and release candidate
- Balance pass over the whole life using the sim's numbers (only now, with every feature in).
- Signed AAB through internal testing.
- **Exit:** the director plays full lives, birth to death and into a legacy, on the phone and signs off.

## Stage 2 decisions (GDD §6.9, director 2026-11-03)
- Every common real-world job; university and trade courses gate the jobs that need them (M8).
- Rent or buy, mortgages and debt (M8, scene in M9).
- Dating apps, social events, card events; marriage, divorce, infidelity, children (M10).
- Still to ask when each milestone starts: the adult menu actions per tab and their age ranges.

## Out of scope
Monetisation (§11), until the director decides.

## Order
- Critical path: M1 → M2 → M3.
- M4 starts after M2.
- M5 (art) runs alongside M1–M4.
- M6 writing starts once the director approves the M1 schema.
- M7 can ship any time after M5.
- Stage 2: M8 → M9 and M10 (in parallel) → M11 → M12. M13 comes last.
