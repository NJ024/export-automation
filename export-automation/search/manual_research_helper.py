"""
search/manual_research_helper.py — generates ready-to-use search strings for
the manual LinkedIn/Facebook research step (see linkedin_search.py and
facebook_search.py for why discovery there is manual, not scraped).
"""

from config import SEARCH_KEYWORD


def suggest_linkedin_queries(keyword=None, countries=None):
    keyword = keyword or SEARCH_KEYWORD
    countries = countries or [""]
    queries = []
    for country in countries:
        suffix = f" {country}".rstrip()
        queries.extend([
            f'site:linkedin.com/in "{keyword}" importer{suffix}',
            f'site:linkedin.com/in "{keyword}" buyer{suffix}',
            f'site:linkedin.com/company "{keyword}" wholesale{suffix}',
        ])
    return queries


def suggest_facebook_queries(keyword=None, countries=None):
    keyword = keyword or SEARCH_KEYWORD
    countries = countries or [""]
    queries = []
    for country in countries:
        suffix = f" {country}".rstrip()
        queries.extend([
            f'site:facebook.com "{keyword}" shop{suffix}',
            f'site:facebook.com "{keyword}" wholesale{suffix}',
            f'site:facebook.com groups "{keyword}" buyers{suffix}',
        ])
    return queries


if __name__ == "__main__":
    print("LinkedIn queries:")
    for q in suggest_linkedin_queries(countries=["USA", "Germany"]):
        print(" ", q)
    print("\nFacebook queries:")
    for q in suggest_facebook_queries(countries=["USA", "Germany"]):
        print(" ", q)
