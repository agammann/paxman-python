"""B1 RED — common-word suppression off vs on (ADR-0009 §16 / R7).

Fails before B1 lands, passes after:
- CapabilityContract gains suppress_common_words bool=False
  (frozen no-slots, default off)
- Each capability's create_contract propagates the flag
- COMMON_WORDS derived intersection lowercased, USD not suppressed
- Engine loop skips suppressible short-code hits when flag on
"""

from __future__ import annotations

import paxman
from paxman.api.canonicalize import canonicalize
from paxman.api.scan import scan
from paxman.capabilities import Country, Currency
from paxman.core.discovery import reset_registry
from paxman.core.domain import Resolution

TEXT = "Ship to the United States of America, total 45.50 USD, weight 3.5 kg"


def _contract_country(suppress: bool):
    return Country.create_contract(suppress_common_words=suppress)


def _contract_currency(suppress: bool):
    return Currency.create_contract(suppress_common_words=suppress)


def test_common_words_table_invariants() -> None:
    from paxman.core.grammar.data.common_words import COMMON_WORDS

    # frozen size guard — Google1000 ∩ (ISO3166 α2/α3 + ISO4217 + ISO639)
    assert len(COMMON_WORDS) == 67
    assert "USD" not in COMMON_WORDS
    assert "usd" not in COMMON_WORDS
    # spot checks — curated via Google1000 ∩ code sets, USD never suppressed
    assert "to" in COMMON_WORDS
    assert "and" in COMMON_WORDS
    assert "is" in COMMON_WORDS
    assert "all" in COMMON_WORDS
    # not in intersection (shape-only noise, not valid-code collision)
    assert "the" not in COMMON_WORDS
    assert "of" not in COMMON_WORDS


def test_capability_contract_default_off() -> None:
    c = Country.create_contract()
    assert hasattr(c, "suppress_common_words")
    assert c.suppress_common_words is False
    c2 = Country.create_contract(suppress_common_words=True)
    assert c2.suppress_common_words is True
    # byte-identical when off (default)
    assert c.suppress_common_words is False


def test_scan_off_snapshot_locked() -> None:
    reset_registry()
    paxman.register_all_shipped()
    contract = _contract_country(False)
    result = scan(TEXT, [contract])
    mentions = result.mentions["country"]
    # 4 clustered mentions off — locked snapshot.
    # The code lanes claim the ISO 3166-1 code vocabulary, not arbitrary
    # token shapes, so "the", "45", "USD", "3" and "5" are never claimed.
    assert len(mentions) == 4
    spans = {m.span for m in mentions}
    assert (5, 7) in spans  # to -> Tonga
    assert (12, 36) in spans  # United States of America
    assert (47, 49) in spans  # 50 -> Bangladesh (zero-padded 050)
    assert (66, 68) in spans  # kg -> Kyrgyzstan
    # Never claimed: none of these is an ISO 3166-1 code, so no rule could
    # ever accept them.
    for absent in ((8, 11), (44, 46), (50, 53), (62, 63), (64, 65)):
        assert absent not in spans


def test_scan_on_suppresses_common_words() -> None:
    reset_registry()
    paxman.register_all_shipped()
    contract = _contract_country(True)
    result = scan(TEXT, [contract])
    mentions = result.mentions["country"]
    name_mentions = [m for m in mentions if m.grammar == "name_recognition"]
    assert len(name_mentions) == 1
    assert name_mentions[0].span == (12, 36)
    assert name_mentions[0].grammar == "name_recognition"
    spans = {m.span for m in mentions}
    assert (5, 7) not in spans  # to is common word -> suppressed
    # kg is not in COMMON_WORDS (not a valid-code collision) so it remains
    assert (66, 68) in spans  # kg not suppressed (kg not in Google1000)
    # "the" is not a code, so it is never claimed — nothing to suppress
    assert (8, 11) not in spans
    # total noise reduced: off 4 -> on 3 (only "to" removed)
    assert len(mentions) == 3


def test_scan_on_usd_remains_for_currency() -> None:
    reset_registry()
    paxman.register_all_shipped()
    contract = Currency.create_contract(suppress_common_words=True)
    result = scan(TEXT, [contract])
    mentions = result.mentions["currency"]
    spans = {m.span for m in mentions}
    assert (50, 53) in spans
    # the is not in COMMON_WORDS, so it remains even with suppression
    assert (8, 11) in spans
    # currency 'all' etc would be suppressed if present, but not in this text
    assert len(mentions) == 2


def test_canonicalize_to_off_vs_on_whole_input_exempt() -> None:
    reset_registry()
    paxman.register_all_shipped()
    off = canonicalize("to", _contract_country(False))
    assert off.status == Resolution.SUCCESS
    assert off.canonicalized_value == "TO"

    reset_registry()
    paxman.register_all_shipped()
    on = canonicalize("to", _contract_country(True))
    assert on.status == Resolution.SUCCESS
    assert on.canonicalized_value == "TO"


def test_whole_input_exempt_variants() -> None:
    for text in ("to", "TO", "  to  ", "to\n"):
        reset_registry()
        paxman.register_all_shipped()
        result = canonicalize(text, _contract_country(True))
        assert result.status == Resolution.SUCCESS
        assert result.canonicalized_value == "TO"


def test_embedded_still_suppressed() -> None:
    reset_registry()
    paxman.register_all_shipped()
    missing = canonicalize("in/", _contract_country(True))
    assert missing.status == Resolution.MISSING
    assert missing.canonicalized_value is None

    reset_registry()
    paxman.register_all_shipped()
    survived = canonicalize("to and usa", _contract_country(True))
    assert survived.status == Resolution.SUCCESS
    assert survived.canonicalized_value == "US"


def test_boundary_never_recognized() -> None:
    for text in ("in56", "2in"):
        reset_registry()
        paxman.register_all_shipped()
        result = canonicalize(text, _contract_country(True))
        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None


def test_scan_whole_input_exempt() -> None:
    reset_registry()
    paxman.register_all_shipped()
    result = scan("to", [_contract_country(True)])
    mentions = result.mentions["country"]
    assert len(mentions) == 1
    assert mentions[0].span == (0, 2)


def test_suppression_signal_defaults() -> None:
    reset_registry()
    paxman.register_all_shipped()
    result = canonicalize("to", _contract_country(False))
    assert result.suppressed_count == 0
    assert result.suppressed_spans == ()


def test_suppression_signal_missing() -> None:
    reset_registry()
    paxman.register_all_shipped()
    result = canonicalize("in/", _contract_country(True))
    assert result.status == Resolution.MISSING
    assert result.suppressed_count == 1
    assert result.suppressed_spans == ((0, 2),)


def test_suppression_signal_invalid() -> None:
    reset_registry()
    paxman.register_all_shipped()
    # "SU" is a former ISO 3166-3 code: claimed by the alpha-2 lane, but
    # rejected by the current-code rule while the historical rule is gated
    # off — so the call resolves INVALID.
    result = canonicalize("to and SU", _contract_country(True))
    assert result.status == Resolution.INVALID
    assert result.suppressed_count == 2
    assert set(result.suppressed_spans) == {(0, 2), (3, 6)}


def test_suppression_signal_success_embedded() -> None:
    reset_registry()
    paxman.register_all_shipped()
    result = canonicalize("to and usa", _contract_country(True))
    assert result.status == Resolution.SUCCESS
    assert result.suppressed_count == 3
    assert set(result.suppressed_spans) == {(0, 2), (3, 6), (7, 10)}


def test_suppression_signal_all_common_words_stays_missing() -> None:
    """A1 fallback rejected (#122): all-common-word prose stays MISSING.

    Every mention suppressed is observable, not resurrected — the signal
    (count 3) is what distinguishes this from "nothing recognized".
    """
    reset_registry()
    paxman.register_all_shipped()
    result = canonicalize("to and is", _contract_country(True))
    assert result.status == Resolution.MISSING
    assert result.canonicalized_value is None
    assert result.suppressed_count == 3
    assert set(result.suppressed_spans) == {(0, 2), (3, 6), (7, 9)}


def test_canonicalize_usd_not_suppressed() -> None:
    reset_registry()
    paxman.register_all_shipped()
    off = canonicalize("USD", Currency.create_contract(suppress_common_words=False))
    assert off.status == Resolution.SUCCESS
    assert off.canonicalized_value == "USD"
    reset_registry()
    paxman.register_all_shipped()
    on = canonicalize("USD", Currency.create_contract(suppress_common_words=True))
    assert on.status == Resolution.SUCCESS
    assert on.canonicalized_value == "USD"
