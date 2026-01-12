from gluon.http import HTTP # type: ignore
from gluon.contrib.markdown import WIKI

def doi():
    path_param = '/'.join(request.args) if request.args else None
    isAReview = "rev" in path_param
    if not isAReview:
        raise HTTP(404, "DOI is not for a review")

    delimiter = ".rev"
    delimiter_start_index = path_param.find(delimiter)
    delimiter_stop_index = delimiter_start_index + len(delimiter)
    recommendation_doi = path_param[:delimiter_start_index]
    # We assume there aren't more than nine rounds of reviews
    review_round_number = path_param[delimiter_stop_index:][0]
    review_number = path_param[delimiter_stop_index:][1:]
    reviewContentAsHtml = db.get_review_text(recommendation_doi, review_round_number, review_number)
    foo = WIKI(reviewContentAsHtml, safe_mode="")
    if reviewContentAsHtml is None:
        raise HTTP(404, "No such review")

    return foo
