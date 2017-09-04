from flask import request
from flask_restplus import Api, Resource

from app import app
from relevant_keywords.top_keyword import TopKeywords
from util.log import get_logger

logger = get_logger('TopKeywordsAPI')

api = Api(app, doc='/doc/', version='1.0', title='Top Keywords')

crawler_endpoint = 'http://localhost:8888/page/extract'
top_keyword = TopKeywords(crawler_endpoint)

ns = api.namespace('keyword', 'Top Keywords')


@ns.route('/top')
class TopKeywordsResource(Resource):
    """
    Top keywords
    """

    @api.doc(params={'urls': 'Urls separate by comma',
                     'max_df': 'Float in range [0.0, 1.0] or int, default=`0.9`. '
                               'When building the vocabulary ignore terms that have a document frequency strictly '
                               'higher than the given threshold. If float, '
                               'the parameter represents a proportion of documents, integer absolute counts.',
                     'min_df': 'Float in range [0.0, 1.0] or int, default=`0.3`. '
                               'When building the vocabulary ignore terms that have a document frequency strictly '
                               'lower than the given threshold. This value is also called cut-off in the literature. '
                               'If float, the parameter represents a proportion of documents, integer absolute counts.',
                     'max_voc': 'Num of vocabulary to keep, default is `200`',
                     'top_n': 'Top n keywords, default is `20`'})
    def get(self):
        """
        Get top keywords from urls
        """
        result = {
            'ok': True,
            'top_keywords': {},
            'crawl_status': {}
        }
        try:
            urls = check_not_empty('urls')
            top_n = request.values.get('top_n', 20)
            min_df = request.values.get('min_df', 0.3)
            max_df = request.values.get('max_df', 0.9)
            max_voc = request.values.get('max_voc', 200)
            result.update(top_keyword.get_top_keywords(urls=urls, top_n=top_n, min_df=min_df,
                                                       max_df=max_df, max_voc=max_voc))
        except Exception as e:
            logger.exception(e)
            result['ok'] = False
            result['message'] = e.message
            return result, 500

        return result, 200


def check_not_empty(param):
    value = request.values.get(param)
    if not value:
        raise ValueError('Param `%s` is empty', param)
    return value