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
- 4.3 Every stat except Money is a 0–100 bar. Money is a plain number.
- 4.4 Karma/Reputation is hidden from the player. All other stats are visible.
- 4.5 Stress rises from activities (§6.5). How stats affect each other beyond the rules in this document:
  ask the director.

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
- 6.5 There is no action limit per year; money is the only limit.
- 6.6 Balance: each activity costs time and adds Stress or has another downside, so buying stats every year
  has a price beyond money.

## 7. Setting and tone

- 7.1 Generic world, no specific country: no named currency, school system, laws or real places.
- 7.2 Tone is mostly grounded, with occasional absurd or funny cards.

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
- 10.4 The style is chosen by test: build the same one-room prototype twice,
  (a) 3D cel-shaded (simple models, 2–3 tone toon shading, ink outlines) and (b) 2D flat vector.
  Show the director screenshots of both; the director picks. Until then no other scene art is made.
- 10.5 Screen layout (portrait): the dollhouse fills the top ~45%, a strip of stat bars sits below it, and
  the card fills the bottom half.

## 11. Monetisation

- 11.1 Decided later. No system may depend on ads or purchases until the director decides.

## 12. Technical rules

- 12.1 Godot 4.7.2, Android, portrait 720×1280, touch-first (mouse emulates touch in the editor).
- 12.2 Cards, events, items and activities live in JSON data files, not hard-coded in scripts. The exact
  schema is proposed to the director by the first card-system task.
- 12.3 Launch target: about 300 cards.
- 12.4 Repo conventions are in `CLAUDE.md` (branches, PRs, CI, LFS, no keystores in git).

## 13. Open questions (ask the director; do not decide)

1. Art style pick after the §10.4 prototypes.
2. The JSON card schema (§12.2), once proposed.

## 14. Change log

- 2026-11-02: Document created from the director's answers (§1–§12).
- 2026-11-02: Answered open questions: childhood (§2.5), super like (§3.4), stats (§4.3–4.5), death (§5.3),
  activity balance (§6.6), autosave (§8.3), legacy (§9.3), layout (§10.5), JSON + ~300 cards (§12.2–12.3).
