# Swipe Life — Game Design Document

**This is the bible.** Every session reads it before gameplay, content, UI or art work.

## 0. How to use this document

- 0.1 Every decision here was made by the director. Build exactly what it says.
- 0.2 If a task conflicts with this document, stop and ask the director. Do not pick a side yourself.
- 0.3 If something is not covered here or is listed in §13 Open questions, ask the director. Never fill a gap
  with your own design and never mark an open question as decided.
- 0.4 Only the director changes decisions. When they do, update the section and add a line to §14 Change log.
- 0.5 Cite rules by number in commits, PRs and questions (e.g. "GDD §3.2").

## 1. Pitch

- 1.1 Swipe Life is a life and career simulator for Android. You live one person's life from birth to death by
  swiping decision cards: left, right, or up.
- 1.2 Inspirations for the *type* of play: BitLife (life simulation) and Reigns (swipe decisions).
- 1.3 Never copy either game: no cards, text, characters, UI layouts, stat names used as their identity, or
  systems taken from them. If an idea is recognisably theirs, drop it.

## 2. Core loop

- 2.1 One year of life = 4 decision cards, one per quarter (each card stands for 3 months).
- 2.2 After the 4th card, the between-year free-actions menu opens (§6).
- 2.3 Leaving the menu ends the year: age +1, and the next year's first card is dealt.
- 2.4 Repeat until the life ends (§5).
- 2.5 Childhood uses the same rhythm from age 0: 4 cards per year. Baby and toddler cards are simple, often
  funny choices (e.g. cry or nap).

## 3. Swipes

- 3.1 Each card shows a situation and two choices. Swipe left = one choice, swipe right = the other.
- 3.2 Swipe up = **super like**: a bolder version of a choice with a bigger reward and a bigger risk.
- 3.3 The player gets **one super like per year**.
- 3.4 Super-like outcomes are card-specific: each card's data defines its own super-like result and its own
  risk. There is no global multiplier.

## 4. Stats

- 4.1 A life tracks these stats: Health, Happiness, Money, Career/Skills, Relationships, Smarts, Looks,
  Karma/Reputation, Stress.
- 4.2 The list is open: the director may add more.
- 4.3 Every stat except Money is a 0–100 bar. Money is a plain number. Children get pocket money each year:
  $10 from age 6, $20 from age 10.
- 4.4 Karma/Reputation is hidden from the player. All other stats are visible.
- 4.5 Stress rises from activities (§6.5). High Stress or low Happiness can cause mental illnesses, which are
  very sticky. Checked at each year end from age 6:
  - Anxiety: starts when Stress ≥ 70, chance 10% + 1% per point above 70. Each year: Stress +5, Health −3.
    Lifts with a 15% chance per year, only while Stress < 40.
  - Depression: starts when Happiness ≤ 30, chance 10% + 1% per point below 30. Each year: Happiness −5,
    Health −3. Lifts with a 15% chance per year, only while Happiness > 60.
- 4.6 Two personality spectrums, each one visible slider (director, 2026-11-05):
  Cautious ↔ Risk-taker (`boldness`) and Introvert ↔ Extrovert (`sociability`), 0–100.
  - A new life starts each at a random 40–60. Only swipe choices move them.
  - They gate which cards appear (`requires.stats`) and change stat outcomes (`by_trait`,
    `docs/CARD_SCHEMA.md`). They never change risk or death odds.

## 5. Life span

- 5.1 A life starts at birth.
- 5.2 A life ends by natural old age, or earlier through risky choices and events.
- 5.3 Three ways to die:
  (a) Health reaching 0;
  (b) rare deadly outcomes on risky cards (set per card in its data);
  (c) old age, with the chance of death rising each year from about age 70.

## 6. Between-year free actions

- 6.1 Shop / assets: buy a house, car, furniture and other items. Bought items appear in the scene (§10).
- 6.2 Activities: e.g. gym, doctor, holiday, study; spend money to change stats.
- 6.3 People: talk to, gift, date or argue with characters in your life.
- 6.4 Job board: apply for jobs and courses.
- 6.5 The menu allows 3 actions per card turn from age 13 (12 per year, one per month); 2 per turn
  aged 6-12 (8 per year) and 1 per turn under 6 (4 per year). Same in old age. The budget refills each
  birthday. Free actions would otherwise loop for ever. Moving money (savings, investments, debt),
  navigation and browsing places are free; doing things costs actions. (Director, 2026-11-12)
- 6.6 Balance: effort, fear and conflict add Stress; that is their time cost (there is no time budget). Fun
  and rest (toys, friends, family, treats) lower it, on actions and card choices alike. Repeating effort in
  one year piles up Stress (and the illness risk of §4.5), so buying stats every year has a price beyond money.
- 6.7 The menu is age-gated: options unlock as the character grows (a baby has almost none; the full menu is
  open by 18). Tabs unlock at: Activities 5, People 10, Jobs 14, Shop 18. Each action also has its own age range
  inside its tab (e.g. crushes from 14). Actions live in `data/actions/*.json`.
- 6.8 Careers (teen phase, ages 14–17; spec in `docs/CAREERS.md`). The Jobs tab is the **Career** menu, with
  submenus to advance your standing, deal with staff and look for other work; drama arrives as cards.
  - You hold at most one regular job and one special career at a time.
  - Each career has four named coworkers: boss, rival, crush and friend.
  - Special careers: AFL, Formula 1, Basketball, Musician, Actor, Gangster, Pro Skater, eSports and Head of State (army and cop dropped; Head of State is adult-only; eSports is a generic title, no real game).
  - A gang arrest sends you to juvie and gives you a criminal record; any record can be expunged later (director, 2026-11-04).
  - A partner met at work stays your partner after the job ends; a breakup ends the partner.
  - Adult careers come later on the same data.
- 6.9 Adult life (director 2026-11-03):
  - Careers: basically every common real-world job. Education gates careers: university and trade courses
    unlock the jobs that need them (e.g. doctor needs university).
  - Housing: rent or buy; buying takes a mortgage, and debt is possible. Money rules: docs/ADULT_MONEY.md.
  - Love and family: dating apps, meeting people at social events, and card events; marriage, divorce,
    infidelity and children.

## 7. Setting and tone

- 7.1 Generic world, no specific country: no named currency, school system, laws or real places.
- 7.2 Tone is mostly grounded, with occasional absurd or funny cards.
- 7.2a Dark comedy (director 2026-11-04): the cute clay art against the brutal realities of life is the game's niche. Cards may be darkly funny; under-18 sensitive-content rules still apply.

## 8. Session length

- 8.1 One full life is long: 30+ minutes.
- 8.2 A life can be saved and resumed mid-life.
- 8.3 The game autosaves once per year, when the between-year menu closes. There are no manual save slots.

## 9. Replay

- 9.1 Achievements / ribbons for outcomes and life summaries.
- 9.2 Unlockable content earned by past lives: careers, backgrounds, card sets.
- 9.3 Legacy: after death, continue as your child, inheriting from the parent:
  money (minus a tax), the house and its items, some traits (e.g. Looks, Smarts, Health), and family
  relationships (siblings, the other parent).
- 9.4 Open for more replay ideas from the director.

## 10. The scene (tamagotchi view)

- 10.1 The screen shows an isometric view of the character's home with the rooms visible, like a dollhouse.
- 10.2 The scene changes live in response to decisions and purchases (e.g. new furniture, a partner moving in,
  a bigger house).
- 10.3 Style: a toon look with lots of personality, made entirely by Claude Code (no artist, no bought assets).
  Free base meshes are allowed and clay-ified (director, 2026-11-04): CC0 from Kenney (Furniture, Car, City
  Suburban, Building Kit), poly.pizza and Poly Haven; CC-BY only where CC0 lacks an item, with a credits
  screen (M11). Each download is asked first.
- 10.4 Chosen style (director, 2026-11-03): flat 2D **clay cut-outs**. Clay pieces are modelled and lit in
  Blender, prerendered to PNGs, and turned on pivots in Godot, posed at 24 fps with a clay boil shader on twos (12 fps).
  Motion is copied from proven clips (e.g. Mixamo), never improvised.
- 10.5 Screen layout (portrait): the dollhouse fills the top ~45%, a strip of stat bars sits below it, and
  the card fills the bottom half.
- 10.6 Childhood home (ages 0–17, director 2026-11-03): a 2x2 cutaway of four rooms: bedroom, living room,
  kitchen, bathroom. The dollhouse shows one room at a time at full scale; the camera moves between rooms
  (director 2026-11-03). Each card names its room (`room`, default bedroom); the view slides across the
  house to it (~0.4 s). The bedroom's age bands: baby 0–3, child 4–12, teen 13–17.
- 10.7 The player is a girl or a boy, set at birth. People are **modular, like Lego** (director 2026-11-03):
  every person is assembled from interchangeable parts.
  - Body: 4 age sizes (baby, child, teenager, adult); a female and a male shape; from child up, tall or short
    and fat, skinny or athletic (the baby has one body).
  - Clothing mixes and matches with no gender constraints. Slots: top, bottom, shoes, full-body (replaces top
    and bottom, e.g. onesie, dress), outerwear over the top, headwear, glasses.
  - Any item and hair can be any colour: parts are rendered once in neutral clay and tinted in game.
  - Also modular: haircuts, facial hair, skin tones, eye and brow shapes, ageing
    details (grey hair, wrinkles, baldness), body extras (freckles, scars, tattoos).
  - Skin tone is genetic (director 2026-11-03): a child's tone blends both parents' tones plus a little
    randomness (black and white parents make a light brown baby; light brown and white, a very light brown one).
    Skin tone and ethnicity have no other gameplay effect: no stat, card, chance or sim tendency depends on them.
  - A look is inherited from the parents plus randomness, and improves with lifestyle (e.g. becoming
    athletic through exercise, plastic surgery). Attractiveness is the Looks stat (§4.1), not a separate part.
  - The game is fully LGBTQ+ friendly (director): a partner can be any sex, whatever the player's sex.
  - The player picks their whole look at the start of a life (director 2026-11-09).
  - People are real 3D figures living inside the rooms at room scale, seen from any angle, doing everyday things (director 2026-11-09; replaces front-view only).
  - Architecture: `docs/PEOPLE.md`.
- 10.7b Life shows in the scene (director, 2026-11-12): cards and actions feed the visuals directly. Examples: a
  punk musician gets band posters on the wall and maybe a mohawk; a trophy won appears on her bookshelf; losing a
  limb shows on the character. Every career, win, injury and big card outcome should map to a visible change on
  the person or the house. Needs a mapping table (event/flag -> prop or body part); see docs/ROADMAP.md.
- 10.8 Before 18 (Shop locked, §6.7) the scene changes with age (e.g. crib → bed → desk) and with activities,
  which leave props in the house (e.g. a ball from the sports club, books from studying).

## 11. Monetisation

- 11.1 Decided later. No system may depend on ads or purchases until the director decides.

## 12. Technical rules

- 12.1 Godot 4.7.2, Android, portrait 720×1280, touch-first (mouse emulates touch in the editor).
- 12.2 Cards, events, items and activities live in JSON data files, not hard-coded in scripts. The exact
  schema is in `docs/CARD_SCHEMA.md` (approved 2026-11-03).
- 12.3 Launch target: about 300 cards. The first playable (birth to 18, `docs/ROADMAP.md`) has about 200
  cards for ages 0–17.
- 12.4 Repo conventions are in `CLAUDE.md` (branches, PRs, CI, LFS, no keystores in git).

## 15. Stage 3 direction (director interview, 2026-11-12)

Audience: the director only for now (itch web + APK each milestone). Rating Mature 16+; nothing off-limits
if handled with taste. The game is firmly anti-fascist, anti-sexist and anti-bigotry; faith and voting exist.
English only for now. I decide content; the director reviews.

- 15.1 Order: polish and feel first, starting with the swipe. Biggest weakness: the scene looks flat.
- 15.2 Swipe feel: the card bends like heavy clay while dragged; stat icons preview the change on drag;
  haptics; the super swipe gets a big moment (card flies up, burst, slow-mo, sound sting).
- 15.3 Feedback: the character reacts (cheer, sulk, wince), stat bars animate, numbers float. The year turns
  with a calendar flip. Cards get richer text (two to three lines).
- 15.4 Places: home, workplace (office and law, trades and service first), school, town street. Cards move
  you to their place; menu actions let you pick one. Browsing places is free.
- 15.5 Home: room switching (bedroom, lounge, kitchen, garage). Bought items auto-fill fixed slots; the player
  can swap which item fills a slot (a bought car in the driveway, a couch in the lounge). House size and type
  and furniture quality follow money. Pets appear when acquired.
- 15.6 Life shows in the scene (§10.7b): career props, trophies and wins, body changes, relationships and kids.
  Changes fade over years (posters come down after the career). Build a full set per category, then show it.
  Injuries are realistic but soft (casts, scars, wheelchair, missing limb).
- 15.7 Character: chosen at birth (gender and pronouns, any; skin, hair, eyes; name; birthplace and family).
  Looks change by shop (wardrobe, hair, tattoos) and by cards. Outfits follow context (work clothes at work,
  pyjamas at night). Ages visibly every year, gradually.
- 15.8 People: every named person is an on-screen clay character with a visible bond meter, living their own
  life (friends marry, parents age and die, rivals succeed). Grunts and reactions, no speech.
- 15.9 Family background (rich, poor, country, parents) changes gameplay strongly.
- 15.10 World: about 15 countries to start, with local cards and laws (driving, drinking, school ages, legal
  outcomes). Move country through cards and actions. Languages are learnable and gate jobs abroad.
- 15.11 Fame: a new stat with 6 tiers (local, rising, known, famous, star, icon), each with its own card set.
  It unlocks cards, boosts income, shows in the scene (fans, magazine covers) and lasts after death.
  Infamy is a separate stat from crime and scandal, with its own cards.
- 15.12 Content: about 1,000 cards. Cards chain over years: multi-year story arcs and loose callbacks.
- 15.13 Play time: 15 minutes rushed, 2-3+ hours taking time. Slow play comes from optional activities (visit
  places, shop, decorate, talk to people) and mini-games (job shifts, school tests, sport, music and stage).
  Mini-games are always skippable (auto-resolve by stats); skill gives only a small bonus.
- 15.14 Achievements: hundreds; common ones visible, rare ones secret with hints.
- 15.15 Endings: darkly comic stop-motion death scenes, then a life recap scene (house and body as they ended,
  a short story), shareable as an image.
- 15.16 Legacy: optional. After death, play on as an heir at their current age, or start over. A will can be
  written any time (an action) and edited at death; it decides who gets money and house and belongings.
  Family reputation and relationships carry over. One life at a time (autosave).
- 15.17 Audio: music changes with life stage, career and mood, made with Suno (I operate it in Chrome).
  SFX: clay foley for UI, ambience per place; SFX and grunts from ElevenLabs. Existing credits on both
  accounts may be used freely; ask before buying more.
- 15.18 UI: full clay redesign of the year menu and stats.

## 13. Open questions (ask the director; do not decide)

None.

## 14. Change log

- 2026-11-02: Document created from the director's answers (§1–§12).
- 2026-11-02: Answered open questions: childhood (§2.5), super like (§3.4), stats (§4.3–4.5), death (§5.3),
  activity balance (§6.6), autosave (§8.3), legacy (§9.3), layout (§10.5), JSON + ~300 cards (§12.2–12.3).
- 2026-11-03: Art style picked: 2D clay cut-outs (§10.4). Age-gated menu (§6.7). First playable = birth to 18
  with ~200 cards (§12.3, `docs/ROADMAP.md`).
- 2026-11-03: Card JSON schema approved (§12.2, `docs/CARD_SCHEMA.md`).
- 2026-11-03: Mental illness rule and numbers (§4.5).
- 2026-11-03: Menu unlock ages (§6.7) and Stress as the time cost (§6.6); §13.1 closed.
- 2026-11-03: Childhood home rooms (§10.6), girl or boy at birth (§10.7), pre-18 scene changes (§10.8).
- 2026-11-04: Tone: pretty dark-comedy, cute art vs brutal life (§7.2a).
- 2026-11-04: Special careers add Pro Skater, eSports and Head of State (§6.8, director).
- 2026-11-03: Dollhouse shows one room at a time, camera moves between rooms (§10.6).
- 2026-11-05: Personality spectrums: Cautious/Risk-taker, Introvert/Extrovert (§4.6).
- 2026-11-03: Card picks the room, slide pan, bedroom age bands 0–3 / 4–12 / 13–17 (§10.6).
- 2026-11-03: Modular people (§10.7): body sizes, shapes, mix-and-match clothing slots, tinted parts, extras; looks inherited + random, improved by lifestyle.
- 2026-11-03: Teen careers (§6.8): career menu, one job + one special, named coworkers, six specials, juvie
  and a permanent record, work partners carry over, breakups end the partner.
- 2026-11-03: Career and work-card Stress cut by 25%; a free job is open even in debt.
- 2026-11-03: Fun relieves Stress (§6.6): toys -3, friends -3, parents -2; pure-fun card choices -2.
- 2026-11-03: M7 balance: pocket money (§4.3); card Happiness gains halved; F1 open to the richest ~10% of
  teens ($140); yearly performance drift -12..+10 and firing at 30 or less; gang unchanged.
- 2026-11-03: Adult life (§6.9): every common job, education gates careers, rent or buy with mortgages,
  dating apps, social events, marriage, divorce, infidelity, children. Balance comes last (`docs/ROADMAP.md`).
- 2026-11-03: Skin tone blends the parents' tones (§10.7); it has no gameplay effect beyond genetics.
- 2026-11-04: Adult framework: CardDB age cap lifted now behind a feature flag; entry adult salary $30,000/yr
  (all adult prices scale from it); adult content rated Mature 16+; adult systems split M8 money + careers,
  M10 relationships + health, M11 possessions + retirement.
- 2026-11-04: Director answered the adult-life proposals (romance, friendship, illness, finances, retirement,
  possessions, careers); answers in docs/proposals/DECISIONS.md until each GDD section is written.
- 2026-11-04: §6.8: every criminal record, gang records included, can be expunged (was permanent).
- 2026-11-04: §10.3: approved CC0 asset sources and CC-BY with credits; §6.8 change above. Further answers in DECISIONS.md.
- 2026-11-09: M8 money placeholders in docs/ADULT_MONEY.md stand until balance (M13).
- 2026-11-09: Adult life turned on: lives run past 18 to death (§5).
- 2026-11-09: M9 is the homes only (§10.2): bought items move to M11, adult and partner figures to after M5's clothes and hair.
