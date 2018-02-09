from enum import Enum
from pdb import set_trace
from application.Connections import Connection
import os

class Code(Enum):
    USASTATECODE = 1
    COUNTRYCODE = 2
    BOTH = 3
    NOTACODE = 4

UsaStateCodes = ["al","ak","az","ar","ca","co","ct","de","dc","fl","ga","hi","id","il","in","ia","ks","ky","la",
"me","md","ma","mi","mn","ms","mo","mt","ne","nv","nh","nj","nm","ny","nc","nd","oh","ok","or","pa","ri","sc","sd",
"tn","tx","ut","vt","va","wa","wv","wi","wy"]

class Predictor(object):
    """Predict location from given location string"""
    def __init__(self):
        # self.location_database = self.fetch_location_database(LOC_DATABASE_PATH)
        # self.country_code_database = self.fetch_country_code_database(COUNTRY_DATABASE_PATH)
        self.country_code_database, self.location_database = self.fetch_database()

    '''
        Fetches country_code_database and location_database and  from PostGreSql DB
    '''
    def fetch_database(self):
        with Connection.Instance().get_cursor() as cur:
            # country_code
            print("Fetching country_code database...")
            cur.execute("SELECT * FROM country_code")
            result = cur.fetchall()
            country_code_database = {x[0] : x[1] for x in result}
            
            # location country codes
            print("Fetching location_country_codes database...")
            cur.execute("SELECT * FROM location_country_codes")
            result = cur.fetchall()
            location_database = {x[0] : list(x[1].items()) for x in result}
            
            return(country_code_database, location_database)

    def predict_location(self, query, ):
        if not query:
            return ""

        pred = self.predict_location_helper(query)
        if not pred:
            pred = self.predict_location_helper(query,"")

        if pred:
            return pred
        else:
            return ""

    def predict_location_helper(self, query, delimiter=","):
        if delimiter == "":
            splitted = query.split()
        else:
            splitted = query.split(delimiter)

        # Start from last token.
        # If at any token, we have the name of the country, return country code of it.
        # Otherwise, if we encounter a country code, we must check if it is also an
        # USA state code. In this case, we check other tokens to see which possibility makes
        # sense. When none of the above is encountered, we simply continue to guess country
        # code from tokens and return the one with the highest probability.
        country_code_ambig = None
        l = []
        for tokenIdx,token in enumerate([x.strip() for x in reversed(splitted)]):
            tokenCodeType, code = self.getCode(token)
            if (tokenCodeType == Code.USASTATECODE or tokenCodeType == Code.COUNTRYCODE) and tokenIdx == 0:
                # Return "US"
                return code
            elif tokenCodeType == Code.BOTH:
                # If there is no other token, return this. Otherwise skip
                country_code_ambig = token.lower()
            else: # tokenCodeType == Code.None
                country_code = self.country_code_for_location(token)
                if country_code:
                    l.append(country_code)

        if l:
            prediction = max(l, key=lambda x: x[1])[0]
            return prediction
        elif country_code_ambig and len(splitted) <= 3:
            return country_code_ambig
        else:
            return ""

    def getCode(self, token):
        token = token.lower()
        if self.country_code_for_country(token):
            return (Code.COUNTRYCODE, self.country_code_for_country(token))
        else:
            isUsaStateCode = token in UsaStateCodes
            isCountryCode = token in self.country_code_database.values()
            if isUsaStateCode and isCountryCode:
                return (Code.BOTH, token)
            elif isCountryCode:
                return (Code.COUNTRYCODE, token)
            elif isUsaStateCode:
                return (Code.USASTATECODE, "us")
            else:
                return (Code.NOTACODE, None)

    def country_code_for_country(self, query):
        query = query.lower()
        # Look if query is in the country database, return None if it does not
        if query in self.country_code_database:
            return self.country_code_database[query]
        else:
            return None

    def country_code_for_location(self, query):
        query = query.lower()
        if query not in self.location_database:
            return None
        l = sorted(self.location_database[query], key=lambda x: x[1], reverse=True)
        sum_countries = sum([x[1] for x in l])
        if len(l) == 1:
            return (l[0][0], 1.0)
        elif sum_countries == 0:
            return (l[0][0], 1.0 / len(l))
        else:
            return (l[0][0], l[0][1] / sum_countries)
