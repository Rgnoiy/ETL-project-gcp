import functions_framework
from google.cloud import bigquery
import src.functions as f
import src.database as dbc


# Construct a BigQuery client object.
client = bigquery.Client()

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def data_transformation(cloud_event):
   # data = cloud_event.data
   event_id = cloud_event["id"]
   # create tables in bq
   dbc.create_tables(client)
   # read csv file from google storage use pandas as dataframe
   df = f.ReadCSVandCleanDF(event_id)
   store_name = f.LoadStore(df)
   # Load product name into db and drop duplicates---------------------------------------------------------------------------------------------
   f.LoadProduct(f.ExplodedItems(df), client)
   f.LoadTransactionDF(df, store_name)
   f.LoadBasketItemsDF(f.ExplodedItems(df))