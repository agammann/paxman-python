"""Normalizer unit tests — composable, provenance-aware, offset-disciplined."""

from __future__ import annotations

from paxman.core.domain import Provenance
from paxman.core.grammar.normalizers import (
    AccentStrip,
    CaseFold,
    DecimalDigitFold,
    IDNAFold,
    Normalizer,
    NormalizerSequence,
    SeparatorFold,
    StripSeparators,
    SymbolFold,
)
from paxman.core.grammar.scan_context import ScanContext

BIPM = Provenance(
    authority="BIPM",
    specification_name="SI Brochure",
    kind="specification",
    reference_url="https://www.bipm.org/",
    version="9",
    lifecycle="active",
    publication_year=2019,
)


def test_decimal_digit_fold_maps_every_nd_script_to_ascii() -> None:
    """Nd digits fold to ASCII 1:1, so identity offsets stay exact."""
    nf = DecimalDigitFold()
    assert nf.name == "ascii_digits"
    assert nf.provenance is None
    assert nf.stripped_chars is None
    # Arabic-Indic, Devanagari, full-width, Extended Arabic-Indic, and the
    # astral Mathematical Bold block (outside the BMP, still one code point).
    for text in (
        "\u0668\u0664\u0660",
        "\u096e\u096a\u0966",
        "\uff18\uff14\uff10",
        "\u06f8\u06f4\u06f0",
        "\U0001d7d6\U0001d7d2\U0001d7ce",
    ):
        subject, starts, ends = nf.normalize(text)
        assert subject == "840", text
        assert len(subject) == len(text)
        assert starts is None and ends is None


def test_decimal_digit_fold_leaves_everything_else_alone() -> None:
    """ASCII text and non-decimal numerals are returned untouched."""
    nf = DecimalDigitFold()
    for text in ("840", "Cote d'Ivoire", "", "US 840"):
        assert nf.normalize(text) == (text, None, None)
    # Superscript/circled numerals are No, not Nd: `\\d` never matched them
    # and neither does this view, so no reach is invented.
    for text in ("\u2078\u2074\u2070", "\u2467\u2463\u2460"):
        assert nf.normalize(text) == (text, None, None)


def test_decimal_digit_fold_view_preserves_source_spans() -> None:
    """A folded view is 1:1, so view spans equal source spans."""
    nf = DecimalDigitFold()
    ctx = ScanContext.of("x \u0668\u0664\u0660 y")
    view = ctx.view(nf.name, nf.normalize, stripped_chars=nf.stripped_chars)
    assert view.subject == "x 840 y"
    # Nothing was stripped or expanded, so no offset map is needed at all.
    assert view.source_starts is None
    assert view.source_ends is None
    start = view.subject.index("840")
    assert view.original_span(start, start + 3) == (2, 5)


def test_casefold_identity_view() -> None:
    nf = CaseFold()
    assert nf.name == "casefolded"
    assert nf.provenance is None
    subject, starts, ends = nf.normalize("Hello € WORLD")
    assert subject == "hello € world"
    assert starts is None and ends is None
    ctx = ScanContext.of("Hello € WORLD")
    view = ctx.view(nf.name, nf.normalize)
    assert view.subject == "hello € world"
    assert view.source_starts is None
    assert view.source_ends is None


def test_separatorfold_bcp47() -> None:
    nf = SeparatorFold()
    assert nf.provenance is not None
    assert "BCP 47" in nf.provenance.specification_name
    assert SeparatorFold().normalize("en_US")[0] == "en-US"
    subj, s, e = SeparatorFold().normalize("en_US")
    assert s is None and e is None
    _ = subj


def test_accentstrip_country() -> None:
    nf = AccentStrip()
    assert nf.normalize("Côte d'Ivoire")[0] == "cote d'ivoire"
    subj, s, e = nf.normalize("Côte d'Ivoire")
    assert s is None and e is None
    _ = subj
    ctx = ScanContext.of("Côte d'Ivoire")
    view = ctx.view(nf.name, nf.normalize)
    assert ctx.text[view.original_span(0, 4)[0] : view.original_span(0, 4)[1]] == "Côte"


def test_symbolfold_si() -> None:
    nf = SymbolFold()
    assert nf.provenance is not None
    assert "BIPM" in nf.provenance.authority
    assert "SI Brochure" in nf.provenance.specification_name
    assert nf.normalize("m²")[0] == "m2"
    assert nf.normalize("µm")[0] == "μm"
    subj, s, e = nf.normalize("m²")
    assert s is None and e is None
    _ = subj
    assert IDNAFold().name == "idna"


def test_stripseparators_phone() -> None:
    nf = StripSeparators()
    subject, starts, ends = nf.normalize("+1 (555) 123-4567")
    assert subject == "+15551234567"
    assert starts is not None and ends is not None
    assert len(starts) == len(subject)
    assert len(ends) == len(subject)
    ctx = ScanContext.of("+1 (555) 123-4567")
    view = ctx.view("compact", nf.normalize)
    o_s, o_e = view.original_span(1, 4)
    assert 0 <= o_s < o_e <= len(ctx.text)


def test_sequence_composable() -> None:
    seq = NormalizerSequence(steps=(CaseFold(), SeparatorFold()))
    subject, starts, ends = seq.normalize("Hello_World")
    assert subject == "hello-world"
    assert starts is None and ends is None


def test_protocol_shape() -> None:
    assert isinstance(CaseFold(), Normalizer)
    assert isinstance(SeparatorFold(), Normalizer)


def test_casefold_expanding_fold_emits_explicit_maps() -> None:
    # İ U+0130 lowercases to two code points: identity offsets would mis-map
    # view spans to source ranges (previously a RecognitionError downstream).
    subject, starts, ends = CaseFold().normalize("Aİ")
    assert subject == "a" + "i̇"
    assert starts == (0, 1, 1)
    assert ends == (1, 2, 2)
    assert len(starts) == len(subject) and len(ends) == len(subject)


def test_casefold_maps_cover_subject_exactly() -> None:
    # Greedy consumption covers the subject exactly once, in order — even
    # with the dotted-i contraction (i + U+0307 lowers to one char).
    texts = ["İ", "AİB", "i" + "̇x", "ΟΣ", "Hello"]
    for text in texts:
        subject, starts, ends = CaseFold().normalize(text)
        if len(subject) == len(text):
            assert starts is None and ends is None
        else:
            assert starts is not None and ends is not None
            assert len(starts) == len(subject)
            assert len(ends) == len(subject)
            assert all(s < e for s, e in zip(starts, ends, strict=True))


def test_accentstrip_reshape_emits_explicit_maps() -> None:
    # Combining mark with no base char: stripping reshapes the text, so
    # identity offsets would mis-map.
    subject, starts, ends = AccentStrip().normalize("e" + "́")
    assert subject == "e"
    assert starts == (0,)
    assert ends == (1,)
