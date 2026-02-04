from dataclasses import dataclass
import re
from enum import Enum
from typing import Literal, Optional, TypedDict

from gluon.contrib.markdown import WIKI
from gluon.http import HTTP  # type: ignore

from models.recommendation import Recommendation
from models.review import Review

class EvaluationType(Enum):
    REVIEW = "rev"
    DECISION = "d"
    AUTHOR_RESPONSE = "ar"
    RECOMMENDATION = "recommendation"

@dataclass(frozen=True)
class DecodedDecisionRequest:
    recommendation_doi: str
    round_number: int

@dataclass(frozen=True)
class DecodedAuthorResponseRequest:
    recommendation_doi: str
    round_number: int

@dataclass(frozen=True)
class DecodedReviewRequest:
    recommendation_doi: str
    round_number: int
    evaluation_number: int

@dataclass(frozen=True)
class DecodedRecommendationRequest:
    recommendation_doi: str


NewDecodedRequest = DecodedDecisionRequest | DecodedAuthorResponseRequest | DecodedReviewRequest | DecodedRecommendationRequest

# We assume there are never more than nine review rounds
def _decode_evaluation_doi(path: str) -> NewDecodedRequest:
    match = re.match(r"^(.*)\.(rev|d|ar)(\d)?(\d*)$", path)
    if not match:
        return DecodedRecommendationRequest(
            recommendation_doi=path
        )
    recommendation_doi, evaluation_type, round_number, evaluation_number = (
        match.groups()
    )
    if evaluation_type == "d":
        if evaluation_number or not round_number:
            raise HTTP(400, "Invalid DOI")
        return DecodedDecisionRequest(
            recommendation_doi=recommendation_doi,
            round_number=int(round_number),
        )
    if evaluation_type == "ar":
        if evaluation_number or not round_number:
            raise HTTP(400, "Invalid DOI")
        return DecodedAuthorResponseRequest(
            recommendation_doi=recommendation_doi,
            round_number=int(round_number)
        )
    if evaluation_type == "rev":
        if not evaluation_number:
            raise HTTP(400, "Invalid DOI")
        return DecodedReviewRequest(
            recommendation_doi=recommendation_doi,
            round_number=int(round_number),
            evaluation_number=int(evaluation_number)
        )
    # This should never happen due to regular expression
    raise HTTP(400, "Unable to decode request")


def _get_markdown_content_based_on_evaluation_type(decoded_request: NewDecodedRequest):
    recommendations = Recommendation.get_by_doi(decoded_request.recommendation_doi)
    if not recommendations:
        return None
    lastRecommendation = recommendations[-1]
    match decoded_request:
        case DecodedDecisionRequest():
            if len(recommendations) < decoded_request.round_number:
                return None
            reviewRoundDecision = recommendations[decoded_request.round_number - 1]
            return reviewRoundDecision.recommendation_comments
        case DecodedAuthorResponseRequest():
            if len(recommendations) < decoded_request.round_number:
                return None
            reviewRoundDecision = recommendations[decoded_request.round_number - 1]
            return reviewRoundDecision.reply
        case DecodedReviewRequest():
            if len(recommendations) < decoded_request.round_number:
                return None
            relevantRecommendation = recommendations[decoded_request.round_number - 1]
            reviewsForRecommendationDescending = Review.get_by_recommendation_id(relevantRecommendation.id)
            if len(reviewsForRecommendationDescending) < decoded_request.evaluation_number:
                return None
            reviewLocationInTheArray = decoded_request.evaluation_number - 1
            relevantReview = reviewsForRecommendationDescending[reviewLocationInTheArray]
            return relevantReview.review
        case DecodedRecommendationRequest():
            return lastRecommendation.recommendation_comments
    return None


def doi():
    if request.args is None:
        return HTTP(400, "No DOI supplied")

    path_param = "/".join(request.args)
    decodedRequest = _decode_evaluation_doi(path_param)
    if decodedRequest is None:
        raise HTTP(400, "Invalid DOI")

    markdown_content = _get_markdown_content_based_on_evaluation_type(decodedRequest)
    if markdown_content is None:
        raise HTTP(404, "No such review")

    contentAsHtml = WIKI(markdown_content, safe_mode="")

    return contentAsHtml
