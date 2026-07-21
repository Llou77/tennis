# features

Turns `RawMatch` + `PlayerState` (+ weather, news) into a flat, model-ready
`MatchFeatures`. Each signal is a `FeatureBuilder`; `build.py` merges them.

Golden rule: **no leakage** — a feature may only use information available
before `match_date`.

Contract in: `RawMatch`, `PlayerState`. Contract out: `MatchFeatures`.
Run standalone: `python -m tennisbet features`.
