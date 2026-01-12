from gluon.http import HTTP # type: ignore
from gluon.contrib.markdown import WIKI

def _decode_evaluation_doi(path: str):
    isAReview = "rev" in path
    if not isAReview:
        return None

    delimiter = ".rev"
    delimiter_start_index = path.find(delimiter)
    delimiter_stop_index = delimiter_start_index + len(delimiter)
    recommendation_doi = path[:delimiter_start_index]
    # We assume there aren't more than nine rounds of reviews
    review_round_number = path[delimiter_stop_index:][0]
    review_number = path[delimiter_stop_index:][1:]

    return dict(
       recommendation_doi=recommendation_doi,
       evaluation_type='rev',
       round_number=review_round_number,
       evaluation_number=review_number
    )


def doi():
    if request.args is None:
        return HTTP(400, "No DOI supplied")

    path_param = '/'.join(request.args)
    decodedRequest = _decode_evaluation_doi(path_param)

    if decodedRequest is None:
        raise HTTP(400, "Invalid DOI")

    reviewContentAsMarkdown = db.get_review_text(decodedRequest['recommendation_doi'], decodedRequest['round_number'], decodedRequest['evaluation_number'])
    if reviewContentAsMarkdown is None:
        raise HTTP(404, "No such review")

    reviewContentAsHtml = WIKI(reviewContentAsMarkdown, safe_mode="")

    return reviewContentAsHtml
