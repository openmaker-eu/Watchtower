# coding=utf-8
import re # for regex in location filtering

italy_in_different_langs = ["italy","IT","an Eadailt","yr Eidal","Étalie","an Iodáil","Itaalia","Italia","Itàlia","Italía","Itália","Ítalía","Italii","Italië","Italie","Itálie","Italien","Italija","Itālija","Italio","Īṭāliya","Italiya","l\-Italja","Itallia","Itaeri","Italska","Italya","İtalya","Italye","Itaria","Olaszország","Talia","Taliansko","Ṭālyān","Włochy","Yìdàlì"]
slovakia_in_different_langs = ["slovakia","SK","Eslovakia","Eslovaquia","Eslováquia","Eslovàquia","Horowākia","Seullobakia","Sīluòfákè","Slovacchia","Slovacia","Slovakia","Slovakiet","Slovensko"]
spain_in_different_langs = ["spain","ES","Espainia","España","Espanya","Hispania","İspanya","Spagna","Spanien"]
uk_in_different_langs = ["UK","GB","united\s*kingdom","Britania","England","İngiltere"]

def getLocationRegex(location):
    location = location.lower()
    location_in_different_langs = "("
    if location == "italy" or location == "it":
        location_in_different_langs += ("|".join(italy_in_different_langs) + ")")
    elif location == 'slovakia' or location =='sk':
        location_in_different_langs += ("|".join(slovakia_in_different_langs) + ")")
    elif location == 'spain' or location =='es':
        location_in_different_langs += ("|".join(spain_in_different_langs) + ")")
    elif location == 'uk' or location =='gb':
        location_in_different_langs += ("|".join(uk_in_different_langs) + ")")
    else:
        location_in_different_langs = location

    # PROBLEM! Non-unicode characters are also counted as boundary values. Need to fix this.
    return re.compile("^.*\\b" + location_in_different_langs + "\\b.*$", re.IGNORECASE)
