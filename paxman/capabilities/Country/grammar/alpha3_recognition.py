"""Alpha-3 country code recognition grammar (kernel LexiconMatcher).

Recognizes ISO 3166-1 alpha-3 code tokens: the 249 assigned codes plus
the user-assigned XKX (Kosovo). Recognition is over the code vocabulary,
not over an arbitrary three-letter shape — a token that no authority
could ever accept is never claimed, so ordinary prose words do not
surface as country mentions. The keys are lowercased and matched on the
``casefolded`` kernel view; the emitted notation is uppercased.
BoundarySpec.WORD provides word-boundary discipline (ADR-0009 §10).
Syntax only: never resolves the code to a country.
Suppressible short-code matcher (ADR-0009 §16).
"""

from __future__ import annotations

from paxman.capabilities.Country.grammar.data.alpha3_codes import ALPHA3_CODE_KEYS
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.grammar import AnchorSet, BoundarySpec, PipelineGrammar, StandardPre
from paxman.core.grammar.matchers.lexicon import LexiconMatcher
from paxman.core.grammar.scan_context import ScanContext


def _emit(span: tuple[int, int], ctx: ScanContext) -> CountryNotation:
    s, e = span
    raw = ctx.text[s:e]
    return CountryNotation(shape="alpha3", value=raw.upper())


_MATCHER = LexiconMatcher(
    tokens=ALPHA3_CODE_KEYS,
    boundary=BoundarySpec.WORD,
    view="casefolded",
    anchors=AnchorSet(),
    emit=_emit,
    suppressible=True,
    representation="trie",
)


class Alpha3Grammar(PipelineGrammar[CountryNotation]):
    """Recognizes ISO 3166-1 alpha-3 code tokens.

    Examples: "USA", "GBR", "usa", "gbr"
    Non-examples: "US" (2 letters), "123" (digits), "United" (6 letters),
                  "the" (not an assigned code)
    """

    name = "alpha3_recognition"
    semantics = "alpha3_recognition"
    single_value = True

    pre = StandardPre[CountryNotation](empty_guard=True)
    matchers = (_MATCHER,)
