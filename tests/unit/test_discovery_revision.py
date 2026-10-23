"""Gates for the ``recognition_revision`` stamp.

Two properties, both regression-pinned:

* **Cost** — ``freeze_registry`` uses each matcher's cached ``digest``
  (computed once at construction) instead of re-deriving sorted tokens per
  freeze, and snapshot hashing is memoized.
* **Stability** — the revision is identical across processes for the same
  library snapshot. Several payloads used to be rendered with ``repr()``,
  which for a ``frozenset[str]`` follows hash order, so the revision varied
  with ``PYTHONHASHSEED`` and could not distinguish "different library" from
  "different process".
"""

from __future__ import annotations


def test_freeze_twice_identical_recognition_revision() -> None:
    from paxman.capabilities.Country.capability import CountryCapability
    from paxman.core.discovery import (
        freeze_registry,
        get_recognition_revision,
        register_capability,
        reset_registry,
    )

    reset_registry()
    register_capability(CountryCapability())
    freeze_registry()
    rev1 = get_recognition_revision()
    reset_registry()
    register_capability(CountryCapability())
    freeze_registry()
    rev2 = get_recognition_revision()
    assert rev1 == rev2, (
        f"freeze twice must give identical revision: {rev1!r} != {rev2!r}"
    )
    assert rev1 != "0"
    reset_registry()


def test_repeated_freeze_uses_cached_digests() -> None:
    """Second onward freeze must use cached digests via matcher.digest identity."""
    from paxman.core.discovery import (
        freeze_registry,
        reset_registry,
    )
    from paxman.core.grammar.matchers.lexicon import LexiconMatcher
    from paxman.core.grammar.matchers.regex import RegexMatcher
    from paxman.core.grammar.matchers.scanner import ScannerMatcher
    from paxman.core.grammar.scan_context import View

    lex = LexiconMatcher(tokens=frozenset({"hello", "world"}))
    assert hasattr(lex, "digest")
    lex_d = getattr(lex, "digest", None)
    assert isinstance(lex_d, str) and len(lex_d) > 0

    reg = RegexMatcher(pattern=r"\d+", flags=0)
    assert hasattr(reg, "digest")
    reg_d = getattr(reg, "digest", None)
    assert isinstance(reg_d, str) and len(reg_d) > 0

    def _scan(view: View, pos: int):  # type: ignore[no-untyped-def]
        return None

    scan = ScannerMatcher(scan=_scan, max_window=10)
    assert hasattr(scan, "digest")
    scan_d = getattr(scan, "digest", None)
    assert isinstance(scan_d, str) and len(scan_d) > 0

    lex_digest_id = id(lex_d)
    _ = (reg_d, scan_d)

    from paxman.capabilities.Country.capability import CountryCapability
    from paxman.core.discovery import register_capability

    for _ in range(5):
        reset_registry()
        register_capability(CountryCapability())
        freeze_registry()
        lex2 = LexiconMatcher(tokens=frozenset({"hello", "world"}))
        assert getattr(lex2, "digest", None) == getattr(lex, "digest", None), (
            "same tokens must give equal digest"
        )

    assert getattr(lex, "digest", None) == getattr(
        LexiconMatcher(tokens=frozenset({"hello", "world"})), "digest", None
    )
    # digest is computed once at construction, so the string object is retained
    assert id(getattr(lex, "digest", None)) == lex_digest_id

    for _ in range(3):
        assert hasattr(LexiconMatcher(tokens=frozenset({"a", "b"})), "digest")

    reset_registry()


def test_lexicon_digest_purity_same_tokens_equal() -> None:
    from paxman.core.grammar.matchers.lexicon import LexiconMatcher

    a = LexiconMatcher(tokens=frozenset({"alpha", "beta", "gamma"}))
    b = LexiconMatcher(tokens=frozenset({"gamma", "beta", "alpha"}))
    assert getattr(a, "digest", None) == getattr(b, "digest", None), (
        "same tokens in any order must give equal digest"
    )
    assert isinstance(getattr(a, "digest", None), str)


def test_lexicon_digest_changes_on_token_add() -> None:
    from paxman.core.grammar.matchers.lexicon import LexiconMatcher

    base = LexiconMatcher(tokens=frozenset({"alpha", "beta"}))
    plus_one = LexiconMatcher(tokens=frozenset({"alpha", "beta", "gamma"}))
    assert getattr(base, "digest", None) != getattr(plus_one, "digest", None), (
        "+1 token must change digest"
    )


def test_regex_digest_purity() -> None:
    from paxman.core.grammar.matchers.regex import RegexMatcher

    a = RegexMatcher(pattern=r"hello\d+", flags=0)
    b = RegexMatcher(pattern=r"hello\d+", flags=0)
    c = RegexMatcher(pattern=r"hello\d+", flags=2)
    d = RegexMatcher(pattern=r"world\d+", flags=0)
    assert getattr(a, "digest", None) == getattr(b, "digest", None)
    assert getattr(a, "digest", None) != getattr(c, "digest", None), (
        "flags change must change digest"
    )
    assert getattr(a, "digest", None) != getattr(d, "digest", None), (
        "pattern change must change digest"
    )


def test_scanner_digest_purity() -> None:
    from paxman.core.grammar.boundary_spec import BoundarySpec
    from paxman.core.grammar.matchers.scanner import ScannerMatcher
    from paxman.core.grammar.scan_context import View

    def _scan_a(view: View, pos: int):  # type: ignore[no-untyped-def]
        return None

    def _scan_b(view: View, pos: int):  # type: ignore[no-untyped-def]
        return None

    s1 = ScannerMatcher(scan=_scan_a, max_window=10)
    s2 = ScannerMatcher(scan=_scan_a, max_window=10)
    s3 = ScannerMatcher(scan=_scan_a, max_window=20)
    s4 = ScannerMatcher(scan=_scan_b, max_window=10)
    assert getattr(s1, "digest", None) == getattr(s2, "digest", None)
    assert getattr(s1, "digest", None) != getattr(s3, "digest", None), (
        "max_window change must change digest"
    )
    assert getattr(s1, "digest", None) != getattr(s4, "digest", None), (
        "qualname change must change digest"
    )

    s5 = ScannerMatcher(scan=_scan_a, max_window=10, boundary=BoundarySpec.WORD)
    assert getattr(s1, "digest", None) != getattr(s5, "digest", None)


def test_snapshot_hash_memo_dict_exists() -> None:
    import paxman.core.discovery as disc

    val = getattr(disc, "_snapshot_hashes", None)
    assert hasattr(disc, "_snapshot_hashes"), (
        "discovery must expose _snapshot_hashes memo dict"
    )
    assert isinstance(val, dict)


def test_discovery_freeze_reads_digest_not_sorted_tokens() -> None:
    """Ensure freeze_registry source reads matcher.digest."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    src = (repo_root / "paxman" / "core" / "discovery.py").read_text(encoding="utf-8")
    assert (
        "matcher.digest" in src
        or 'getattr(matcher, "digest"' in src
        or "getattr(matcher, 'digest'" in src
    ), "freeze_registry must read matcher.digest"
    freeze_section = src[
        src.find("def freeze_registry") : src.find("def is_registry_frozen")
    ]
    assert "sorted(cast(Iterable[str], tokens_set))" not in freeze_section, (
        "freeze_registry must not re-derive sorted tokens — use matcher.digest"
    )


def test_stable_repr_is_hash_order_independent() -> None:
    """``stable_repr`` must not depend on set/dict iteration order.

    ``repr(frozenset[str])`` iterates in hash order, which is randomised per
    process, so it cannot feed a digest that must be identical across
    processes. ``stable_repr`` sorts set members and dict items.
    """
    from paxman.core.grammar.matchers._stable import stable_repr

    assert stable_repr(frozenset({"alpha", "beta", "gamma"})) == stable_repr(
        frozenset({"gamma", "beta", "alpha"})
    )
    assert stable_repr({"b": 1, "a": 2}) == stable_repr({"a": 2, "b": 1})
    # Ordered containers keep their order — order is meaningful there.
    assert stable_repr(("a", "b")) != stable_repr(("b", "a"))
    # Scalars render as repr.
    assert stable_repr("US") == "'US'"
    assert stable_repr(None) == "None"
    # Callables render by qualname, never by address.
    from paxman.core.grammar.matchers._stable import stable_repr as sr

    def _sample() -> None:  # pragma: no cover - identity only
        pass

    assert sr(_sample).endswith("._sample")
    assert "0x" not in sr(_sample)
    # Compiled patterns render by source and flags, not by object identity.
    import re

    assert stable_repr(re.compile("a+", re.I)) == stable_repr(re.compile("a+", re.I))
    assert stable_repr(re.compile("a+")) != stable_repr(re.compile("a+", re.I))
    assert "0x" not in stable_repr(re.compile("a+"))

    # An unmodelled object keeps its repr, but never its memory address — two
    # instances of the same type must render identically in two processes.
    class _Opaque:
        pass

    first, second = _Opaque(), _Opaque()
    assert stable_repr(first) == stable_repr(second)
    assert re.search(r"0x[0-9a-fA-F]", stable_repr(first)) is None


def test_anchor_set_stable_repr_is_hash_order_independent() -> None:
    """An ``AnchorSet``'s frozenset fields must render canonically."""
    from paxman.core.grammar.anchors import AnchorSet
    from paxman.core.grammar.matchers._stable import stable_repr

    a = AnchorSet(literals=frozenset({"x", "y"}), key_sets=(frozenset({"p", "q"}),))
    b = AnchorSet(literals=frozenset({"y", "x"}), key_sets=(frozenset({"q", "p"}),))
    assert stable_repr(a) == stable_repr(b)
    assert "0x" not in stable_repr(a)


def test_recognition_revision_is_process_stable() -> None:
    """``recognition_revision`` must be identical across processes.

    The revision hashes every matcher's compiled payload. Several payloads
    were rendered with ``repr()`` — which for a ``frozenset[str]`` follows
    hash order and therefore varies with ``PYTHONHASHSEED``. A revision that
    changes between two runs of the same library snapshot cannot be used to
    tell "different library" from "different process".
    """
    import os
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    script = (
        "import paxman\n"
        "from paxman.core.discovery import freeze_registry, get_recognition_revision\n"
        "paxman.register_all_shipped()\n"
        "freeze_registry()\n"
        "print(get_recognition_revision())\n"
    )
    revisions: set[str] = set()
    for seed in ("0", "1", "12345"):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = seed
        completed = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(repo_root),
            env=env,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        revisions.add(completed.stdout.strip())
    assert len(revisions) == 1, (
        "recognition_revision varies across processes "
        f"(PYTHONHASHSEED 0/1/12345): {sorted(revisions)}"
    )
    assert revisions != {"0"}
