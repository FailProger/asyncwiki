
__all__ = (
    "wiki_search_url",
    "wiki_page_url",
    "wiki_answer_template",
    "wiki_summary_limit",
    "wiki_query_clean_list"
)

# URL to Wikipedia api and page
wiki_search_url = "https://api.wikimedia.org/core/v1/wikipedia/{}/search/{}"  # Add language code and endpoint
wiki_page_url = "https://{}.wikipedia.org/wiki/{}"  # Add language code ang page key

# List of text elements for WikiResult
wiki_answer_template = [
    "===<b><i>{}</i></b>===\n\n",  # Title

    "{}\n",  # Summary
    "<i><a href='{}'>Оригинал...</a></i>\n\n",  # Links to original article

    "===<b><i>Похожие результаты</i></b>===\n",  # Simple results
    "{}"  # Links to simple articles
]

# Number of sign start with text will cut
wiki_summary_limit = 200

# Words that will be removed
wiki_query_clean_list = [
    "what", "where", "who", "why", "when", "that", "this", "how",
    "что", "такое", "где", "кто", "зачем", "куда", "когда", "такие", "такой", "такого", "как", "какой", "такая",
]
