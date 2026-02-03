from dataclasses import dataclass
from typing import Iterator, Optional
from unittest.mock import MagicMock, patch

import pytest
from gluon.http import HTTP  # type: ignore

import controllers.content as controllers_module
from controllers.content import (
    EvaluationType,
    _decode_evaluation_doi,
    _get_markdown_content_based_on_evaluation_type,
)

@dataclass(frozen=True)
class RecommendationMock:
    recommendation_comments: Optional[str] = None
    reply: Optional[str] = None


ANY_EVALUATION_TYPE = EvaluationType.REVIEW

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


@pytest.fixture(name="recommendation_mock")
def _recommendation_mock() -> Iterator[MagicMock]:
    with patch.object(controllers_module, "Recommendation") as mock:
        yield mock


@pytest.mark.parametrize("case", test_cases, ids=lambda c: c["path"])
def test_decode_evaluation_doi(case):
    result = _decode_evaluation_doi(case["path"])
    assert result == case["expected"]


class TestGetMarkdownContentBasedOnEvaluationType:
    def test_should_return_none_if_there_are_no_recommendations_expressed_as_none(
        self,
        recommendation_mock: MagicMock,
    ):
        recommendation_mock.get_by_doi.return_value = None
        result = _get_markdown_content_based_on_evaluation_type(
            {
                "recommendation_doi": "10.1234/xyz",
                "evaluation_type": ANY_EVALUATION_TYPE,
                "round_number": "1",
                "evaluation_number": "2",
            }
        )
        recommendation_mock.get_by_doi.assert_called_once_with("10.1234/xyz")
        assert result is None

    def test_should_return_none_if_there_are_no_recommendations_expressed_as_an_empty_list(
        self,
        recommendation_mock: MagicMock,
    ):
        recommendation_mock.get_by_doi.return_value = []
        result = _get_markdown_content_based_on_evaluation_type(
            {
                "recommendation_doi": "10.1234/xyz",
                "evaluation_type": ANY_EVALUATION_TYPE,
                "round_number": "1",
                "evaluation_number": "2",
            }
        )
        recommendation_mock.get_by_doi.assert_called_once_with("10.1234/xyz")
        assert result is None

    class TestDecisionType:
        def test_should_raise_exception_for_decisions_that_have_evaluation_number(
            self,
            recommendation_mock: MagicMock,
        ):
            recommendation_mock.get_by_doi.return_value = [{}]
            with pytest.raises(HTTP):
                _get_markdown_content_based_on_evaluation_type(
                    {
                        "recommendation_doi": "10.1234/xyz",
                        "evaluation_type": EvaluationType.DECISION,
                        "round_number": "1",
                        "evaluation_number": "3",
                    }
                )
        
        def test_requested_round_does_not_exist(
            self,
            recommendation_mock: MagicMock,
        ):
            recommendation_mock.get_by_doi.return_value = [{}]
            result = _get_markdown_content_based_on_evaluation_type(
                {
                    "recommendation_doi": "10.1234/xyz",
                    "evaluation_type": EvaluationType.DECISION,
                    "round_number": "2",
                    "evaluation_number": "",
                }
            )
            recommendation_mock.get_by_doi.assert_called_once_with("10.1234/xyz")
            assert result is None

        def test_recommendation_comments_of_rounds_before_the_last_are_the_decision_content(
            self,
            recommendation_mock: MagicMock,
        ):
            recommendation_mock.get_by_doi.return_value = [
                RecommendationMock(), 
                RecommendationMock(recommendation_comments="Foo bar"),
                RecommendationMock()
            ]
            result = _get_markdown_content_based_on_evaluation_type(
                {
                    "recommendation_doi": "10.1234/xyz",
                    "evaluation_type": EvaluationType.DECISION,
                    "round_number": "2",
                    "evaluation_number": "",
                }
            )
            recommendation_mock.get_by_doi.assert_called_once_with("10.1234/xyz")
            assert result is "Foo bar"
    
    class TestAuthorResponseType:
        def test_should_raise_exception_for_author_responses_that_have_evaluation_number(
            self,
            recommendation_mock: MagicMock,
        ):
            recommendation_mock.get_by_doi.return_value = [{}]
            with pytest.raises(HTTP):
                _get_markdown_content_based_on_evaluation_type(
                    {
                        "recommendation_doi": "10.1234/xyz",
                        "evaluation_type": EvaluationType.AUTHOR_RESPONSE,
                        "round_number": "1",
                        "evaluation_number": "2",
                    }
                )

        def test_should_return_none_if_requested_round_does_not_exist(
            self,
            recommendation_mock: MagicMock,
        ):
            recommendation_mock.get_by_doi.return_value = [{}]
            result = _get_markdown_content_based_on_evaluation_type(
                {
                    "recommendation_doi": "10.1234/xyz",
                    "evaluation_type": EvaluationType.AUTHOR_RESPONSE,
                    "round_number": "2",
                    "evaluation_number": "",
                }
            )
            recommendation_mock.get_by_doi.assert_called_once_with("10.1234/xyz")
            assert result is None

        def test_recommendation_comments_of_rounds_before_the_last_are_the_author_response_content(
            self,
            recommendation_mock: MagicMock,
        ):
            recommendation_mock.get_by_doi.return_value = [
                RecommendationMock(),
                RecommendationMock(reply="Foo bar"),
                RecommendationMock()
            ]
            result = _get_markdown_content_based_on_evaluation_type(
                {
                    "recommendation_doi": "10.1234/xyz",
                    "evaluation_type": EvaluationType.AUTHOR_RESPONSE,
                    "round_number": "2",
                    "evaluation_number": "",
                }
            )
            recommendation_mock.get_by_doi.assert_called_once_with("10.1234/xyz")
            assert result == "Foo bar"
