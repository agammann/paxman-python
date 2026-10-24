"""Alpha-2 country code recognition grammar (kernel LexiconMatcher).

Recognizes ISO 3166-1 alpha-2 code tokens: the 249 assigned codes plus
the user-assigned XK (Kosovo). Recognition is over the code vocabulary,
not over an arbitrary two-letter shape — a token that no authority could
ever accept is never claimed, so ordinary prose words do not surface as
country mentions. The keys are lowercased and matched on the
``casefolded`` kernel view; the emitted notation is uppercased.
BoundarySpec.WORD provides word-boundary discipline (ADR-0009 §10).
Syntax only: never resolves the code to a country.
Suppressible short-code matcher (ADR-0009 §16): with
suppress_common_words=True the high-frequency word hits are skipped in
the engine loop (provenance-neutral, default off).
"""

from __future__ import annotations

from paxman.capabilities.Country.grammar.data.alpha2_codes import ALPHA2_CODE_KEYS
from paxman.capabilities.Country.notation import CountryNotation
from paxman.core.grammar import AnchorSet, BoundarySpec, PipelineGrammar, StandardPre
from paxman.core.grammar.matchers.lexicon import LexiconMatcher
from paxman.core.grammar.scan_context import ScanContext


def _emit(span: tuple[int, int], ctx: ScanContext) -> CountryNotation:
    s, e = span
    raw = ctx.text[s:e]
    return CountryNotation(shape="alpha2", value=raw.upper())


_MATCHER = LexiconMatcher(
    tokens=ALPHA2_CODE_KEYS,
    boundary=BoundarySpec.WORD,
    view="casefolded",
    anchors=AnchorSet(),
    emit=_emit,
    suppressible=True,
    representation="trie",
)


class Alpha2Grammar(PipelineGrammar[CountryNotation]):
    """Recognizes ISO 3166-1 alpha-2 code tokens.

    Examples: "US", "GB", "us", "gB"
    Non-examples: "USA" (3 letters), "12" (digits), "U" (1 letter),
                  "xx" (not an assigned code)
    """

    name = "alpha2_recognition"
    semantics = "alpha2_recognition"
    single_value = True

    pre = StandardPre[CountryNotation](empty_guard=True)
    matchers = (_MATCHER,)
