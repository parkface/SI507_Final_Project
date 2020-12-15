from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import pdb
import sqlite3
from flask import Flask

CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {} 
baseurlSoup = 'https://www.internationalstudent.com/school-search/usa'
baseurlAPI = 'http://www.mapquestapi.com/search/v2/radius'
dbName = 'UniversitiesInfo.db'
createTableUniversities = '''CREATE TABLE IF NOT EXISTS Universities (
                            ID integer PRIMARY KEY,
                            NAME text NOT NULL,
                            STATE text NOT NULL,
                            ADDRESS text,
                            ZIPCODE text,
                            PHONE text,
                            URL text NOT NULL UNIQUE,
                            MALE text,
                            FEMALE text,
                            MALEINTL text,
                            FEMALEINTL text
                            );'''
createTableRestaurants = '''CREATE TABLE IF NOT EXISTS Restaurants (
                            ID integer PRIMARY KEY,
                            NAME text UNIQUE,
                            ADDRESS text,
                            PHONE text,
                            UniID integer NOT NULL,
                            FOREIGN KEY (UniID) REFERENCES Universities (ID)
                            );'''
STATES = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','District of Columbia','Florida',
                'Georgia','Guam','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts',
                'Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico',
                'New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Puerto Rico','Rhode Island','South Carolina',
                'South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming']
class university:
    '''An University 

    Instance Attributes
    -------------------
    states: string
        States of USA
    name: string
        name of the university
    address: string
        address of the university
    zipcode: string
        zip-code of the university
    phone: string
        phone of the university
    male_tot, male_intl, female_tot, female_intl: string
        number of the male total, male international, female total, female international respectively
    '''
    def __init__(self): #initialize empty attributes
        self.states = [] # states in US
        self.name = [] # name of the university
        self.male_tot = [] # total num of male students
        self.male_intl = [] # num of international male students
        self.female_tot = [] # total num of female students
        self.female_intl = [] # num of international female students
        self.address = [] # address of the university
        self.zipcode = [] # zip code of the university
        self.phone = [] # phone of the university
        self.url = [] # url of the university

    def info(self):
        return self.name + ' : ' + self.address + ' [' + self.zipcode + ']'

    pass

class restaurant:
    '''A restaurant

    Instance Attributes
    -------------------
    name: string
        name of the restaurnat
    address: string
        address of the restaurnat
    zipcode: string
        zip-code of the restaurnat
    '''
    def __init__(self): #initialize empty attributes
        self.name = [] # address of the restaurant
        self.address = [] # address of the restaurant
        self.zipcode = [] # zip code of the restaurant

    def info(self):
        return self.name + ' : ' + self.address + ' [' + self.zipcode + ']'

    pass

def loadCache(): 
    ''' Load cache if exists 

    Parameters
    ----------
    None

    Returns
    -------
    cache
        jason format, if the cache exists
        empty, if the cache does not exist
    '''

    try: # Try to get cache 
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except: # if no cache 
        cache = {}
    return cache
# Load the cache, save in a global variable
CACHE_DICT = loadCache()
def createDB():
    ''' create DB if not exists
    '''
    # Connect to dbName
    connection = sqlite3.connect(dbName)
    cursor = connection.cursor()

    # Connect or create tables if not exists
    cursor.execute(createTableUniversities)
    cursor.execute(createTableRestaurants)

    # Close connection
    connection.close()

def saveCache(cache):
    ''' save cache

    Parameters
    ----------
    cache : dict

    Returns
    -------
    None
    '''
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def constructUniqueKey(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    key_value_temp = [] # empty string
    connector = "_"
    for i in params.keys(): # get all of values in params
        key_value_temp.append(f'{i}_{params[i]}')
    key_value_temp.sort() # sort string in alphabat order
    unique_key = baseurl + connector + connector.join(key_value_temp)
    return unique_key

def requestResponseText(url):
    ''' request response text of the url

    Parameters
    ----------
    url: string

    Returns
    -------
    response.text
    '''
    if (url in CACHE_DICT.keys()): 
        print("Using cache")
    else:
        print("Fetching")
        response = requests.get(url)
        CACHE_DICT[url] = response.text 
        saveCache(CACHE_DICT)
    return CACHE_DICT[url]

def extractUniInfo(url, stateName):
    '''Extract an university info and
    make an instance that contains the info
    
    Parameters
    ----------
    url: string
        The URL for an university
    
    Returns
    -------
    instance
        an university instance
    '''

    Uni = university() # call the class
    
    response_text = requestResponseText(url)
    soup = BeautifulSoup(response_text, 'html.parser') # get the text
    Uni.url = url
    Uni.states = stateName
    ## some universities have no information
    
    try:
        Uni.name = soup.find('div',{'class':'card card-body mb-3 p-3'}).h1.text # name
    except:
        pass
    try:
        Uni.state = soup.find_all('li',{'class':'breadcrumb-item'})[2].a.text
    except:
        pass
    try:
        Uni.male_tot = soup.find_all('strong',{'class':'f-12'})[1].text
    except:
        pass
    try:
        Uni.male_intl = soup.find_all('strong',{'class':'f-12'})[4].text
    except:
        pass
    try:
        Uni.female_tot = soup.find_all('strong',{'class':'f-12'})[2].text
    except:
        pass
    try:
        Uni.female_intl = soup.find_all('strong',{'class':'f-12'})[5].text
    except:
        pass
    try:
        fullAddress = soup.find('ul',{'class':'fa-ul'}).li.text.strip()
        if fullAddress[-5] == '-': # if the zipcode is '5digits - 4 digits' format
            fullAddress = fullAddress[:-5] # ignore the last 4 digits
    except:
        pass
    try:
        Uni.address = fullAddress[:-6]
    except:
        pass
    try:
        Uni.zipcode = fullAddress[-5:]
    except:
        pass
    try:
        Uni.phone = soup.find('ul',{'class':'fa-ul'}).a.text
    except:
        pass

    return Uni

def insertIgnoreIntoUniversities(Uni):
    '''execute INSERT or IGNORE to store the university info into the 'Universities' table

    Parameters
    ----------
    Uni: Instance of the University class
    
    Returns
    -------
    None
    '''
    # Connect to dbName
    connection = sqlite3.connect(dbName)
    cursor = connection.cursor()

    insertUni = """
    INSERT or IGNORE INTO Universities (NAME,STATE,ADDRESS,ZIPCODE,PHONE,URL,MALE,FEMALE,MALEINTL,FEMALEINTL)
    VALUES ("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}");""".format(Uni.name,Uni.states,Uni.address,
    Uni.zipcode,Uni.phone,Uni.url,Uni.male_tot,Uni.female_tot,Uni.male_intl,Uni.female_intl)

    # Connect or create tables if not exists
    cursor.execute(insertUni)
    connection.commit()

    query = '''
    SELECT ID
    FROM Universities
    WHERE NAME = '{}'
    '''.format(Uni.name)
    UniID = cursor.execute(query).fetchall()[0][0]
    connection.close()

    return UniID

def insertIgnoreIntoRestaurants(restaurantNameInfo,UniID):
    '''execute INSERT or IGNORE to store the Restaurant info into the 'Restaurants' table

    Parameters
    ----------
    restaurantNameInfo: Dictionary containing restaurant's info

    Returns
    -------
    None
    '''
    # Connect to dbName
    connection = sqlite3.connect(dbName)
    cursor = connection.cursor()
    i = 1
    for key in restaurantNameInfo.keys():
        if i > 10:
            break
        insertRest = """
        INSERT or IGNORE INTO Restaurants (NAME,ADDRESS,PHONE,UniID)
        VALUES ("{}","{}","{}",{});""".format(key,
        restaurantNameInfo[key]['address'],restaurantNameInfo[key]['phone'],UniID)

        # Connect or create tables if not exists
        cursor.execute(insertRest)
        connection.commit()

        i +=1

    connection.close()

def uniInfoString(Uni):
    '''string of the University info
    
    Parameters
    ----------
    Uni: instance
    
    Returns
    -------
    uniInfo: string
    '''
    uniInfo = """
    Name: {}
    Address: {}
    Phone Number: {}
    # of male students: {}
    # of female students: {}
    # of male international students: {}
    # of female international students: {}
    """.format(Uni.name, Uni.address+', '+Uni.zipcode, Uni.phone, Uni.male_tot, Uni.female_tot, Uni.male_intl, Uni.female_intl)
    
    return uniInfo

def extractUnis(url, lists):
    '''Extract university urls and name recursively
    
    Parameters
    ----------
    url: string
        The URL of the state
    lists: empty list
    
    Returns
    -------
    lists
        appended lists
    '''

    response_text = requestResponseText(url)
    soup = BeautifulSoup(response_text, 'html.parser') # get the text
    
    # Universities are listed on the several pages
        # we have to click 'next' in the website
    isnext = soup.find('li',{'class':'btn btn-sm btn-link next'})
    
    if not(isnext == None): # if this is the last page
        url_new = 'https://www.internationalstudent.com' + isnext.a['href']
        extractUnis(url_new, lists)

        return lists.append(soup.find_all('li',{'class':'list-group-item d-flex justify-content-between font-bitter h6'}))
    
    return lists.append(soup.find_all('li',{'class':'list-group-item d-flex justify-content-between font-bitter h6'}))

def getUniList(url):
    '''Make a dictionary of university instances from a state url
    
    Parameters
    ----------
    url: string
        A URL for a state
    
    Returns
    -------
    uniNameUrl: Dict
        keys: uniName, value: uni url
    '''
    
    li_list = []
    #dictUniInsatnce = {}
    uniNameUrl = {}

    extractUnis(url,li_list)
    for i in range(len(li_list)):
        h = len(li_list) - 1 - i # li_list has a reverse order
        for j in range(len(li_list[h])):
            uniName = li_list[h][j].a.text.strip()
            uniURL = 'https://www.internationalstudent.com' + li_list[h][j].a['href']
            #dictUniInsatnce[uniName] = extractUniInfo(uniURL,stateName)
            uniNameUrl[uniName] = uniURL

    return uniNameUrl

def extractStates():
    '''Extract state urls and
    make a dict containing the state name and corresponding url
    
    Parameters
    ----------
    None
    
    Returns
    -------
    dict
        state name : state url
    '''

    stateNameURL = {}
    response_text = requestResponseText(baseurlSoup)
    soup = BeautifulSoup(response_text, 'html.parser') # get the text

    for i in range(3):
        ultag = soup.find_all('ul',{'class':'list-unstyled col-md mb-0 d-flex flex-column justify-content-between'})[i+3]
        for litag in ultag.find_all('li'):
            stateName = litag.a.text.strip()
            stateURL = 'https://www.internationalstudent.com' + litag.a['href']
            stateNameURL[stateName] = stateURL

    return stateNameURL

def requestAPI(url, params):
    ''' request API and retrun the output in the json format

    Parameters
    ----------
    url: Strings
    params: dictionary

    Returns
    -------
    json
    '''
    response = requests.get(url, params=params) # oauth is defined globally
    return response.json()

def getNearbyPlaces(uni):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    uni: Insatnce
        an instance of an university
    
    Returns
    -------
    dict
        a value of the 'searchResults' value of the converted API return from MapQuest API
    '''

    
    params = {"key":secrets.API_KEY, "origin":uni.zipcode, "radius":10, "maxMatches":500, "ambiguities":"ignore"}
    unique_key = constructUniqueKey(baseurl=baseurlAPI, params= params)

    if unique_key in CACHE_DICT.keys(): # if the unique key is in cache
        print("Using Cache")
    else: # if the unique key is not in cache
        print("Fetching")
        CACHE_DICT[unique_key] = requestAPI(url=baseurlAPI, params=params) #request new one
        saveCache(CACHE_DICT) # save the current state

    results = CACHE_DICT[unique_key]
    return results['searchResults']

def extractRestaurantInfoOnly(searchResults):
    '''Extract restaurant info from dictionary that was a return of the API request
    
    Parameters
    ----------
    searchResults: Dict
        Return of the API request
    
    Returns
    -------
    restaurantNameInfo : Dict
        'Nmae of the restaurant' : {'phone' : value, 'address' : value}
    '''
    restaurantNameInfo = {}
    for i in range(len(searchResults)):
        singleRestaurantInfo = {}
        name = searchResults[i]['name']
        fields = searchResults[i]['fields']
        # restaurants only
        if fields['group_sic_code_name'] == '(All) Restaurants':
            if fields['phone']: # non-empty phone
                singleRestaurantInfo['phone'] = fields['phone']
            else:
                singleRestaurantInfo['phone'] = 'None'
            if fields['address'] and fields['city']: # non-empty address & city
                singleRestaurantInfo['address'] = fields['address'] + ', ' + fields['city']
            else:
                singleRestaurantInfo['address'] = 'None'
            restaurantNameInfo[name] = singleRestaurantInfo

    return restaurantNameInfo

def restaurantInfoString(restaurantNameInfo):
    i = 1
    
    restaurantInfo = ""
    for key in restaurantNameInfo.keys():
        if i > 10:
            break
        name = key
        address = restaurantNameInfo[key]['address']
        phone = restaurantNameInfo[key]['phone']
        restaurantInfo = restaurantInfo + "[{}] {} : {}, {} \n".format(i, name, address, phone)
        i += 1

    return restaurantInfo
def printDictKeys(dictionary):
    i = 1
    for key in dictionary.keys():
        print('[{}] {}'.format(i, key))
        i += 1
    pass



if __name__=="__main__":
    # upper lower case
    createDB()
    exitFlag = False
    while not(exitFlag):
        print("=============================================")
        stateNameURL = extractStates()
        printDictKeys(stateNameURL)

        while 1:
            print("=============================================")
            stateName = input("Type a state name (case sensitive) you want to explore or 'exit': ")
            if stateName in STATES:
                break
            elif stateName == 'exit':
                print("Bye~")
                exitFlag = True
                break
            else:
                print("Please type a correct state name !")
        
        if exitFlag:
            break
        
        print("=============================================")
        print("University lists in the chosen state")
        uniNameUrl = getUniList(stateNameURL[stateName])
        printDictKeys(uniNameUrl)

        while 1:
            print("=============================================")
            uniName = input("Type one of the universities you are interested in or 'exit': ")
            if uniName in uniNameUrl.keys():
                break
            elif uniName == 'exit':
                print("Bye~")
                exitFlag = True
                break
            else:
                print("Please type a correct university name !")

        if exitFlag:
            break
        
        # extract university information
        uniInstance = extractUniInfo(uniNameUrl[uniName], stateName)
        uniInfo = uniInfoString(uniInstance)

        # get nearby restaurant info
        searchResults = getNearbyPlaces(uniInstance)
        restaurantDict = extractRestaurantInfoOnly(searchResults)
        restaurantInfo = restaurantInfoString(restaurantDict)
        
        # update DB
        UniID=insertIgnoreIntoUniversities(uniInstance)
        insertIgnoreIntoRestaurants(restaurantDict,UniID)

        # merge the info
        uniRestaurantInfo = """=============================================\n{}\n=============================================\n{}
        """.format(uniInfo, restaurantInfo)

        while 1:
            print("=============================================")
            print("Choose one display option for showing the university and near restaurants information")
            print("between 'command line prompt (CLP)' and 'Flask'")
            printOption = input("Type 'CLP' or 'Flask' or 'exit': ")
            
            if printOption in ['CLP', 'Flask']:
                if printOption == 'CLP':
                    print(uniRestaurantInfo)
                    break
                else:
                    # Todo
                    app = Flask(__name__)
                    @app.route("/")
                    def flaskUniRestaurantInfo():
                        return uniRestaurantInfo
                    app.run()
                    break
            elif printOption == 'exit':
                print("Bye~")
                exitFlag = True
                break
            else:
                print("Please type a correct word !")

        if exitFlag:
            break

        while 1:
            print("=============================================")
            continueCheck = input("If you want to restart the searching, type 'continue' or 'exit': ")
            if continueCheck == 'continue':
                break
            elif continueCheck == 'exit':
                print("Bye~")
                exitFlag = True
                break
            else:
                print("Please type a correct university name !")

        if exitFlag:
            break

