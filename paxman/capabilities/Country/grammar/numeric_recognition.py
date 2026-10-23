"""Numeric (M49) country code recognition grammar (kernel LexiconMatcher).

Recognizes ISO 3166-1 numeric (M49) code tokens: the 249 assigned codes
in their zero-padded 3-digit form, plus the shorter 1- and 2-digit forms
that zero-pad to an assigned code (the validation rule pads to 3 digits,
so "4" resolves to "004"). Recognition is over the code vocabulary, not
over an arbitrary 1-3 digit run — a number that no authority could ever
accept is never claimed. Scanning runs on the ``ascii_digits`` view: the
rule resolves through ``int()``, which accepts every Unicode decimal-digit
script ("٨٤٠" is 840), so the ASCII keys must reach those forms too. The
view is 1:1, so spans map back to the source text and the notation keeps
the raw digits. BoundarySpec.WORD provides word-boundary discipline
(ADR-0009 §10). Syntax only: never resolves the code to a country.
Suppressible marker present (ADR-0009 §16) — digit hits never collide with
COMMON_WORDS but declaration keeps the short-code surface uniform.
"""

from __future__ import annotations

from paxman.capabilities.Country.grammar.data.numeric_codes import NUMERIC_CODE_KEYS
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.grammar import AnchorSet, BoundarySpec, PipelineGrammar, StandardPre
from paxman.core.grammar.matchers.lexicon import LexiconMatcher
from paxman.core.grammar.scan_context import ScanContext


def _emit(span: tuple[int, int], ctx: ScanContext) -> CountryNotation:
    s, e = span
    raw = ctx.text[s:e]
    return CountryNotation(shape="numeric", value=raw)


_MATCHER = LexiconMatcher(
    tokens=NUMERIC_CODE_KEYS,
    boundary=BoundarySpec.WORD,
    view="ascii_digits",
    anchors=AnchorSet(),
    emit=_emit,
    suppressible=True,
    representation="trie",
)


class NumericGrammar(PipelineGrammar[CountryNotation]):
    """Recognizes ISO 3166-1 numeric (M49) code tokens.

    Examples: "840", "4", "004"
    Non-examples: "US" (letters), "1234" (4 digits), "12a" (alphanumeric),
                  "01" (not an assigned code)
    """

    name = "numeric_recognition"
    semantics = "numeric_recognition"
    single_value = True

    pre = StandardPre[CountryNotation](empty_guard=True)
    matchers = (_MATCHER,)
