import re

import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer

stop_words = {'www', 'http', 'https', 'href', 'links', 'link', 'copyright', 'style', 'function',
              'tags', 'corporate', 'sort', 'details', 'detail', 'comment', 'comments', 'reviews', 'review',
              'icon', 'footer', 'icon', 'body', 'begin', 'data', 'stylesheet'}


def is_number(text):
    try:
        float(text)
        return True
    except:
        return False


def is_valid_token(token):
    return not token.startswith('<') \
           and not token.endswith('>') \
           and not token.startswith('[') \
           and not token.endswith(']') \
           and len(token) > 3 \
           and token not in stop_words \
           and not is_number(clean_token(token))


def clean_token(token):
    return re.sub(r'[\W\-]', ' ', token)


def tokenize(text):
    text = ' '.join([clean_token(token) for token in text.split() if is_valid_token(token)])
    return [token.strip() for token in text.split() if token.strip() and is_valid_token(token.strip())]


class TopKeywords(object):
    def __init__(self, crawler_endpoint):
        self.crawler_endpoint = crawler_endpoint

    def _crawl(self, urls):
        payload = {
            'urls': urls,
            'extractor': 'all_text'
        }
        response = requests.post(url=self.crawler_endpoint, data=payload)
        url_pages = response.json()
        failed_crawl = []
        contents = []
        for url, page in url_pages['pages']:
            if page.get('ok'):
                contents.append(page['content'])
            else:
                failed_crawl.append({
                    'url': url,
                    'error': page['error']
                })

        return {
            'contents': contents,
            'crawl_status': {
                'failed_count': len(failed_crawl),
                'succeed_count': len(urls.split(',')) - len(failed_crawl),
                'failed_urls': failed_crawl
            }
        }

    def get_top_keywords(self, urls, top_n=20, min_df=0.3, max_df=0.9, max_voc=200):
        crawled = self._crawl(urls)
        vectorized = TfidfVectorizer(tokenizer=tokenize, stop_words='english',
                                     min_df=min_df, max_df=max_df, max_features=max_voc)
        vectorized.fit_transform(crawled['contents'])
        features = vectorized.get_feature_names()
        indices = np.argsort(vectorized.idf_)[::-1]
        top_keywords = [(features[i], vectorized.idf_[i]) for i in indices[:top_n]]
        return {
            'top_keywords': top_keywords,
            'crawl_status': crawled['crawl_status']
        }
