# Card schema (approved 2026-11-03, GDD §12.2)

Cards live in `data/cards/*.json`. Each file holds an array of cards, usually one file per age band
(e.g. `data/cards/age_00_02.json`).

## Example

```json
{
  "id": "toddler_broccoli",
  "text": "Dinner is broccoli. Again.",
  "ages": [2, 4],
  "weight": 10,
  "requires": { "stats": { "health": [0, 100] }, "flags": [], "not_flags": [] },
  "left":  { "label": "Throw it",  "effects": { "happiness": 5, "health": -3 },
             "result": "It hits the dog. The dog is delighted." },
  "right": { "label": "Eat it",    "effects": { "health": 5, "happiness": -5 } },
  "up":    { "label": "Eat it all, ask for more", "effects": { "health": 10, "looks": 2 },
             "risk": { "chance": 0.2, "effects": { "happiness": -10 },
                       "result": "Stomach ache. Never again." } }
}
```

## Fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique, snake_case. Never reused, so it is safe to keep in saves. |
| `text` | yes | The situation shown on the card. |
| `ages` | yes | `[min, max]`, inclusive. The card can be drawn only at those ages. |
| `weight` | no (10) | Relative draw chance among eligible cards. A rare card is 1–3. |
| `requires.stats` | no | `{stat: [min, max]}`. Every listed stat must be in range. |
| `requires.flags` / `not_flags` | no | Flags that must be set or unset (e.g. `has_sibling`). |
| `left`, `right` | yes | The two choices (§3.1). |
| `up` | no | The super-like choice (§3.2, §3.4). If it is missing, the card cannot be super-liked. |
| `once` | no (true) | The card is drawn at most once per life. |
| `room` | no (`bedroom`) | Dollhouse room shown with the card: `bedroom`, `bathroom`, `living`, `kitchen` (GDD §10.6). |

Each choice has these fields:

| Field | Required | Meaning |
|---|---|---|
| `label` | yes | Short text shown while dragging. |
| `effects` | no | `{stat: delta}`. Money is in the game's unnamed currency (§7.1). |
| `set_flags` / `clear_flags` | no | Story memory, e.g. `"broke_arm"` unlocks later cards. |
| `result` | no | One line shown after the swipe. |
| `risk` | no | `{chance, effects, result}`. It applies on top of `effects` when it rolls. |
| `death` | no | `{chance, cause}`. A rare deadly outcome (§5.3b). |
| `by_trait` | no | `{spectrum: {stat: delta}}`, spectrum `boldness` or `sociability` (GDD §4.6). The delta is scaled by where the player sits: full at 100, none at 50, reversed at 0. E.g. `{"sociability": {"happiness": 6}}` cheers an extrovert, drains an introvert. |

## Validator rules (CI fails on any)
- The JSON must parse, and every required field must be present.
- Ids are unique across all files.
- Stat names must be in `GameState.STATS` (the 9 stats of GDD §4.1 plus the 2 spectrums of §4.6).
- `ages` is within 0–17 for now. Chances are within 0–1.
- No unknown keys, so typos are caught.
