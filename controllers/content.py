from gluon.http import HTTP # type: ignore
from gluon.contrib.markdown import WIKI
from enum import Enum
import re

class EvaluationType(Enum):
    REVIEW = "rev"
    DECISION = "d"
    AUTHOR_RESPONSE = "ar"
# >>> def handle_semaphore(light):
# ...     match light:
# ...         case Semaphore.RED:
# ...             print("You must stop!")
# ...         case Semaphore.YELLOW:
# ...             print("Light will change to red, be careful!")
# ...         case Semaphore.GREEN:
# ...             print("You can continue!")
# ...

# >>> handle_semaphore(Semaphore.GREEN)
# You can continue!

# >>> handle_semaphore(Semaphore.YELLOW)
# Light will change to red, be careful!

# >>> handle_semaphore(Semaphore.RED)
# You must stop!


# We assume there are never more than nine review rounds
def _decode_evaluation_doi(path: str):
    match = re.match(r'^(.*)\.(rev|d|ar)(\d)(\d*)$', path)
    if not match:
        return None
    recommendation_doi, evaluation_type, round_number, evaluation_number = match.groups()
    return dict(
        recommendation_doi=recommendation_doi,
        evaluation_type=evaluation_type,
        round_number=round_number,
        evaluation_number=evaluation_number
    )

def _get_markdown_content_based_on_evaluation_type(decoded_request: str):
    match decoded_request['evaluation_type']:
        case EvaluationType.DECISION.value:
            if decoded_request['evaluation_number'] != '':
                raise HTTP(400, "Invalid DOI")
            return db.get_decision_text(decoded_request['recommendation_doi'], decoded_request['round_number'])
        case EvaluationType.AUTHOR_RESPONSE.value:
            raise HTTP(400, "Unsupported evaluation type")
        case EvaluationType.REVIEW.value:
            return db.get_review_text(decoded_request['recommendation_doi'], decoded_request['round_number'], decoded_request['evaluation_number'])
    return None

def doi():
    if request.args is None:
        return HTTP(400, "No DOI supplied")

    path_param = '/'.join(request.args)
    decodedRequest = _decode_evaluation_doi(path_param)
    if decodedRequest is None:
        raise HTTP(400, "Invalid DOI")

    markdownContent = _get_markdown_content_based_on_evaluation_type(decodedRequest)
    if markdownContent is None:
        raise HTTP(404, "No such review")

    contentAsHtml = WIKI(markdownContent, safe_mode="")

    return contentAsHtml
