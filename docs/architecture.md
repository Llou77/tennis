# Architecture

## Principle: contracts over coupling

The only shared language between modules is `tennisbet/core/contracts.py`.
No module imports another module's internals; they import contracts. This is
what lets you "polish one part without touching the others."

## Data flow

1. **ingestion** → `RawMatch` (history + upcoming), `OddsSnapshot` (odds).
2. **features** → `MatchFeatures` from `RawMatch` + `PlayerState` (+ weather, news).
3. **models/outcome** → `OutcomePrediction`; **models/closeness** → `ClosenessPrediction`.
4. **betting** → `ValueBet` by comparing calibrated model probs to de-vigged odds.
5. **news** → `NewsSignal` enriching `PlayerState`/features (built last).

Everything is persisted through `core/storage.py` (parquet today, swappable).

## The closeness label is an open decision

`models/closeness/labels.py` enumerates candidate targets:
`games_margin`, `sets_margin`, `total_games`, `went_to_deciding_set`,
`competitiveness_index`. Pick one in config before building the model — the
model code is label-agnostic.

## Honest priorities (highest ROI first)

1. **Elo + surface Elo** — the strongest cheap signal. Baseline outcome model.
2. **Serve/return + form/fatigue + H2H** — the bulk of remaining structured signal.
3. **Calibration + backtest vs the closing line** — the only success metric that
   matters. Accuracy is a vanity metric; edge after de-vig is real.
4. **Closeness model** — build after outcome is calibrated.
5. **News/NLP enrichment** — last. Most match-relevant info is already priced in
   by match time; treat it as a marginal add, not a core driver.

## Roadmap

- **P0 (done):** scaffold, contracts, betting math + tests.
- **P1:** Sackmann ingest + Elo features + Elo-logistic baseline outcome model.
- **P2:** odds ingest + de-vig + walk-forward backtest vs closing line; calibration.
- **P3:** gradient-boosted outcome model; feature expansion.
- **P4:** closeness model on the chosen label.
- **P5:** news enrichment.

## Testing / anti-leakage

- Betting math is unit-tested (`tests/`).
- Features must use only pre-match information; backtests must be walk-forward
  (train on past, predict future) — never random splits.
