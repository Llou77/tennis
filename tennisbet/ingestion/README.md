# ingestion

Pulls raw data from external sources. Each source is a `Fetcher` subclass and
writes normalized rows via `tennisbet.core.storage`. Nothing downstream knows
which provider was used.

Sources: `historical_sackmann` (training backbone), `schedule_results`
(current season), `odds` (bookmaker snapshots), `weather` (venue conditions).

Contract out: `RawMatch`, `OddsSnapshot` (see `core/contracts.py`).
Run standalone: `python -m tennisbet ingest`.
