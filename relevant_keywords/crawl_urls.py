import pandas as pd
from parser.content_getter import ContentGetter
from parser.crawler import PageCrawler
from parser.extractor import GooseDragnetPageExtractor
from pprint import pprint

FIELD_KEYWORD = 'Keyword'
FIELD_URL = 'Landing Page'
FIELD_URL_PAGE_CONTENT = 'Landing Page Content'
FIELD_URL_CRAWL_STATUS = 'Crawl Status'
FIELD_URL_TYPE = 'Url Type'
URL_TYPE_WEB = 'Web'
URL_TYPE_NEWS = 'News'

crawler = PageCrawler()
extractor = GooseDragnetPageExtractor()
content_getter = ContentGetter(crawler=crawler, extractor=extractor)

if __name__ == '__main__':
    url_file = 'data/top_10_ranking_keywords.xlsx'
    df = pd.read_excel(url_file)
    urls = set()
    for idx, row in df.iterrows():
        url = row[FIELD_URL]
        urls.add(url)
        # if idx == 5:
        #     break

    url_page_contents = content_getter.process(urls)
    for idx, row in df.iterrows():
        url = row[FIELD_URL]
        crawled_page = url_page_contents.get(url)
        # if not crawled_page:
        #     continue
        df.loc[idx, FIELD_URL_PAGE_CONTENT] = crawled_page['content']
        if crawled_page['error']:
            df.loc[idx, FIELD_URL_CRAWL_STATUS] = crawled_page['error']
        else:
            df.loc[idx, FIELD_URL_CRAWL_STATUS] = 'Crawl successfully'

    df.to_excel(url_file[:-5] + '.out.xlsx', index=False, encoding='utf-8')
