# Careers (teen phase, ages 14–17)

Director decisions, 2026-11-03:
- Teen jobs come first; adult careers come later, built on the same data.
- At once you hold at most **one regular job plus one special career**.
- Each career has four named coworkers: boss, rival, crush and friend.
- A **career menu** with submenus is where you advance your standing, talk to staff and look for other work. Cards bring the drama.
- A gang arrest sends you to **juvie** and gives you a **criminal record**.
- A partner you meet at work **stays your partner** after the job ends.
- The special careers are AFL, Formula 1, Basketball, Musician, Actor and Gangster.

## Data: `data/careers/*.json` (validated by `CareerDB`)
| key | meaning |
|---|---|
| `id`, `label` | unique id, display name |
| `kind` | `job` (regular slot) or `special` (special slot) |
| `ages` | `[min, max]` |
| `requires` | `{stats:{s:[min,max]}, flags:[], not_flags:[]}`, same as cards; e.g. `not_flags:["criminal_record"]` |
| `cost` | money paid on joining (gear, club fees, kart) |
| `meter` | specials only: `fame`, `heat` or `fitness` (0–100) |
| `ranks` | `[{title, pay, stress, promote_at}]`; `pay` < 0 is a running cost; the top rank has no `promote_at`; every rank adds stress (GDD §6.6) |

## State (`GameState`, saved)
- `careers`: maps a slot (`job` or `special`) to `{id, rank, titles, performance, years, meter, coworkers}`.
- `coworkers`: maps each role to `{name, affinity -100..100}`.
- `partner`: `{name, affinity, met}`. It is `{}` when you're single.
- Story flags for a career start with `work_<slot>_` and are cleared when you leave it.

## Rules (`CareerRules`)
- **Promotion** is asked for from the career menu. It succeeds when performance has reached the rank's `promote_at`. Asking too early costs you performance and the boss's goodwill.
- **At year end:** each career pays its rank's pay, adds stress, raises the career stat and drifts performance by -8 to +12 plus a career-stat bonus.
- **Firing:** performance of 15 or less at year end gets you fired (flag `fired`).
- **Gang career:** heat rises by 6 per rank each year, and the chance of arrest is heat × 0.5%. An arrest ends the career and sets the flags `juvie` and `criminal_record`.

## Cards
These keys are added to the card format (`docs/CARD_SCHEMA.md`).

**`requires.job`** says which career a card is about. It can be:
- a career id
- a slot (`job` or `special`)
- `any`

It can be narrowed with:
- `requires.rank`: `[min, max]`
- `requires.coworker`: `{role: [min, max] affinity}`

The card then acts on the slot that matched.

**Choice keys:**
- `coworker`: `{role: affinity delta}`
- `partner`: `"end"`, also allowed inside `risk` (a breakup: you are single again and `dating_work_partner` is cleared)
- `job`: `{performance, rank, meter, date: true (the crush becomes your partner), leave: "<flag>"}`

**Text placeholders:** `{boss}` `{rival}` `{crush}` `{friend}` `{job}` (the current title) and `{partner}`.
