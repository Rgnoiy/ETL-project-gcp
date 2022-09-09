import hashlib
from google.cloud import bigquery
import pandas as pd
import gcsfs


        
def hash(s: str) -> str:
    return str(int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16))[:10]
    

def ReadCSVandCleanDF(file_url):
    
    """Read .csv file from cloud storage, generate hash id, drop columns."""
    
    # read csv from cloud storage
    df = pd.read_csv(file_url, names=['timestamp', 'store', 'customer_name', 'basket_items', 'total_price', 'cash_or_card', 'card_number'], parse_dates=['timestamp'], infer_datetime_format=True, dayfirst=True, cache_dates=True)
    
    # generate hash code as unique id for each transaction record
    df["order_id_pre_hash"] = str(df["timestamp"]) + df["store"] + df["customer_name"]
    df.index = df["order_id_pre_hash"].apply(lambda x: hash(x))
    
    # set standard formate for datetime in bigquery
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%0m-%0d %H:%M:%S')
    
    # drop unwanted columns
    df.drop(columns=['card_number'], inplace=True)
    df.drop(columns=['customer_name'], inplace=True)
    df.drop(columns=["order_id_pre_hash"], inplace=True)
    
    # to match the column name in the table
    df.index.name = 'transaction_hash_id'

    print(df)
    
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
    # select the unique products out of the list
    product_list = df.drop_duplicates(subset=[0], keep='first', ignore_index=True)

    product_list.rename(columns={0: 'product_name', 1: 'price'}, inplace=True)

    # assign unique id for each product
    product_list["product_id"] = product_list["product_name"].apply(lambda x: hash(x))
    print(product_list)
    
    try:
        for product in product_list.to_dict('records'):
            sql = f"""INSERT transformed_data_for_cafe.product (product_id, product_name, price) WITH w AS (SELECT * FROM UNNEST(ARRAY<STRUCT<product_id STRING, product_name STRING, price DECIMAL>>[('{product["product_id"]}', '{product['product_name']}', {product['price']})]) AS col) SELECT product_id, product_name, price FROM w WHERE NOT EXISTS (SELECT product_name FROM transformed_data_for_cafe.product WHERE product_name = "{product['product_name']}");"""
            query_job = client.query(sql)   # make an API request
        print(query_job.result())
        print("Product table has been loaded.")
    except Exception as e: 
        print(f"the error is : {e}")

    return product_list


def LoadStore(df, client):
    # extract 'store' column + remove leading and trailing space of the string + convert it to df
    store = df['store'].apply(lambda x: x.strip(' ')).drop_duplicates().to_frame()

    # generate hash id for the store 
    store.index = store["store"].apply(lambda x: hash(x))

    # grant store_name and store_id
    store = store.to_dict('split')
    store_id = store["index"][0]
    store_name = store["data"][0][0]
    print(store_name, store_id)

    try:
        sql = f"""INSERT transformed_data_for_cafe.store (store_id, store_name) WITH w AS (SELECT * FROM UNNEST(ARRAY<STRUCT<store_id STRING, store_name STRING>>[('{store_id}', '{store_name}')]) AS col) SELECT * FROM w WHERE NOT EXISTS (SELECT store_name FROM transformed_data_for_cafe.store WHERE store_name = '{store_name}');"""
        query_job = client.query(sql)   # make an API request
        print("Store table has been loaded.")
    except Exception as e: 
        print(f"the error is : {e}")
    return store_id
    
    
def LoadBasketItemsDF(df, product_list, client):
    
    """Transform df to fit in basket table, return df."""
    
    # generate quantity column
    basket_items = df.groupby(df.index)[0].apply(lambda x: x.value_counts()).to_frame()
    # fix multi-index problem
    basket_items = basket_items.reset_index()
    basket_items.rename(columns={'level_1': 'product_id', 0: 'quantity'}, inplace=True)
   #  product_list.index = product_list['product_id']
    basket_items['product_id'] = basket_items['product_id'].apply(lambda x: product_list[product_list.product_name == x].product_id.iloc[0])
    # rename columns
    print(basket_items)
    # try:
    #     
    #     basket_items.to_gbq("transformed_data_for_cafe.basket", if_exists='append')
    # except Exception as e:
    #     print(f"the error is : {e}")
    try:
        # load df directly to bigquery
        table_id = 'glass-haven-360720.transformed_data_for_cafe.basket'
        job = client.load_table_from_dataframe(basket_items, table_id)
        print("basket table has been added")
    except Exception as e:
        print(e)
    
    
def LoadTransactionDF(df, store_id, client):
    
    """Transform df to fit in transaction table, return df."""
    
    # drop unwanted columns
    transaction = df.drop(columns=['basket_items', 'items'])
    # replace store name by its id
    transaction['store'] = store_id
    # Rename column names to match DB columns
    transaction.rename(columns={'store':'store_id', 'cash_or_card':'payment_method'}, inplace=True)
    transaction.reset_index(inplace=True)
    print(transaction)
    # try:
    #     # load df directly to bigquery
    #     transaction.to_gbq("transformed_data_for_cafe.transaction", if_exists='append')
    #     print("Transaction table has been loaded.")
    # except Exception as e:
    #     print(f"the error is : {e}")
    try:
        table_id = 'glass-haven-360720.transformed_data_for_cafe.transaction'
        job = client.load_table_from_dataframe(transaction, table_id)
        print("transaction table has been added")
    except Exception as e:
        print(e)