"""Player-name normalization for cross-source linking.

The two sources disagree on format, and this is the single biggest source of
silent data loss in the project:

    Sackmann      "Novak Djokovic"        first last
    tennis-data   "Djokovic N."           surname, initial(s)

tennis-data is the easy side: the surname is explicit. Sackmann is genuinely
ambiguous — from the string alone, "Felix Auger Aliassime" (surname
"Auger Aliassime") is indistinguishable from "Juan Pablo Varillas" (surname
"Varillas"). Guessing a split rule gets one of them wrong.

So we do not guess. Every Sackmann name yields a SET of candidate keys, one per
possible split, and a link succeeds when a candidate matches the tennis-data key.

The remaining failure mode: two players producing the same key (two "Zverev A.").
`build_key_index` flags those, and linking DROPS them rather than picking one.
A wrong link is far worse than a missing one — it silently corrupts every
backtest downstream, and nothing later will tell you.
"""
from __future__ import annotations

import re
import unicodedata


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(s or ""))
                   if not unicodedata.combining(c))


def _clean(s: str) -> str:
    s = strip_accents(s).lower()
    s = s.replace("-", " ").replace("'", "").replace(".", " ")
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def name_key(surname: str, initial: str) -> str:
    return f"{surname}|{initial}"


def parse_tennis_data_name(name: str) -> tuple[str, str] | None:
    """'Djokovic N.' -> ('djokovic','n');  'Varillas J.P.' -> ('varillas','j')."""
    c = _clean(name)
    if not c:
        return None
    parts = c.split()
    initials: list[str] = []
    while len(parts) > 1 and len(parts[-1]) == 1:
        initials.insert(0, parts.pop())
    if not parts:
        return None
    if not initials:
        return (" ".join(parts), "")
    return (" ".join(parts), initials[0])


def key_from_tennis_data(name: str) -> str | None:
    p = parse_tennis_data_name(name)
    return name_key(*p) if p else None


def sackmann_candidate_keys(name: str) -> set[str]:
    """All plausible (surname, initial) keys for a 'First [Middle] Last...' name.

    'Felix Auger Aliassime' -> {'auger aliassime|f', 'aliassime|f'}
    'Juan Pablo Varillas'   -> {'pablo varillas|j', 'varillas|j'}
    Exactly one of each set will match the explicit tennis-data surname.
    """
    c = _clean(name)
    if not c:
        return set()
    parts = c.split()
    if len(parts) == 1:
        return {name_key(parts[0], "")}
    initial = parts[0][0]
    return {name_key(" ".join(parts[i:]), initial) for i in range(1, len(parts))}


def key_from_sackmann(name: str) -> str | None:
    """The single most likely key (everything after the first token).
    Use `sackmann_candidate_keys` for matching; this is for display/debug."""
    c = _clean(name)
    if not c:
        return None
    parts = c.split()
    if len(parts) == 1:
        return name_key(parts[0], "")
    return name_key(" ".join(parts[1:]), parts[0][0])


def build_key_index(sackmann_names: dict[str, str]) -> tuple[dict[str, str], set[str]]:
    """{player_id: full_name} -> (key -> player_id, ambiguous_keys).

    A key claimed by more than one player_id is ambiguous and excluded from the
    lookup entirely.
    """
    claims: dict[str, set[str]] = {}
    for pid, nm in sackmann_names.items():
        for k in sackmann_candidate_keys(nm):
            claims.setdefault(k, set()).add(pid)
    ambiguous = {k for k, ids in claims.items() if len(ids) > 1}
    index = {k: next(iter(ids)) for k, ids in claims.items() if len(ids) == 1}
    return index, ambiguous
