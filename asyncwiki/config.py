
__all__ = (
    "wiki_search_url",
    "wiki_page_url",
    "title_tag",
    "summary_tag",
    "page_url_tag",
    "srtitle_tag_name",
    "simple_results_tag",
    "default_answer_template",
    "wiki_summary_cut_len",
    "wiki_summary_len_threshold",
    "query_clean_list"
)

# URL to Wikipedia api and page
wiki_search_url = "https://api.wikimedia.org/core/v1/wikipedia/{}/search/{}"  # Add language code and endpoint
wiki_page_url = "https://{}.wikipedia.org/wiki/{}"  # Add language code ang page key

# Template tags
title_tag = "{title}"
summary_tag = "{summary}"
page_url_tag = "{page_url}"
srtitle_tag_name = "srtitle"  # Should use how: <srtitle>
simple_results_tag = "{simple_results}"

# Default template for WikiResult
default_answer_template = (
    f"===<b><i>{title_tag}</i></b>===\n\n"  # Title

    f"{summary_tag}\n"  # Summary
    f"<i><a href='{page_url_tag}'>Оригинал...</a></i>\n\n"  # Links to original article

    f"<{srtitle_tag_name}>===<b><i>Похожие результаты</i></b>===\n</{srtitle_tag_name}>"  # Simple results
    f"{simple_results_tag}"  # Links to simple articles
)

# Number of sign start with text will cut
wiki_summary_cut_len = 200
wiki_summary_len_threshold = 10

# Words that will be removed
query_clean_list = [
    "what", "where", "who", "why", "when", "that", "this", "how",
    "что", "такое", "где", "кто", "зачем", "куда", "когда", "такие", "такой", "такого", "как", "какой", "такая",
]
