from pymongo import MongoClient
import os
import pandas as pd

def get_mongo_client():
    """Restituisce un client MongoDB con connessione a MONGO_URI."""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017/FactoryMindDB")
    client = MongoClient(mongo_uri)
    return client

def fetch_mongo_data(database_name, collection_name, query={}, projection=None):
    """Recupera dati da MongoDB e li converte in DataFrame Pandas."""
    client = get_mongo_client()
    db = client[database_name]
    collection = db[collection_name]

    if projection:
        data = list(collection.find(query, projection))
    else:
        data = list(collection.find(query))

    df = pd.DataFrame(data)
    if '_id' in df.columns:
        df = df.drop(columns=['_id'])
    return df
