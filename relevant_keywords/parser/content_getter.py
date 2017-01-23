from relevant_keywords.util.utils import get_logger


class ContentGetter(object):

    def __init__(self, crawler, extractor):
        self.crawler = crawler
        self.extractor = extractor
        self.logger = get_logger(self.__class__.__name__)

    def process(self, urls):
        # crawl pages
        result = self.crawler.process(urls)
        # extract content from pages
        result = self.extractor.process(result)
        return result

