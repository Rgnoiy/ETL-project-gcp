import functions_framework
from google.cloud import bigquery
from google.cloud import storage
import functions as f
import database as dbc


# Construct a BigQuery client object.
client = bigquery.Client()
storage_client = storage.Client()

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def data_transformation(cloud_event):
   # data = cloud_event.data
   bucket = cloud_event["bucket"]
   folder_file_name = cloud_event["subject"].split("/", 1)[1]
   file_url = f"gs://{bucket}/{folder_file_name}"
   print("-" * 80)
   print(cloud_event)
   # create tables in bq
   dbc.create_tables(client)
   # read csv file from google storage use pandas as dataframe
   df = f.ReadCSVandCleanDF(file_url)

   
   store_id = f.LoadStore(df, client)
   

   product_list = f.LoadProduct(f.ExplodedItems(df), client)


   f.LoadTransactionDF(df, store_id, client)


   f.LoadBasketItemsDF(f.ExplodedItems(df), product_list, client)