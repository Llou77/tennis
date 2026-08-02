# P1 — Elo baseline

## What P1 is

`load matches -> Elo features -> walk-forward evaluation -> comparison table`

Three models are scored under one identical protocol:

| model | what it is |
|---|---|
| `elo_baseline` | blended Elo probability, **zero fitted parameters** |
| `rank_baseline` | ATP rank difference through a logistic squash |
| `outcome_logistic` | logistic regression over the Elo feature block |

## Running it

Offline (synthetic tour — no network, verifies the pipeline itself):

```bash
python -m tennisbet p1 --synthetic --start-season 2016
```

On real data. The sandbox this was developed in cannot reach the dataset, so
run this **on your own machine**:

```bash
# option A: let it download and cache into data/raw/sackmann/
python -m tennisbet p1 --from-year 2005 --start-season 2015

# option B: clone the dataset once, then work fully offline
git clone https://github.com/JeffSackmann/tennis_atp ~/tennis_atp
python -m tennisbet p1 --from-year 2005 --start-season 2015 --local-dir ~/tennis_atp
```

Inspect the ingest alone:

```bash
python -m tennisbet ingest --from-year 2005 --out data/matches.parquet
```

## Results on the synthetic tour (33k matches, 2010–2024)

```
model                 log_loss    brier     ece     acc  folds        n
elo_baseline            0.5356   0.1801  0.0251   0.729      9   19,800
outcome_logistic        0.5403   0.1805  0.0276   0.729      9   19,800
rank_baseline           0.6415   0.2245  0.1268   0.685      9   19,800
```

Elo's ratings correlate **0.775** with the latent skill they were never shown —
the engine works.

## Read this before celebrating

**Logistic regression did not beat plain Elo.** That is the expected result, not
a bug: the features fed to it are all monotone transforms of the same Elo
numbers, so there is nothing extra to learn. It matters because it sets the bar
correctly — *any* future model must beat `elo_baseline` on log loss out of
sample, or it is added complexity buying nothing.

Real data will differ from these numbers. Expect roughly 0.58–0.62 log loss and
64–70% accuracy for Elo on real ATP matches; the synthetic tour is cleaner than
reality (no injuries, no motivation effects, no scheduling chaos).

**Accuracy is not the goal.** A bookmaker's closing line achieves ~0.55 log loss
on real matches. Until P2 measures us against actual closing prices, none of
these numbers say anything about whether money can be made.

## Leakage defences

Guarding against training on the future is the whole game, so it is enforced in
code and asserted in tests:

- Elo snapshots features **before** applying each match's result
  (`test_snapshot_is_pre_match`).
- Matches are processed in strict chronological order.
- Walk-forward folds train only on earlier seasons
  (`test_train_is_strictly_before_test`, `test_leakage_canary`).
- Calibration uses a **time-ordered tail**, never a random split.
- Post-match statistics carry a `post_` prefix so misuse is visible on sight.
- Walkovers do not move ratings; incomplete matches are dropped from training.
