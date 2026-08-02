# P2 — the closing-line test

## The only question that matters

Not "is the model accurate?" but:

> Does the model predict better than the price the market is offering,
> after the bookmaker's margin is removed?

If no, every profit figure is noise. P2 answers this and nothing else.

## Data source

**tennis-data.co.uk** — free, ATP 2001→present, one Excel file per season.
Includes **Pinnacle** (`PSW`/`PSL`), the sharpest book and the best free proxy
for a closing line, plus Bet365, market max and market average.

**Caveat, stated plainly:** the site says odds "generally represent the most
recent before play starts". That is *approximately* closing, not verified
closing. Every CLV-style number here inherits that uncertainty. Pinnacle
coverage also thins out in the earlier years.

## Running it

```bash
# offline, synthetic market — verifies the harness end to end
python -m tennisbet p2 --synthetic --from-year 2010 --to-year 2024 --start-season 2016

# real data (download the season files first, they are behind a browser check)
#   http://www.tennis-data.co.uk/alldata.php  -> save 2005.xls .. 2026.xlsx
python -m tennisbet p2 --from-year 2005 --start-season 2015 --odds-dir ~/tennis_odds
```

## The linking problem

Two sources with no shared ID:

| | Sackmann | tennis-data |
|---|---|---|
| player | `Novak Djokovic` | `Djokovic N.` |
| date | tournament **start** date | actual **match** date |

Names are matched on `(surname, first initial)`. Sackmann's format is genuinely
ambiguous — `Felix Auger Aliassime` (surname `Auger Aliassime`) cannot be told
apart from `Juan Pablo Varillas` (surname `Varillas`) by any single split rule —
so every Sackmann name generates a *set* of candidate keys and the explicit
tennis-data surname picks the right one.

Dates are joined with a ±14 day window to absorb the tournament-start offset.

**Ambiguity is dropped, never guessed.** Two players sharing surname+initial, or
two candidate matches equally close in time, are discarded and counted in the
link report. A wrong link silently corrupts every number downstream and nothing
later can detect it; a missing link merely costs sample size.

Always read the link report. Below ~85% on modern seasons means something is
broken, not merely lossy.

## What the harness refuses to let you fool yourself about

**The vig is removed before every comparison.** Raw implied probabilities sum to
~1.05. Comparing a model against those manufactures edge out of arithmetic.

**A null test ships with the backtest.** It feeds the market's de-vigged
probabilities back in as if they were the model's. The correct output is *zero
bets*. If the null test ever finds profit, the harness is broken and every
result above it is void.

**Predictions are strictly out of sample**, produced by the same walk-forward
protocol as P1. Backtesting in-sample predictions is the standard way to invent
an edge that dies on contact with real money.

## Synthetic control results

`market_skill` controls how much of the true signal the simulated book sees;
at 1.00 it is perfectly efficient and unbeatable by construction.

| market | model log loss | market log loss | difference | bets | ROI |
|---|---|---|---|---|---|
| efficient (1.00) | 0.5412 | 0.5368 | **−0.0044** | 6,624 | −0.70% |
| very sharp (0.95) | 0.5388 | 0.5357 | **−0.0031** | 7,076 | **+1.78%** |
| beatable (0.85) | 0.5388 | 0.5396 | +0.0008 | 9,612 | +10.73% |
| soft (0.70) | 0.5388 | 0.5528 | +0.0140 | 12,442 | +26.69% |

Read the second row again. Against a very sharp market the model is **worse than
the market** on log loss — it has no edge whatsoever — and still returns
**+1.78% ROI over 7,076 bets**. That is what betting-strategy noise looks like,
and it is why ROI is not allowed to be the headline number here.

Note also that the model happily places thousands of bets even in the efficient
case. A `min_edge` threshold does not protect you; it just filters on a
disagreement that may be entirely the model's own error.

### A bug worth recording

The first version of this control kept the book's noise constant regardless of
`market_skill`, so the "efficient market" was still noisy and the harness
printed **+12.29% ROI against a market that was supposed to be unbeatable**. The
fault was in the fixture, not the model. That failure is now pinned by
`tests/test_p2_controls.py::test_efficient_market_cannot_be_beaten`.

## What P2 does not tell you

- Whether you can actually get these prices (limits, closing account risk).
- Whether the odds are true closing prices — see the caveat above.
- Anything about live/in-play markets.
- Anything about real ATP matches yet. **Run it on real data before drawing any
  conclusion.** Prior expectation: an Elo-only model does **not** beat Pinnacle
  closing. That is the honest starting hypothesis, and P2 exists to test it, not
  to confirm it.
