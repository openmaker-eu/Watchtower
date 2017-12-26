from utils import country_code_for_location, country_code_for_country
from pdb import set_trace
#import re

def predict_location(query, location_database, country_code_database):
    if not query:
        return ""

    pred = predict_location_helper(query, location_database,country_code_database)
    if not pred:
        pred = predict_location_helper(query, location_database,country_code_database,"")

    if pred:
        return pred
    else:
        return ""

def predict_location_helper(query,location_database,country_code_database, delimiter=","):
    ### Returns predicted country code

    if delimiter == "":
        splitted = query.split()
    else:
        splitted = query.split(delimiter)

    # Start from last token, first check if it is a country.
    # If yes, return the country code. If not, find predicted country code
    # and probability from the location database.
    l = []
    for token in [x.strip() for x in reversed(splitted)]:
        country_code = country_code_for_country(token, country_code_database)
        if country_code:
            return country_code
        else:
            country_code = country_code_for_location(token, location_database)
            if country_code:
                # set_trace()
                l.append(country_code)
    if not l:
        return None
    prediction = max(l, key=lambda x: x[1])[0]
    return prediction
