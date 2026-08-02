# tennis — ATP value-betting engine

A modular pipeline that predicts **match outcome** and **match closeness** for
ATP matches, compares those predictions to bookmaker odds, and flags
**value bets**.

> **Scope (hard rule):** predictions are only made for **ATP250, ATP500,
> ATP1000 and Grand Slam** events. Enforced via `ALLOWED_TIERS` in
> `tennisbet/core/contracts.py`.

## Why it's built in slices

Every module talks to the others **only** through the dataclasses in
`tennisbet/core/contracts.py`. Honor the contract and you can rewrite any
module's internals — or swap it entirely — without touching the rest.

```
ingestion ──RawMatch/OddsSnapshot──▶ features ──MatchFeatures──▶ models
                                                                   │
                          OutcomePrediction + ClosenessPrediction  │
                                                                   ▼
                              betting ──ValueBet──▶ (staking plan)
        news ──NewsSignal──▶ enriches PlayerState / features
```

## Module map

| Module | Does | In → Out | Run |
|---|---|---|---|
| `ingestion` | pull matches, odds, weather | ext → `RawMatch`, `OddsSnapshot` | `python -m tennisbet ingest` |
| `features` | build model inputs (Elo, form, serve/return, H2H, context) | `RawMatch` → `MatchFeatures` | `python -m tennisbet features` |
| `models/outcome` | P(player A wins) | `MatchFeatures` → `OutcomePrediction` | `python -m tennisbet train` |
| `models/closeness` | match tightness (pluggable label) | `MatchFeatures` → `ClosenessPrediction` | `python -m tennisbet predict` |
| `betting` | de-vig odds, edge, staking | `OutcomePrediction`+`OddsSnapshot` → `ValueBet` | `python -m tennisbet value` |
| `news` | injury/withdrawal signals (built last) | news → `NewsSignal` | `python -m tennisbet news` |

## Quickstart

```bash
python -m pip install -e ".[dev]"     # core + test deps
cp config/config.example.yaml config/config.yaml
cp .env.example .env                   # add API keys
python -m pytest -q                    # scaffold ships with passing tests
python -m tennisbet pipeline           # end-to-end wiring (stubs for now)
```

Per-module deps are optional extras so you can install just what you touch:
`pip install -e ".[data]"`, `".[models]"`, `".[news]"`.

## Status

**P1 complete.** Real and working: contracts, Sackmann ingest (tier filtering,
canonical player ordering, score parsing), Elo + surface Elo, the baseline
outcome model, walk-forward evaluation, and the betting math — **57 tests passing**. Still stubs: form/serve-return/H2H features, the closeness model,
odds ingestion, and news.

Try it offline in one command:

```bash
python -m tennisbet p1 --synthetic --start-season 2016
```

See `docs/p1_baseline.md` for results and how to run on real data, and
`docs/architecture.md` for the roadmap.

## Disclaimer

Sports betting carries financial risk and beating the closing line is hard.
This is a research tool, not financial advice.
