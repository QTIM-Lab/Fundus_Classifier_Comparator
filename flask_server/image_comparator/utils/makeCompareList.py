# require 'net/http'
# require 'uri'
# require 'json'

import os, sys, requests, json, couchdb, uuid, pdb, random, math
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from itertools import combinations



load_dotenv("flask_server/.env",verbose=True)
 
DB_ADMIN_USER = os.getenv("DB_ADMIN_USER")
DB_ADMIN_PASS = os.getenv("DB_ADMIN_PASS")
DNS = os.getenv("DNS")
IMAGES_DB = os.getenv("IMAGES_DB")
DB_PORT = os.getenv("DB_PORT")
ADMIN_PARTY = True if os.getenv("ADMIN_PARTY") == 'True' else False

# https://couchdb-python.readthedocs.io/en/latest/getting-started.html
if ADMIN_PARTY:
    couch = couchdb.Server(f'http://{DNS}:{DB_PORT}')
else:
    couch = couchdb.Server(f'http://{DB_ADMIN_USER}:{DB_ADMIN_PASS}@{DNS}:{DB_PORT}')

# couch package ex for later
    # db = couch[IMAGES_DB]
    # imageIDs = [int(row['id']) for row in db.view('_design/basic_views/_view/imageSet2ImageId')]
    # imageIDs.sort()
    # imageIDs = [str(i) for i in imageIDs]

def getURL(imageSet: str) -> str:
    url = f"http://{DNS}:{DB_PORT}/{IMAGES_DB}"
    view = f'/_design/basic_views/_view/imageSet2ImageId?key="{imageSet}"'
    URL = url + view
    return URL

def getImageIDs(url: str) -> list:
    # pdb.set_trace()
    if ADMIN_PARTY:
        response = requests.get(url)
    else:
        response = requests.get(url, auth=(DB_ADMIN_USER, DB_ADMIN_PASS))
    response = response.content.decode('utf-8')
    response = json.loads(response)    
    imageIDs = [int(row['id']) for row in response['rows']]
    imageIDs.sort()

    return imageIDs

def makeList(listName: str, pairs: list) -> None:
    # pdb.set_trace()
    uid = uuid.uuid1()
    t = datetime.now() - timedelta(hours=4)
    obj = {
           "type":"image_compare_list",
           "list_name": listName,
           "count":len(pairs),
           "list":pairs,
           "time_added":t.strftime('%Y-%m-%d %H:%M:%S')}
    db = couch[IMAGES_DB]
    # pdb.set_trace()
    print(f"Created Compare List: {listName}")
    doc_id, doc_rev = db.save(obj)
    


def main(imageSet: str, listName: str, pctRepeat: int = 0):
    url = getURL(imageSet)
    imageIDs = getImageIDs(url)
    # create all unique combinations
    unique_pairs = [list(comb) for comb in combinations(imageIDs, 2)]
    random.shuffle(unique_pairs)
    amountRepeat = math.ceil(pctRepeat/100 * len(unique_pairs))
    repeats = random.sample(unique_pairs, amountRepeat)
    pairs = unique_pairs + repeats
    makeList(listName, pairs)



if __name__ == "__main__":
    try:
        try:
            main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
            print(f"* Creating Image Compare List using {sys.argv[3]} repeats *")
        except IndexError as err:
            print(f"* Creating Image Compare List using 0 repeats *")
            main(sys.argv[1], sys.argv[2])
    except IndexError as err:
        print(f"""
        Error: {err}, and probably means you 
        didn't provide <imageSet>, <listName>, with optional [<pctRepeat>]
        """)
    


