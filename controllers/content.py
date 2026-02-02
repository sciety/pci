import re
from enum import Enum

from gluon.contrib.markdown import WIKI
from gluon.http import HTTP  # type: ignore

from models.recommendation import Recommendation
from models.review import Review

class EvaluationType(Enum):
    REVIEW = "rev"
    DECISION = "d"
    AUTHOR_RESPONSE = "ar"
    RECOMMENDATION = "recommendation"


# We assume there are never more than nine review rounds
def _decode_evaluation_doi(path: str):
    match = re.match(r"^(.*)\.(rev|d|ar)(\d)(\d*)$", path)
    if not match:
        return dict(
            recommendation_doi=path,
            evaluation_type=EvaluationType("recommendation"),
            round_number=None,
            evaluation_number=None,
        )
    recommendation_doi, evaluation_type, round_number, evaluation_number = (
        match.groups()
    )
    return dict(
        recommendation_doi=recommendation_doi,
        evaluation_type=EvaluationType(evaluation_type),
        round_number=round_number,
        evaluation_number=evaluation_number,
    )


def _get_markdown_content_based_on_evaluation_type(decoded_request):
    recommendation = Recommendation.get_by_doi(decoded_request["recommendation_doi"])
    lastRecommendation = recommendation[-1]
    if recommendation == None:
        return None
    match decoded_request["evaluation_type"]:
        case EvaluationType.DECISION:
            if decoded_request["evaluation_number"] != "":
                raise HTTP(400, "Invalid DOI")
            reviewRoundDecision = recommendation[int(decoded_request["round_number"]) - 1]
            if reviewRoundDecision == None:
                return None
            return reviewRoundDecision.recommendation_comments

        case EvaluationType.AUTHOR_RESPONSE:
            if decoded_request["evaluation_number"] != "":
                raise HTTP(400, "Invalid DOI")
            reviewRoundDecision = recommendation[int(decoded_request["round_number"]) - 1]
            if reviewRoundDecision == None:
                return None
            return reviewRoundDecision.reply

        case EvaluationType.REVIEW:
            relevantRecommendation = recommendation[int(decoded_request["round_number"]) - 1]
            reviewsForRecommendationDescending = Review.get_by_recommendation_id(relevantRecommendation.id)
            reviewLocationInTheArray = int(decoded_request["evaluation_number"]) - 1
            relevantReview = reviewsForRecommendationDescending[reviewLocationInTheArray]
            return relevantReview.review
        
        case EvaluationType.RECOMMENDATION:
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