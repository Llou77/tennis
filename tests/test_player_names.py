from tennisbet.ingestion.player_names import (
    build_key_index, key_from_sackmann, key_from_tennis_data,
    parse_tennis_data_name, sackmann_candidate_keys, strip_accents,
)


def linked(sack: str, td: str) -> bool:
    return key_from_tennis_data(td) in sackmann_candidate_keys(sack)


def test_simple_names_link():
    assert linked("Novak Djokovic", "Djokovic N.")
    assert linked("Carlos Alcaraz", "Alcaraz C.")
    assert linked("Jannik Sinner", "Sinner J.")


def test_compound_surnames_link():
    assert linked("Botic Van De Zandschulp", "Van De Zandschulp B.")
    assert linked("Felix Auger Aliassime", "Auger Aliassime F.")
    assert linked("Roberto Bautista Agut", "Bautista Agut R.")
    assert linked("Alex De Minaur", "De Minaur A.")


def test_double_first_name_links():
    """The case a single split rule cannot get right at the same time as the
    compound-surname case."""
    assert linked("Juan Pablo Varillas", "Varillas J.P.")
    assert linked("Jan Lennard Struff", "Struff J.L.")


def test_accents_and_hyphens():
    assert strip_accents("Cerúndolo") == "Cerundolo"
    assert linked("Francisco Cerundolo", "Cerundolo F.")
    assert key_from_tennis_data("Bautista-Agut R.") == key_from_tennis_data("Bautista Agut R.")


def test_non_matches_stay_unlinked():
    assert not linked("Novak Djokovic", "Alcaraz C.")
    assert not linked("Carlos Alcaraz", "Djokovic N.")
    assert not linked("Novak Djokovic", "Djokovic M.")   # wrong initial


def test_empty_inputs():
    assert parse_tennis_data_name("") is None
    assert key_from_sackmann("") is None
    assert sackmann_candidate_keys("") == set()


def test_ambiguous_keys_excluded_from_index():
    names = {"1": "Alexander Zverev", "2": "Alexandre Zverev", "3": "Novak Djokovic"}
    index, ambiguous = build_key_index(names)
    assert key_from_tennis_data("Zverev A.") in ambiguous
    assert key_from_tennis_data("Zverev A.") not in index      # dropped, not guessed
    assert index[key_from_tennis_data("Djokovic N.")] == "3"


def test_index_resolves_real_roster():
    roster = {
        "1": "Novak Djokovic", "2": "Carlos Alcaraz", "3": "Jannik Sinner",
        "4": "Felix Auger Aliassime", "5": "Botic Van De Zandschulp",
        "6": "Juan Pablo Varillas", "7": "Roberto Bautista Agut",
    }
    index, _ = build_key_index(roster)
    for td, pid in [("Djokovic N.", "1"), ("Alcaraz C.", "2"), ("Sinner J.", "3"),
                    ("Auger Aliassime F.", "4"), ("Van De Zandschulp B.", "5"),
                    ("Varillas J.P.", "6"), ("Bautista Agut R.", "7")]:
        assert index.get(key_from_tennis_data(td)) == pid, td
