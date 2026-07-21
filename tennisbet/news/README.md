# news (enrichment — build last)

Fetches tennis news and extracts structured `NewsSignal`s (injury, withdrawal,
fatigue) that enrich `PlayerState`/`MatchFeatures`.

Honest expectation: lower ROI than structured data — much of this is already in
the odds by match time. Keep it isolated so it can be improved or ignored.
Run standalone: `python -m tennisbet news`.
