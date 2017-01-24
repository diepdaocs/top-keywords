# coding=utf-8
import string
from abc import ABCMeta, abstractmethod
from nltk import wordpunct_tokenize, WhitespaceTokenizer


class Tokenizer(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def tokenize(self, text):
        pass


class GeneralTokenizer(Tokenizer):

    def __init__(self):
        self.tokenizer = WhitespaceTokenizer()

    def normalize(self, text):
        return ' '.join(self.tokenize(text))

    def tokenize(self, text):
        result = []
        if type(text) is not unicode:
            if type(text) in (int, float):
                text = str(text)
            text = unicode(text, 'utf-8', errors='ignore')

        # pre tokenize
        for word in self.tokenizer.tokenize(text):
            word = word.strip(string.punctuation).lower()
            if word.endswith("'s") or word.endswith(u"’s"):
                word = word[:-2]

            if word and word.strip():
                result.append(word)
        return result
