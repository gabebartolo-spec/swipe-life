# Balance audit (M13)

Tools: `tools/audit/card_audit.py` (static, all 592 cards), `tools/audit/run.sh lives reps strategies`
(runs `tools/godot/feature_audit.gd`: five play strategies and every career). ~1 minute per 200 lives.

## Fixed in this pass
- **Job stress pinned every adult at 100.** Ranks add 8–15 Stress a year against -2 recovery, so any
  employed adult sat at Stress 100 and anxiety, `friends` and `parents` meant nothing. Rank Stress is now
  a quarter of the data value (`CareerRules._year`). Stress at 40 now separates play: greedy 54, random 90,
  worst 99 (was 100 for all).
- Test margin "careful vs never-rest lives" is now +10 years (the gap is 15; resting still matters).

- **Health now moves lifespan.** Doctor +3 Health (was +8, which pinned Health at 100), Health drift
  -2 from 40 and -4 from 75, old-age death shifted 1 year per 10 Health from 50. Careful swipes die at
  p50 80, random 78, worst swipes 73 (was 77, 77, 77).
- **Money.** Corporate pays 30k, 50k, 90k, 160k, 300k (was up to 900k). Income tax from 18 (15% over 30k,
  30% over 60k, 45% over 150k). The bank only lends a house loan while mortgage + upkeep fit in half of
  pay (`Finance.can_afford`; the house list shows the pay needed). Skill bonus to Performance is capped
  at +2. Top-rank rate within 40 years is 45–90% (was 95–100%). Estate p50 about 1.0M, a spender 0.75M.
- **Teen special careers** pay 20–200 a year (a part-time job pays 60–130); skater and esports pay an
  adult wage (12k–110k) past 18, they were paying 150 a year to adults.

## Still open
1. **25% of cards have a better swipe.** 148 of 592 cards: one side is at least as good on every stat
   (no risk or flag on it). `python tools/audit/card_audit.py` lists them.
2. **Super swipes cover 63 of 592 cards (11%).** None in the adult, 60+ or Dynasty sets; 2 of 92 special
   cards. Only 9 swipes carry death odds, one of them a super swipe. See `tools/audit/superswipe_audit.py`.
3. Flags `gifted` and `juvie_studied` are set by cards and never read.
