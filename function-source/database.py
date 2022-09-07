from google.cloud import bigquery

def create_tables(client):
    
    """ create tables in BigQuery"""
      
    commands = (
    """
    CREATE TABLE IF NOT EXISTS transformed_data_for_cafe.transaction(
      transaction_hash_id BIGINT,
      timestamp DATETIME,
      store_id INT,
      total_price DECIMAL,
      payment_method STRING,
    );
    """,
    
    
    """
    CREATE TABLE IF NOT EXISTS transformed_data_for_cafe.product(
      product_id INT,
      product_name STRING,
      price DECIMAL,
    );
    """,
    
    """
    CREATE TABLE IF NOT EXISTS transformed_data_for_cafe.store(
      store_id INT,
      store_name STRING,
    );
    """,
    
    
    """
    CREATE TABLE IF NOT EXISTS transformed_data_for_cafe.basket(
      transaction_hash_id BIGINT,
      product_id int,
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