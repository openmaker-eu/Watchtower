import application.utils.location.get_locations as get_location
from application.Connections import Connection
from application.ThreadPool import ThreadPool

a = ThreadPool(10, False)


def abc(k):
    places = get_location.get_place_context(text=k['description'])

    location = {
        "countries": places.countries,
        "country_mentions": places.country_mentions,
        "cities": places.cities,
        "city_mentions": places.city_mentions
    }
    Connection.Instance().newsPoolDB[str(i)].find_one_and_update({'_id': k['_id']}, \
                                                                 {'$set': {'location': location}})


for i in Connection.Instance().newsPoolDB.collection_names():
    print(i)
    if i != "counters":
        for k in Connection.Instance().newsPoolDB[str(i)].find({'location': {'$exists': False}}, {'description': 1}):
            a.add_task(abc, k)
