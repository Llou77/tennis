# models/closeness

Predicts match tightness. In: `MatchFeatures`. Out: `ClosenessPrediction`.
The label is pluggable — see `labels.py` and `models.closeness.label` in config.
Decide the label first; everything else here is label-agnostic.
