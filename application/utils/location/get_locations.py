from .extraction import Extractor
from .places import PlaceContext


def get_place_context(text=None):
    e = Extractor(text=text)
    e.find_entities()

    pc = PlaceContext(e.places)
    pc.set_countries()
    pc.set_regions()
    pc.set_cities()
    pc.set_other()

    return pc
