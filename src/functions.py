import re
import hashlib
from google.cloud import bigquery
import pandas as pd
# import pandas_gbq as pdgbq
# from io import StringIO

        
def hash(s: str) -> str:
    return str(int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16))[:10]
        
        
# def SaveCSVToS3Bucket(df, s3_file_name, index=True, date=None):
    
    """Write dataframe to .csv and save it in another s3 bucket."""
    
    csv_buffer = StringIO()
    s3_resource = boto3.resource('s3')
    bucket = 'team4-transformed-data'
    # store .csv file in buffer
    df.to_csv(csv_buffer, index=index, date_format=date)
    # put .csv file into S3 bucket
    if date is None:
        s3_resource.Object(bucket, f'{s3_file_name}_basket.csv').put(Body=csv_buffer.getvalue())
        print(f"{s3_file_name}_basket.csv has been added to s3 bucket.")
    else:
        s3_resource.Object(bucket, f'{s3_file_name}_transaction.csv').put(Body=csv_buffer.getvalue())
        print(f"{s3_file_name}_transaction.csv has been added to s3 bucket.")
    
    

def ReadCSVandCleanDF(event_id):
    
    """Read .csv file from cloud storage, generate hash id, drop columns."""
    
    df = pd.read_csv(f'gs://{event_id}', names=['timestamp', 'store', 'customer_name', 'basket_items', 'total_price', 'cash_or_card', 'card_number'], parse_dates=['timestamp'], infer_datetime_format=True, dayfirst=True, cache_dates=True)
    df["order_id_pre_hash"] = str(df["timestamp"]) + df["store"] + df["customer_name"]
    df.index = df["order_id_pre_hash"].apply(lambda x: hash(x))
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%0m-%0d %H:%M:%S')
    df.drop(columns=['card_number'], inplace=True)
    df.drop(columns=['customer_name'], inplace=True)
    df.drop(columns=["order_id_pre_hash"], inplace=True)
    df.index.name = 'transaction_hash_id'
    
    return df
    
    
def ExplodedItems(df):
    
    """Generate a df where ordered items are in seperate rows."""
    
    # generate a new column with each row of column 'basket_items' in a format of list
    df["items"] = df["basket_items"].apply(lambda x: x.split(","))
    # spread products into different rows, replicating index.
    df = df.explode("items")
    # extract column 'items'
    items = df['items']
    # seperate price into an independent column
    result = items.str.rsplit(pat='-', n=1, expand=True)
    # remove leading and trailing space of the string
    result[0] = result[0].apply(lambda x: x.strip(' '))
    
    return result
        
        
def LoadProduct(df, client):
    # drop duplicated product type
    product_list = df.drop_duplicates(subset=[0], keep='first', ignore_index=True)
    # rename column name
    product_list.rename(columns={0: 'product_name', 1: 'price'}, inplace=True)
    # convert product df into dict and iterate over it in order to extract each product name and insert it into db
    try:
        for product in product_list.to_dict('records'):
            sql = f"INSERT INTO product (product_name, price) SELECT '{product['product_name']}', {product['price']} WHERE NOT EXISTS (SELECT * FROM product WHERE product_name = '{product['product_name']}');"
        query_job = client.query(sql)   # make an API request
        print("Product table has been loaded.")
    except Exception as e: 
        print(e)


def LoadStore(df, client):

    # extract 'store' column + remove leading and trailing space of the string + convert it to df
    store = df['store'].apply(lambda x: x.strip(' ')).drop_duplicates().to_frame()
    # rename column names
    store.rename(columns={'store':'store_name'}, inplace=True)
    # gain store name
    store_name = store['store_name'][0]
    try:
        sql = f"INSERT INTO store (store_name) SELECT '{store_name}' WHERE NOT EXISTS (SELECT * FROM store WHERE store_name = '{store_name}');"
        query_job = client.query(sql)   # make an API request
        print("Store table has been loaded.")
    except Exception as e: 
        print(e)
    return store_name
    
    
def LoadBasketItemsDF(df):
    
    """Transform df to fit in basket table, return df."""
    
    # generate quantity column
    basket_items = df.groupby(df.index)[0].apply(lambda x: x.value_counts()).to_frame()
    basket_items = basket_items.reset_index()
    try:
        sql = '''SELECT * FROM product'''
        product_from_db = pd.read_gbq(sql, index_col='product_id')
    except Exception as e:
        print(e)
    # replace product name by its id
    basket_items['level_1'] = basket_items['level_1'].apply(lambda x: product_from_db[product_from_db.product_name == x].index[0])
    # rename columns
    basket_items.rename(columns={'level_1':'product_id', 0:'quantity'}, inplace=True)
    try:
        # load df directly to bigquery
        basket_items.to_gbq("transformed_data_for_cafe.basket")
    except Exception as e:
        print(e)
    
    
def LoadTransactionDF(df, store_name):
    
    """Transform df to fit in transaction table, return df."""
    
    # drop unwanted columns
    transaction = df.drop(columns=['basket_items', 'items'])
    # replace store name by its id
    try:
        sql = f"""SELECT * FROM store WHERE store_name='{store_name}'"""
        store_from_db = pd.read_gbq(sql, index_col='store_id')
    except Exception as e:
        print(e)
    transaction['store'] = int(store_from_db.index[0])
    # Rename column names to match DB columns
    transaction.rename(columns={'store':'store_id', 'cash_or_card':'payment_method'}, inplace=True)
    try:
        # load df directly to bigquery
        transaction.to_gbq("transformed_data_for_cafe.transaction")
    except Exception as e:
        print(e)