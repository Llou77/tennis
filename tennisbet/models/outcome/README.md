# models/outcome

P(player_a wins). In: `MatchFeatures`. Out: `OutcomePrediction`.
Success metric is NOT raw accuracy (Elo already gets ~65-70%) but calibrated
probabilities that beat the bookmaker's **closing** line after de-vig.
Run standalone: `python -m tennisbet train` / `predict`.
