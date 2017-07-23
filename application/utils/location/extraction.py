import nltk
from .utils import remove_non_ascii


class Extractor(object):
    def __init__(self, text=None):
        if not text and not url:
            raise Exception('text or url is required')

        self.text = text
        self.places = []

    def find_entities(self):

        text = nltk.word_tokenize(self.text)
        nes = nltk.ne_chunk(nltk.pos_tag(text))

        for ne in nes:
            if type(ne) is nltk.tree.Tree:
                if (ne.label() == 'GPE' or ne.label() == 'PERSON' or ne.label() == 'ORGANIZATION'):
                    self.places.append(u' '.join([i[0] for i in ne.leaves()]))
