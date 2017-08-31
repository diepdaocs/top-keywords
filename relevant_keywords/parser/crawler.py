from datetime import datetime
from multiprocessing import cpu_count
from multiprocessing.dummy import Pool

import requests
from relevant_keywords.util.utils import get_logger, get_unicode


class PageCrawler(object):

    def __init__(self, user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 '
                                  '(KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'):
        self.logger = get_logger(self.__class__.__name__)
        self.user_agent = user_agent

    def process(self, urls):
        urls = list(set(urls))
        result = {}
        if len(urls) > 2:
            # use multi thread to crawl pages
            pool = Pool(cpu_count() * 2)
            pool_results = pool.map(self._crawl_page, urls)
            # get results
            for r in pool_results:
                result.update(r)

            pool.terminate()
        else:
            for url in urls:
                result.update(self._crawl_page(url))

        return result

    def _crawl_page(self, url):
        self.logger.debug('Start crawl %s...' % url)
        result = {
            url: {
                'content': '',
                'error': False
            }
        }
        if url:
            try:
                headers = {'User-Agent': self.user_agent}
                response = requests.get(url, verify=False, timeout=10, headers=headers)
                # raise exception when something error
                if response.status_code == requests.codes.ok:
                    result[url]['content'] = response.content
                else:
                    result[url]['error'] = 'Page not found'

            except Exception as ex:
                self.logger.error('crawl_page error: %s' % ex.message)
                result[url]['error'] = str(ex.message)  # 'Page not found'
        else:
            result[url]['error'] = 'url is empty'

        self.logger.debug('End crawl %s...' % url)
        return result


class PageCrawlerWithStorage(object):

    def __init__(self, storage, user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 '
                                           '(KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'):
        self.logger = get_logger(self.__class__.__name__)
        self.storage = storage
        self.user_agent = user_agent

    def process(self, urls):
        result = {}
        urls = list(set(urls))
        # get crawled pages
        for page in self.storage.find({'_id': {'$in': urls}}):
            if page.get('crawled_date'):
                self.logger.debug('Page was crawled: ' + page['_id'])
                result[page['_id']] = page

        self.logger.info("Num of crawled urls: %s" % len(result))
        # filter crawled page
        urls = [u for u in urls if u not in result]

        self.logger.info("Remain haven't crawled urls: %s" % len(urls))

        if not urls:
            self.logger.info('All urls has been crawled')
            return result

        if len(urls) > 2:
            # use multi thread to crawl pages
            pool = Pool(cpu_count() * 2)
            self.logger.debug('Have to crawl these urls: %s' % urls)
            pool_results = pool.map(self._crawl_page, urls)
            # get results
            for r in pool_results:
                result.update(r)

            pool.close()
            pool.terminate()
        else:
            for url in urls:
                result.update(self._crawl_page(url))

        return result

    def _crawl_page(self, url):
        self.logger.debug('Start crawl %s...' % url)
        result = {
            'content': '',
            'error': False,
            'message': ''
        }
        if url:
            # check database
            page = self.storage.find_one({'_id': url})
            if page and page.get('crawled_date'):
                self.logger.debug('Page was crawled (2nd check): ' + page['_id'])
                return {url: self.storage.find_one({'_id': url})}

            try:
                headers = {'User-Agent': self.user_agent}
                response = requests.get(url, verify=False, timeout=10, headers=headers)
                # raise exception when something error
                if response.status_code == requests.codes.ok:
                    result['content'] = response.content
                else:
                    result['error'] = True
                    result['message'] = 'Page not found'

            except Exception as ex:
                self.logger.error('crawl_page error: %s' % ex.message)
                result['error'] = True
                result['message'] = str(ex.message)  # 'Page not found'
        else:
            result['error'] = True
            result['message'] = 'url is empty'

        # storage to database
        result['_id'] = url
        result['crawled_date'] = datetime.utcnow()
        result['content'] = get_unicode(result['content'])
        self.logger.info('Update crawled page to db...')
        self.storage.update_one({'_id': url}, {'$set': result}, upsert=True)
        self.logger.debug('End crawl %s...' % url)
        return {url: self.storage.find_one({'_id': url})}
