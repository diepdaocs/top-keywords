import re

from relevant_keywords.parser.content_getter import ContentGetter
from relevant_keywords.parser.crawler import PageCrawler
from relevant_keywords.parser.extractor import AllTextPageExtractor
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

crawler = PageCrawler()
extractor = AllTextPageExtractor()
content_getter = ContentGetter(crawler=crawler, extractor=extractor)


def main():
    # Crawl web pages
    urls = [
        'https://www.etsy.com/featured/personalized-holiday-and-christmas-gifts',
        'http://www.personalizationmall.com/',
        'https://www.uncommongoods.com/gifts/personalized/personalized-gifts',
        'https://www.thingsremembered.com/personalized-gifts-for-any-occasion',
        'https://www.personalcreations.com/',
        'https://www.shutterfly.com/personalized-gifts',
        'https://www.walmart.com/cp/personalized-gifts/133224',
        'https://www.gifts.com/categories/personalized-gifts/1vV',
        'https://www.agiftpersonalized.com/',
        'http://www.hallmark.com/personalized-gift'
    ]
    url_page_contents = content_getter.process(urls)
    contents = []
    for url in urls:
        crawled_page = url_page_contents.get(url)
        print '###############################Start content for url: %s################################' % url
        if not crawled_page['error']:
            content = crawled_page['content']
            content = re.sub(r'[^\w\s]+', '', content)
            content = re.sub(r'(\t|\s)+', ' ', content)
            contents.append(content)
            print content
        elif not crawled_page['content']:
            print '- Url "%s" has empty content'
        else:
            print '- Crawl url "%s" error: %s' % (url, crawled_page['error'])
        print '###############################End content for url: %s################################' % url

    # Get top keywords
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
    vectorizer.fit_transform(contents)
    indices = np.argsort(vectorizer.idf_)[::-1]
    features = vectorizer.get_feature_names()
    print '- Top 10 keywords'
    top_n = 100
    top_keywords = [features[i] for i in indices[:top_n]]
    for keyword in top_keywords:
        print keyword

if __name__ == '__main__':
    main()
