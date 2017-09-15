import re

import nltk
import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from gensim.corpora import Dictionary
from gensim.models import LdaModel

from relevant_keywords.util.log import get_logger

STOP_WORDS = set(
    "a,about,above,after,again,against,all,am,an,and,any,are,aren't,as,at,be,because,been,before,being,below," \
    "between,both,but,by,can't,cannot,could,couldn't,did,didn't,do,does,doesn't,doing,don't,down,during,each," \
    "few,for,from,further,had,hadn't,has,hasn't,have,haven't,having,he,he'd,he'll,he's,her,here,here's,hers," \
    "herself,him,himself,his,how,how's,i,i'd,i'll,i'm,i've,if,in,into,is,isn't,it,it's,its,itself,let's,me," \
    "more,most,mustn't,my,myself,no,nor,not,of,off,on,once,only,or,other,ought,our,ours,out,over,own,same," \
    "shan't,she,she'd,she'll,she's,should,shouldn't,so,some,such,than,that,that's,the,their,theirs,them," \
    "themselves,then,there,there's,these,they,they'd,they'll,they're,they've,this,those,through,to,too," \
    "under,until,up,very,was,wasn't,we,we'd,we'll,we're,we've,were,weren't,what,what's,when,when's,where," \
    "where's,which,while,who,who's,whom,why,why's,with,won't,would,wouldn't,you,you'd,you'll,you're,you've," \
    "your,yours,yourself,yourselves,ourselves".split(','))

ADDITIONAL_STOP_WORDS = {'www', 'http', 'https', 'href', 'links', 'link', 'copyright', 'style', 'function',
                         'tags', 'corporate', 'sort', 'details', 'detail', 'comment', 'comments', 'reviews', 'review',
                         'icon', 'footer', 'icon', 'body', 'begin', 'data', 'stylesheet', 'javascript', 'html', 'font',
                         'display'}

STOP_WORDS = STOP_WORDS | ADDITIONAL_STOP_WORDS


def generate_ngram(words, min_ngram, max_ngram):
    result = []
    for i in range(min_ngram, max_ngram + 1):
        result += (' '.join(_) for _ in nltk.ngrams(words, i))

    return result


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
           and token not in STOP_WORDS \
           and not is_number(clean_token(token))


def clean_token(token):
    return re.sub(r'[\W\-]', ' ', token)


def tokenize(text):
    text = ' '.join([clean_token(token) for token in text.split() if is_valid_token(token)])
    return [token.strip() for token in text.split() if token.strip() and is_valid_token(token.strip())]


class TopKeywords(object):
    METRIC_TFIDF = 'tfidf'
    METRIC_COUNT = 'count'
    METRIC_LDA = 'lda'

    EXTRACTORS = {'dragnet', 'goose', 'goose_dragnet', 'readability', 'selective', 'all_text'}

    def __init__(self, crawler_endpoint):
        self.crawler_endpoint = crawler_endpoint
        self.logger = get_logger(self.__class__.__name__)
        self.supported_metrics = {self.METRIC_TFIDF, self.METRIC_COUNT, self.METRIC_LDA}
        self.crawler_user_agent = None

    def get_supported_metric_names(self):
        return ', '.join('`%s`' % m for m in self.supported_metrics)

    def set_crawler_user_agent(self, user_agent):
        self.crawler_user_agent = user_agent

    def get_supported_extractors(self):
        return ', '.join('`%s`' % e for e in self.EXTRACTORS)

    def _crawl(self, urls, extractor):
        payload = {
            'urls': urls,
            'extractor': extractor,
            'cache': 1,
            'user_agent': self.crawler_user_agent
        }
        response = requests.post(url=self.crawler_endpoint, data=payload)
        if not response.ok:
            raise RuntimeError('Call crawler api error: %s - %s' % (response.status_code, response.reason))
        url_pages = response.json()
        failed_crawl = []
        contents = []
        for url, page in url_pages['pages']:
            if page.get('ok'):
                contents.append(page['content'])
            else:
                failed_crawl.append({
                    'url': url,
                    'error': page['error'],
                    'code': page['code']
                })

        return {
            'contents': contents,
            'crawl_status': {
                'failed_count': len(failed_crawl),
                'succeed_count': len(urls.split(',')) - len(failed_crawl),
                'failed_urls': failed_crawl
            }
        }

    def get_top_keywords(self, urls, extractor='all_text', top_n=20, metric='tfidf', min_df=0.3, max_df=0.9,
                         max_voc=200, min_ngram=1, max_ngram=1):

        if extractor not in self.EXTRACTORS:
            raise RuntimeError('Extractor `%s` is not supported, accepted are %s' %
                               (extractor, self.get_supported_extractors()))

        if metric not in self.supported_metrics:
            raise RuntimeError('Metric name `%s` is not supported, accepted are %s' %
                               (metric, self.get_supported_metric_names()))

        crawled = self._crawl(urls, extractor)
        contents = crawled['contents']
        top_keywords = []
        if metric == self.METRIC_TFIDF:
            top_keywords = self._get_top_by_tfidf_score(contents, top_n, min_df, max_df, max_voc, min_ngram, max_ngram)
        elif metric == self.METRIC_COUNT:
            top_keywords = self._get_top_by_count(contents, top_n, min_ngram, max_ngram)
        elif metric == self.METRIC_LDA:
            top_keywords = self._get_top_lda_topics(contents, top_n, min_ngram, max_ngram)

        return {
            'top_keywords': top_keywords,
            'crawl_status': crawled['crawl_status']
        }

    @staticmethod
    def _get_top_by_tfidf_score(contents, top_n, min_df=0.3, max_df=0.9,
                                max_voc=200, min_ngram=1, max_ngram=1):
        vectorized = TfidfVectorizer(tokenizer=tokenize, stop_words='english', ngram_range=(min_ngram, max_ngram),
                                     min_df=min_df, max_df=max_df, max_features=max_voc)
        vectorized.fit_transform(contents)
        features = vectorized.get_feature_names()
        indices = np.argsort(vectorized.idf_)[::-1]
        return [(features[i], vectorized.idf_[i]) for i in indices[:top_n]]

    @staticmethod
    def _get_top_by_count(contents, top_n, min_ngram, max_ngram):
        # Tokenize and filter stop words
        for idx, content in enumerate(contents):
            content = content.lower()
            contents[idx] = generate_ngram(tokenize(content), min_ngram, max_ngram)

        # Counting keywords
        kw_count = {}
        for content in contents:
            for kw in content:
                if kw in kw_count:
                    kw_count[kw] += 1
                else:
                    kw_count[kw] = 1

        # Short and get most occurring keywords
        return sorted(kw_count, key=kw_count.__getitem__, reverse=True)[:top_n]

    @staticmethod
    def _get_top_lda_topics(contents, top_n, min_ngram, max_ngram):
        # Tokenize and filter stop words
        for idx, content in enumerate(contents):
            content = content.lower()
            contents[idx] = generate_ngram(tokenize(content), min_ngram, max_ngram)

        dictionary = Dictionary(contents)
        dictionary.filter_extremes(no_below=3, no_above=0.9)
        corpus = [dictionary.doc2bow(content) for content in contents]
        if not corpus or not dictionary.token2id:
            raise RuntimeError('Empty corpus')

        lda = LdaModel(corpus=corpus, id2word=dictionary, passes=20, num_topics=top_n)
        top_topics = lda.print_topics(num_topics=top_n)
        return [t[1] for t in top_topics]
