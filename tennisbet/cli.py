"""CLI so every stage runs standalone:

    python -m tennisbet p1 --synthetic          # offline end-to-end baseline
    python -m tennisbet p1 --from-year 2005     # real Sackmann data (needs network)
    python -m tennisbet ingest --from-year 2010

Stages not yet implemented print what they are waiting on rather than pretending.
"""
from __future__ import annotations

import argparse

STAGES = ["ingest", "features", "train", "predict", "value", "news", "pipeline", "p1", "p2"]


def _load_df(args):
    if args.synthetic:
        from .ingestion.synthetic import generate
        df, _ = generate(seasons=(args.from_year, args.to_year or 2024), seed=args.seed)
        return df
    from .ingestion.historical_sackmann import SackmannFetcher, build_match_table
    f = SackmannFetcher(from_year=args.from_year, to_year=args.to_year,
                        local_dir=args.local_dir)
    df = build_match_table(f.fetch())
    if df.empty:
        raise SystemExit(
            "No matches loaded. Either the download failed (no network) or the\n"
            "year range is empty. Options:\n"
            "  * clone https://github.com/JeffSackmann/tennis_atp and pass --local-dir\n"
            "  * run with --synthetic to exercise the pipeline offline"
        )
    return df


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tennisbet")
    p.add_argument("stage", choices=STAGES)
    p.add_argument("--config", default="config/config.yaml")
    p.add_argument("--from-year", type=int, default=2005)
    p.add_argument("--to-year", type=int, default=None)
    p.add_argument("--start-season", type=int, default=2015)
    p.add_argument("--local-dir", default=None,
                   help="path to a local clone of JeffSackmann/tennis_atp")
    p.add_argument("--synthetic", action="store_true",
                   help="use the synthetic tour generator (no network needed)")
    p.add_argument("--algo", default="logistic", choices=["logistic", "lightgbm"])
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=None, help="write the match table to parquet")
    p.add_argument("--odds-dir", default=None,
                   help="folder of tennis-data.co.uk season files (xls/xlsx)")
    p.add_argument("--book", default="pinnacle",
                   choices=["pinnacle", "bet365", "max", "avg"])
    p.add_argument("--min-edge", type=float, default=0.03)
    p.add_argument("--baseline", action="store_true",
                   help="score raw Elo instead of a fitted model")
    args = p.parse_args(argv)

    if args.stage == "ingest":
        df = _load_df(args)
        print(f"Loaded {len(df):,} in-scope matches "
              f"({df['match_date'].min().date()} .. {df['match_date'].max().date()})")
        print(df["tier"].value_counts().to_string())
        if args.out:
            df.to_parquet(args.out, index=False)
            print(f"wrote {args.out}")
        return 0

    if args.stage == "p2":
        from .pipeline.p2_value import P2Config, format_report, run
        df = _load_df(args)
        if args.synthetic:
            from .ingestion.synthetic import generate_odds
            from .features.elo import compute_elo_features
            feats, _ = compute_elo_features(df)
            df = generate_odds(df.join(feats[["elo_blend_prob_a"]]))
            df = df.drop(columns=["elo_blend_prob_a"])
        else:
            from .ingestion.linking import link_odds
            from .ingestion.odds_historical import load_odds
            years = sorted(set(df["match_date"].dt.year))
            odds = load_odds(years, local_dir=args.odds_dir)
            if len(odds) == 0:
                raise SystemExit(
                    "No odds loaded. Download the season files from\n"
                    "  http://www.tennis-data.co.uk/alldata.php\n"
                    "into a folder and pass --odds-dir, or use --synthetic.")
            df, report = link_odds(df, odds)
            print(report.format()); print()
        out = run(df, P2Config(start_season=args.start_season, book=args.book,
                               min_edge=args.min_edge, algo=args.algo,
                               use_baseline=args.baseline))
        print(format_report(out))
        return 0

    if args.stage == "p1":
        from .pipeline.p1_baseline import P1Config, format_report, run
        df = _load_df(args)
        out = run(df, P1Config(start_season=args.start_season, algos=(args.algo,)))
        print(format_report(out))
        return 0

    print(f"[tennisbet] stage='{args.stage}' — module scaffolded, not yet implemented.")
    print("See the module README and the roadmap in docs/architecture.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
