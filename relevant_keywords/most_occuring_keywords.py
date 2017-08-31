import json

import nltk
import pandas as pd
from gensim.corpora import Dictionary
from gensim.models import LdaModel

from relevant_keywords.nlp.tokenizer import GeneralTokenizer

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

FIELD_KEYWORD = 'Keyword'
FIELD_URL = 'Landing Page'
FIELD_URL_PAGE_CONTENT = 'Landing Page Content'
FIELD_URL_CRAWL_STATUS = 'Crawl Status'
FIELD_URL_TYPE = 'Url Type'
URL_TYPE_WEB = 'Web'
URL_TYPE_NEWS = 'News'

STOP_WORDS = "a,about,above,after,again,against,all,am,an,and,any,are,aren't,as,at,be,because,been,before,being,below," \
             "between,both,but,by,can't,cannot,could,couldn't,did,didn't,do,does,doesn't,doing,don't,down,during,each," \
             "few,for,from,further,had,hadn't,has,hasn't,have,haven't,having,he,he'd,he'll,he's,her,here,here's,hers," \
             "herself,him,himself,his,how,how's,i,i'd,i'll,i'm,i've,if,in,into,is,isn't,it,it's,its,itself,let's,me," \
             "more,most,mustn't,my,myself,no,nor,not,of,off,on,once,only,or,other,ought,our,ours,out,over,own,same," \
             "shan't,she,she'd,she'll,she's,should,shouldn't,so,some,such,than,that,that's,the,their,theirs,them," \
             "themselves,then,there,there's,these,they,they'd,they'll,they're,they've,this,those,through,to,too," \
             "under,until,up,very,was,wasn't,we,we'd,we'll,we're,we've,were,weren't,what,what's,when,when's,where," \
             "where's,which,while,who,who's,whom,why,why's,with,won't,would,wouldn't,you,you'd,you'll,you're,you've," \
             "your,yours,yourself,yourselves,ourselves".split(',')

ADDITIONAL_STOP_WORDS = {'http', 'com', 'https', 'www'}

STOP_WORDS = set(STOP_WORDS).union(ADDITIONAL_STOP_WORDS)


def generate_ngram(words, min_ngram, max_ngram):
    result = []
    for i in range(min_ngram, max_ngram + 1):
        result += (' '.join(_) for _ in nltk.ngrams(words, i))

    return result


def nltk_stopwords():
    return set(nltk.corpus.stopwords.words('english'))

if __name__ == '__main__':
    url_file = 'data/top_10_ranking_keywords.out.xlsx'
    df = pd.read_excel(url_file)
    keywords = {}
    for idx, row in df.iterrows():
        keyword = row[FIELD_KEYWORD]
        url_content = row[FIELD_URL_PAGE_CONTENT]
        if pd.isnull(url_content):
            print 'Empty url content for row: %d' % (idx + 1)
        if row[FIELD_URL_CRAWL_STATUS] != 'Crawl successfully':
            print 'Url %s has empty content' % row[FIELD_URL]
            continue

        if keyword in keywords:
            keywords[keyword].append(url_content)
        else:
            keywords[keyword] = [url_content]

    tokenizer = GeneralTokenizer()
    keyword_topics = []
    stop_words = nltk_stopwords().union(STOP_WORDS)
    for keyword, docs in keywords.iteritems():
        print 'Get most topics for keyword: %s' % keyword
        # Tokenize and filter stop words
        for idx, doc in enumerate(docs):
            docs[idx] = generate_ngram([w for w in tokenizer.tokenize(doc) if w not in stop_words and len(w) > 2], 1, 3)

        # Counting terms
        terms_count = {}
        for doc in docs:
            for term in doc:
                if term in terms_count:
                    terms_count[term] += 1
                else:
                    terms_count[term] = 1

        # Short and get most occurring terms
        most_occurring_terms = sorted(terms_count, key=terms_count.__getitem__, reverse=True)[:20]
        print most_occurring_terms
        keyword_topics.append((keyword, ' + '.join('%d * %s' % (terms_count[k], k) for k in most_occurring_terms)))

    df = pd.DataFrame(data=keyword_topics, columns=['keyword', 'top_topics'])
    df.to_excel('data/keyword_topics_by_counting.xlsx', index=False, encoding='utf-8')
