def country_code_for_location(query, location_database):
    query = query.lower()
    if query not in location_database:
        return None
    l = sorted(location_database[query], key=lambda x: x[1], reverse=True)
    sum_countries = sum([x[1] for x in l])
    if len(l) == 1:
        return (l[0][0], 1.0)
    elif sum_countries == 0:
        return (l[0][0], 1.0 / len(l))
    else:
        return (l[0][0], l[0][1] / sum_countries)

def country_code_for_country(query, country_code_database):
    query = query.lower()
    # Look if query is in the country database, return None if it does not
    if query in country_code_database:
        return country_code_database[query]
    else:
        return None

def fetch_location_database():
    database = {}
    with open("city_location.txt", "r") as source:
        for line in source:
            city, countries = [x.strip() for x in line.split("|")]
            # set_trace()
            countries = [(x.strip(), int(y.strip())) for x, y in [
                z.split() for z in countries[1:-1].split(",")]]
            database[city] = countries
    return database


def fetch_country_code_database():
    database = {}
    with open("country_code.txt", "r") as source:
        for line in source:
            country, code = [x.strip() for x in line.split("-")]
            database[country] = code
    return database