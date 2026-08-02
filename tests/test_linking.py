import csv
from pathlib import Path

import pandas as pd

from tennisbet.ingestion.historical_sackmann import build_match_table
from tennisbet.ingestion.linking import link_odds
from tennisbet.ingestion.odds_historical import classify_series

FIXTURE = Path(__file__).parent / "fixtures" / "atp_matches_sample.csv"


def matches():
    with FIXTURE.open(encoding="utf-8") as fh:
        return build_match_table(list(csv.DictReader(fh)))


def odds_row(date, winner, loser, tournament="Brisbane", series="ATP250",
             ow=1.8, ol=2.0):
    return {
        "odds_date": pd.Timestamp(date), "tournament": tournament,
        "location": tournament, "series": series, "surface": "hard",
        "round": "The Final", "best_of": 3,
        "winner_name": winner, "loser_name": loser, "comment": "Completed",
        "odds_w_pinnacle": ow, "odds_l_pinnacle": ol,
        "odds_w_bet365": ow, "odds_l_bet365": ol,
        "odds_w_max": ow, "odds_l_max": ol,
        "odds_w_avg": ow, "odds_l_avg": ol,
    }


def test_series_classification():
    assert classify_series("Grand Slam") == "GrandSlam"
    assert classify_series("Masters 1000") == "ATP1000"
    assert classify_series("ATP500") == "ATP500"
    assert classify_series("International") == "ATP250"
    assert classify_series("Masters Cup") is None     # Tour Finals: out of scope
    assert classify_series("") is None


def test_links_real_names_across_formats():
    m = matches()
    odds = pd.DataFrame([
        odds_row("2024-01-07", "Dimitrov G.", "Rune H."),
        odds_row("2024-01-16", "Djokovic N.", "Prizmic D.",
                 tournament="Australian Open", series="Grand Slam"),
        odds_row("2024-01-15", "Alcaraz C.", "Gasquet R.",
                 tournament="Australian Open", series="Grand Slam"),
    ])
    linked, rep = link_odds(m, odds)
    assert rep.linked == 3, rep.format()
    assert rep.match_rate == 1.0


def test_odds_are_reoriented_to_canonical_sides():
    """The winner's price must land on whichever canonical side actually won."""
    m = matches()
    odds = pd.DataFrame([odds_row("2024-01-07", "Dimitrov G.", "Rune H.",
                                  ow=1.5, ol=2.6)])
    linked, _ = link_odds(m, odds)
    r = linked.iloc[0]
    winner_price = r["odds_a_pinnacle"] if r["label_winner"] == 1 else r["odds_b_pinnacle"]
    loser_price = r["odds_b_pinnacle"] if r["label_winner"] == 1 else r["odds_a_pinnacle"]
    assert winner_price == 1.5 and loser_price == 2.6


def test_unknown_player_is_reported_not_guessed():
    odds = pd.DataFrame([odds_row("2024-01-07", "Nonexistent Q.", "Rune H.")])
    linked, rep = link_odds(matches(), odds)
    assert rep.linked == 0 and rep.unresolved_name == 1
    assert len(linked) == 0


def test_date_outside_tolerance_is_not_linked():
    odds = pd.DataFrame([odds_row("2024-06-01", "Dimitrov G.", "Rune H.")])
    _, rep = link_odds(matches(), odds, date_tolerance_days=14)
    assert rep.linked == 0 and rep.no_candidate == 1


def test_tournament_start_date_offset_is_tolerated():
    """Sackmann stamps the tournament START date; a late-round Slam match can be
    ~2 weeks later in the odds feed."""
    odds = pd.DataFrame([odds_row("2024-01-27", "Djokovic N.", "Prizmic D.",
                                  tournament="Australian Open", series="Grand Slam")])
    _, rep = link_odds(matches(), odds, date_tolerance_days=14)
    assert rep.linked == 1


def test_empty_inputs_are_safe():
    linked, rep = link_odds(matches(), pd.DataFrame())
    assert len(linked) == 0 and rep.linked == 0


def test_report_formats():
    _, rep = link_odds(matches(), pd.DataFrame([odds_row("2024-01-07", "Dimitrov G.", "Rune H.")]))
    assert "linked:" in rep.format()
