from gluon.http import HTTP # type: ignore
from gluon.contrib.markdown import WIKI
import re

def _decode_evaluation_doi(path: str):
    match = re.match(r'^(.*)\.(rev|d|ar)(\d)(\d+)$', path)
    if not match:
        return None
    recommendation_doi, evaluation_type, round_number, evaluation_number = match.groups()
    return dict(
        recommendation_doi=recommendation_doi,
        evaluation_type=evaluation_type,
        round_number=round_number,
        evaluation_number=evaluation_number
    )


def doi():
    if request.args is None:
        return HTTP(400, "No DOI supplied")

    path_param = '/'.join(request.args)
    decodedRequest = _decode_evaluation_doi(path_param)

    if decodedRequest is None:
        raise HTTP(400, "Invalid DOI")

    markdownContent = None
    if decodedRequest['evaluation_type'] == 'd':
        markdownContent = db.get_decision_text(decodedRequest['recommendation_doi'], decodedRequest['round_number'])
    if decodedRequest['evaluation_type'] == 'ar':
        raise HTTP(400, "Unsupported evaluation type")
    if decodedRequest['evaluation_type'] == 'rev':
        markdownContent = db.get_review_text(decodedRequest['recommendation_doi'], decodedRequest['round_number'], decodedRequest['evaluation_number'])
    if markdownContent is None:
        raise HTTP(404, "No such review")

    contentAsHtml = WIKI(markdownContent, safe_mode="")

    return contentAsHtml
