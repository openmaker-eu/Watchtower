# coding=utf-8
import re # for regex in location filtering

def getLocationRegex(location):
    location = location.lower()
    location_in_different_langs ="("
    if location == 'italy' or location =='it': # source : wikipedia
        location_in_different_langs += "italy|IT|"
        location_in_different_langs += "an Eadailt|"
        location_in_different_langs += "yr Eidal|"
        location_in_different_langs += "Étalie|"
        location_in_different_langs += "an Iodáil|"
        location_in_different_langs += "Itaalia|"
        location_in_different_langs += "Italia|"
        location_in_different_langs += "Itàlia|"
        location_in_different_langs += "Italía|"
        location_in_different_langs += "Itália|"
        location_in_different_langs += "Ítalía|"
        location_in_different_langs += "Italii|"
        location_in_different_langs += "Italië|"
        location_in_different_langs += "Italie|"
        location_in_different_langs += "Itálie|"
        location_in_different_langs += "Italien|"
        location_in_different_langs += "Italija|"
        location_in_different_langs += "Itālija|"
        location_in_different_langs += "Italio|"
        location_in_different_langs += "Īṭāliya|"
        location_in_different_langs += "Italiya|"
        location_in_different_langs += "l\-Italja|"
        location_in_different_langs += "Itallia|"
        location_in_different_langs += "Itaeri|"
        location_in_different_langs += "Italska|"
        location_in_different_langs += "Italya|"
        location_in_different_langs += "İtalya|"
        location_in_different_langs += "Italye|"
        location_in_different_langs += "Itaria|"
        location_in_different_langs += "Olaszország|"
        location_in_different_langs += "Talia|"
        location_in_different_langs += "Taliansko|"
        location_in_different_langs += "Ṭālyān|"
        location_in_different_langs += "Włochy|"
        location_in_different_langs += "Yìdàlì)"
    elif location == 'slovakia' or location =='sk':
        location_in_different_langs += "slovakia|SK|"
        location_in_different_langs += "Eslovakia|"
        location_in_different_langs += "Eslovaquia|"
        location_in_different_langs += "Eslováquia|"
        location_in_different_langs += "Eslovàquia|"
        location_in_different_langs += "Horowākia|"
        location_in_different_langs += "Seullobakia|"
        location_in_different_langs += "Sīluòfákè|"
        location_in_different_langs += "Slovacchia|"
        location_in_different_langs += "Slovacia|"
        location_in_different_langs += "Slovakia|"
        location_in_different_langs += "Slovakiet|"
        location_in_different_langs += "Slovensko)"
    elif location == 'spain' or location =='es':
        location_in_different_langs += "spain|ES|"
        location_in_different_langs += "Espainia|"
        location_in_different_langs += "España|"
        location_in_different_langs += "Espanya|"
        location_in_different_langs += "Hispania|"
        location_in_different_langs += "İspanya|"
        location_in_different_langs += "Spagna|"
        location_in_different_langs += "Spanien)"
    elif location == 'uk' or location =='gb':
        location_in_different_langs += "UK|GB"
        location_in_different_langs += "united\s*kingdom|"
        location_in_different_langs += "Britania|"
        location_in_different_langs += "England|"
        location_in_different_langs += "İngiltere)"
    else:
        location_in_different_langs = location

    #print(location_in_different_langs)
    # PROBLEM! Non-unicode characters are also counted as boundary values. Need to fix this.
    return re.compile("^.*\\b" + location_in_different_langs + "\\b.*$", re.IGNORECASE)
