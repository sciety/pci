import pytest

from controllers.content import EvaluationType, _decode_evaluation_doi

test_cases = [
    {
        "path": "10.1234/xyz.rev12",
        "expected": {
            "recommendation_doi": "10.1234/xyz",
            "evaluation_type": EvaluationType.REVIEW,
            "round_number": "1",
            "evaluation_number": "2",
        },
    },
    {
        "path": "10.1234/xyz.d1",
        "expected": {
            "recommendation_doi": "10.1234/xyz",
            "evaluation_type": EvaluationType.DECISION,
            "round_number": "1",
            "evaluation_number": "",
        },
    },
    {
        "path": "10.1234/xyz.ar3",
        "expected": {
            "recommendation_doi": "10.1234/xyz",
            "evaluation_type": EvaluationType.AUTHOR_RESPONSE,
            "round_number": "3",
            "evaluation_number": "",
        },
    },
    {
        "path": "10.1234/xyz",
        "expected": {
            "recommendation_doi": "10.1234/xyz",
            "evaluation_type": EvaluationType.RECOMMENDATION,
            "round_number": None,
            "evaluation_number": None,
        },
    },
]


@pytest.mark.parametrize("case", test_cases, ids=lambda c: c["path"])
def test_decode_evaluation_doi(case):
    result = _decode_evaluation_doi(case["path"])
    assert result == case["expected"]
