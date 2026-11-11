# Balance audit (M13)

Tools: `tools/audit/card_audit.py` (static, all 592 cards), `tools/audit/run.sh lives reps strategies`
(runs `tools/godot/feature_audit.gd`: five play strategies and every career). ~1 minute per 200 lives.

## Fixed in this pass
- **Job stress pinned every adult at 100.** Ranks add 8–15 Stress a year against -2 recovery, so any
  employed adult sat at Stress 100 and anxiety, `friends` and `parents` meant nothing. Rank Stress is now
  a quarter of the data value (`CareerRules._year`). Stress at 40 now separates play: greedy 54, random 90,
  worst 99 (was 100 for all).
- Test margin "careful vs never-rest lives" is now +10 years (the gap is 15; resting still matters).

## Findings, not changed (director's call or content work)
1. **Choices barely move the outcome.** Greedy, random and worst swipe strategies all die at p50 76–78 and
   leave an estate of 1.3–1.4M. Lifespan comes from the menu (doctor, friends), not the cards.
2. **Money runs away.** Estate p50 1.3M, p95 3–6M. Every career reaches its top rank within 40 years
   (95–100%) when the player works hard when Performance is under 60; nobody is fired. `corporate` needs
   nothing and pays 30k → 900k over 5 ranks (421k a year averaged over a career).
3. **25% of cards have a better swipe.** 148 of 592 cards have one side that is at least as good on every
   stat (no risk or flag on it). Run `python tools/audit/card_audit.py` for the list. They need a trade-off
   written in, card by card.
4. **Teen special careers pay nothing** (afl, basketball, musician ~$4–9 a year; formula1 −144). Fame
   paths pay only at the top.
5. Flags `gifted` and `juvie_studied` are set by cards and never read.
