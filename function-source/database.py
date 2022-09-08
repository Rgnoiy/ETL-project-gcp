from google.cloud import bigquery

def create_tables(client):
    
    """ create tables in BigQuery"""
      
    commands = (
    """
    CREATE TABLE IF NOT EXISTS transformed_data_for_cafe.transaction(
      transaction_hash_id STRING,
      timestamp DATETIME,
      store_id STRING,
      total_price DECIMAL,
      payment_method STRING,
    );
    """,
    
    
    """
    CREATE TABLE IF NOT EXISTS transformed_data_for_cafe.product(
      product_id STRING,
      product_name STRING,
      price DECIMAL,
    );
    """,
    
    """
    CREATE TABLE IF NOT EXISTS transformed_data_for_cafe.store(
      store_id STRING,
      store_name STRING,
    );
    """,
    
    
    """
    CREATE TABLE IF NOT EXISTS transformed_data_for_cafe.basket(
      transaction_hash_id STRING,
      product_id STRING,
      quantity int
    );
    """)
    
    try:
        # create table one by one
        for command in commands:
            client.query(command)
        print("Tables have been created.")
    except Exception as e: 
      print(e)