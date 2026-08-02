from tennisbet.core.score import parse_score


def test_straight_sets():
    p = parse_score("6-4 6-3")
    assert p.completed
    assert p.sets == [(6, 4), (6, 3)]
    assert p.games_winner == 12 and p.games_loser == 7
    assert p.total_games == 19
    assert p.sets_winner == 2 and p.sets_loser == 0


def test_tiebreak_detail_stripped():
    p = parse_score("7-6(5) 6-4")
    assert p.sets == [(7, 6), (6, 4)]
    assert p.total_games == 23


def test_five_setter():
    p = parse_score("4-6 6-3 3-6 6-2 6-4")
    assert p.sets_winner == 3 and p.sets_loser == 2
    assert p.completed


def test_walkover_not_completed():
    p = parse_score("W/O")
    assert p.walkover and not p.completed


def test_retirement_flagged():
    p = parse_score("6-4 2-0 RET")
    assert p.retired and not p.completed
    assert p.sets == [(6, 4), (2, 0)]


def test_retirement_zero_games():
    p = parse_score("6-4 6-7(4) 0-0 RET")
    assert p.retired
    assert p.sets[-1] == (0, 0)


def test_unparseable():
    assert not parse_score("").parseable
    assert not parse_score(None).parseable
    assert not parse_score("Unfinished").parseable
