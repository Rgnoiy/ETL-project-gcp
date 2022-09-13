from google.cloud import bigquery

def create_tables(client):
    
    """ create tables in BigQuery"""
      
    commands = (
    """
    CREATE TABLE IF NOT EXISTS cafe_data.transaction(
      transaction_hash_id STRING,
      timestamp STRING,
      store_id STRING,
      total_price FLOAT,
      payment_method STRING,
    );
    """,
    
    
    """
    CREATE TABLE IF NOT EXISTS cafe_data.product(
      product_id STRING,
      product_name STRING,
      price DECIMAL,
    );
    """,
    
    """
    CREATE TABLE IF NOT EXISTS cafe_data.store(
      store_id STRING,
      store_name STRING,
    );
    """,
    
    
    """
    CREATE TABLE IF NOT EXISTS cafe_data.basket(
      transaction_hash_id STRING,
      product_id STRING,
      quantity INT
    );
    """)
    
    try:
        # create table one by one
        for command in commands:
            client.query(command)
        print("Tables have been created.")
    except Exception as e: 
      print(e)