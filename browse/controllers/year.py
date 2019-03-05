"""Handle requests for info about one year of archive activity"""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple, Union

from werkzeug.exceptions import BadRequest
from flask import current_app, url_for

from arxiv import status, taxonomy
from browse.domain.listing import MonthCount, ListingCountResponse
from browse.controllers.list_page import get_listing_service
from browse.controllers.years_operating import years_operating, stats_by_year


def year_page(archive_id: str, year: int) -> Any:
    """Get year page for archive.

    Parameters
    ----------
    archive : str
    Must be an arXiv archive identifier.

    year: int
    Must be a two or four digit year.

    Returns
    -------
    dict
        Search result response data.
    int
        HTTP status code.
    dict
        Headers to add to the response.
    """

    if year > date.today().year:
        raise BadRequest("Bad year.")

    if year < 100:
        if year >= 91:
            year = 1900 + year
        else:
            year = 2000 + year

    if archive_id not in taxonomy.ARCHIVES:
        raise BadRequest("Unknown archvie.")
    else:
        archive = taxonomy.ARCHIVES[archive_id]

    listing_service = get_listing_service(current_app)
    month_listing = listing_service.monthly_counts(archive_id, year)

    for month in month_listing['month_counts']:
        month['art'] = ascii_art_month(archive_id, month)
        yymm = month['year'] + month['month']
        month['yymm'] = yymm
        month['url'] = url_for('browse.list_articles',
                               context=archive_id, subcontext=yymm)

    response_data: Dict[str, Any] = {
        'archive_id': archive_id,
        'archive': archive,
        'months': month_listing['month_counts'],
        'listing': month_listing,
        'year': str(year),
        # TODO need to get rid of current year from this list?
        'stats_by_year': stats_by_year(archive_id, archive, years_operating(archive)),
    }
    response_headers: Dict[str, Any] = {}

    response_status = status.HTTP_200_OK

    return response_data, response_status, response_headers


ASCII_ART_STEP = 20
ASCII_ART_CHR = '|'
ASCII_ART_URL_STEP = 100


def ascii_art_month(archive_id: str, month: MonthCount) -> Tuple[str, Union[str, None]]:
    """Make ascii art for a MonthCount."""
    tot = month['new'] + month['cross']
    yymm = month['year'] + month['month']

    def makestep(idx):
        if idx % ASCII_ART_URL_STEP == 0:
            return (ASCII_ART_CHR,
                    url_for('browse.list_articles',
                            context=archive_id, subcontext=yymm))
        else:
            return (ASCII_ART_CHR, None)

    art = [makestep(idx) for idx in range(0, tot, ASCII_ART_STEP)]

    # TODO not sure what the ! means, check legacy
    if tot % ASCII_ART_STEP != 0:  # still have stuff at end
        art.append(('!', None))

    return art
