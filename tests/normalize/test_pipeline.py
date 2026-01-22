"""Tests for the normalization pipeline."""

import pytest

from sxact.normalize import normalize


class TestWhitespaceNormalization:
    def test_extra_spaces_in_brackets(self) -> None:
        assert normalize("T[ -a,  -b ]") == "T[-$1, -$2]"

    def test_multiple_spaces(self) -> None:
        assert normalize("A   +   B") == "A + B"

    def test_no_space_before_comma(self) -> None:
        assert normalize("T[-a ,-b]") == "T[-$1, -$2]"


class TestDummyIndexCanonicalization:
    def test_basic_indices(self) -> None:
        assert normalize("T[-a, -b]") == "T[-$1, -$2]"

    def test_different_index_names(self) -> None:
        assert normalize("T[-x, -y]") == "T[-$1, -$2]"

    def test_same_index_multiple_times(self) -> None:
        assert normalize("T[-a, -b] S[-a, -c]") == "T[-$1, -$2] S[-$1, -$3]"

    def test_mixed_up_down_indices(self) -> None:
        assert normalize("T[-a, b]") == "T[-$1, $2]"

    def test_upper_indices(self) -> None:
        assert normalize("T[a, b]") == "T[$1, $2]"


class TestTermOrdering:
    def test_sum_ordering(self) -> None:
        assert normalize("B + A") == "A + B"

    def test_multi_term_ordering(self) -> None:
        assert normalize("C + A + B") == "A + B + C"

    def test_term_with_coefficient(self) -> None:
        result = normalize("B + 2 A")
        assert result == "2 A + B"


class TestCoefficientNormalization:
    def test_explicit_multiplication(self) -> None:
        assert normalize("2*x") == "2 x"

    def test_negative_one(self) -> None:
        assert normalize("-1*x") == "-x"

    def test_positive_one(self) -> None:
        assert normalize("1*x") == "x"


class TestCombinedPipeline:
    def test_full_normalization(self) -> None:
        input_expr = "T[ -x,  -y ] + S[-y, -x]"
        result = normalize(input_expr)
        assert "T[-$1, -$2]" in result or "S[-$1, -$2]" in result
