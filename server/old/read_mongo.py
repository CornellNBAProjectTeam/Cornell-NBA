'''
PER
    FGM - totals.FG
    Stl - totals.STL
    3PTM - totals.3P
    FTM - totals.FT
    Blk - totals.BLK
    Off_Reb - totals.ORB
    Ast - totals.AST
    Def_Reb - totals.DRB
    Foul - totals.PF
    FT_Miss - totals.FTA-totals.FT
    FG_Miss - totals.FGA-totals.FG
    TO - totals.TOV
'''
import pandas as pd
from pymongo import MongoClient
from bson.objectid import ObjectId

PER_FEATURES = [
    'FG',
    'STL',
    '3P',
    'FT',
    'BLK',
    'ORB',
    'AST',
    'DRB',
    'PF',
    'FT_M', #FT_Miss - totals.FTA-totals.FT
    'FG_M', #FG_Miss - totals.FGA-totals.FG
    'TOV',
    'MP'
]

WANTED_FEATURES = {
	'date': 1, #Int32
	'teams.name': "", #String
	'teams.abbreviation': "", #String
	'teams.score': "", #Int32
	'teams.home': "", #Boolean
	'teams.won': 1, #Int32
    'box.team.ast': 1,  # double
    'box.team.blk': 1,     # Int32
    'box.team.drb': 1,    # Int32
    'box.team.fg': 1,     # Int32
    'box.team.fg3': 1,     # Int32
    'box.team.fg3_pct': 1,    # Int32
    'box.team.fg3a': 1,    # Int32
    'box.team.fg_pct': 1,    # Int32
    'box.team.fga': 1,    # Int32
    'box.team.ft': 1,     # Int32
    'box.team.ft_pct': 1,    # Int32
    'box.team.fta': 1,    # Int32
    'box.team.mp': 1,     # Int32
    'box.team.orb': 1,     # Int32
    'box.team.pf': 1,    # Int32
    'box.team.pts': 1,    # Int32
    'box.team.stl': 1,     # Int32
    'box.team.tov': 1,     # Int32
    'box.team.trb': 1,     # Int32
}

# Connect to MongoDB
def connectMongo(db, host='localhost', port=27017, mongo_uri=None):

    """ A util for making a connection to mongo """

    if mongo_uri:
        conn = MongoClient(mongo_uri)
    else:
        conn = MongoClient(host, port)

    return conn[db]

def readMongo(db, collection, query={}, queryReturn=None,
                _limit=None,no_id=True,mongo_uri=None):

    """ Read from Mongo and Store into DataFrame """

    # Connect to MongoDB
    db = connectMongo(db=db, mongo_uri=mongo_uri)

    # Make a query to the specific DB and Collection
    cursor = db[collection].find(query, queryReturn)

    # Check if a limit was set
    if _limit:
        cursor = cursor.limit(_limit)
    # Expand the cursor and construct the DataFrame
    df =  pd.DataFrame(list(cursor))

    # Delete the _id
    if no_id:
        del df['_id']

    return df