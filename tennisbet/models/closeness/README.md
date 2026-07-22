# models/closeness

Predicts match tightness. In: `MatchFeatures`. Out: `ClosenessPrediction`.
The label is pluggable — see `labels.py` and `models.closeness.label` in config.
Decide the label first; everything else here is label-agnostic.

## Decision (2026-07-22)
Keep all candidate labels and compare them (`compare.py`) rather than fixing one.
`primary_label` (config) = the tradeable label that drives value bets
(default `total_games`); the rest are informational until a market exists.
