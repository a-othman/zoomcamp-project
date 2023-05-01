import psycopg2
from pyspark.sql.types import StructType, TimestampType, StringType, IntegerType, FloatType
from os import getenv
def get_spark_table_schema():
    schema= StructType() \
            .add("event_time", TimestampType(), True) \
            .add("event_type", StringType(), True)\
            .add("product_id", StringType(), True)\
            .add("category_id", StringType(), True)\
            .add("category_code", StringType(), True)\
            .add("brand", StringType(), True)\
            .add("price", FloatType(), True)\
            .add("user_id", IntegerType(), True)\
            .add("user_session", StringType(), True)
    return schema
def create_staging_schema():
    try:
        connection= psycopg2.connect(host=getenv("host"), port=getenv("port"), database=getenv('database'),
                                    user=getenv("username"), password=getenv("password"))
        
        cur= connection.cursor()
        cur.execute("""create schema IF NOT EXISTS staging""")
        connection.commit()
    finally:
        cur.close()
        connection.close()
        print('Connection Closed!')
    print('Finished Schema Creation!!')

def create_table():
    try:
        connection= psycopg2.connect(host=getenv("host"), port=getenv("port"), database=getenv('database'),
                                    user=getenv("username"), password=getenv("password"))

        cur= connection.cursor()
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS events (
        event_time TIMESTAMP,
        event_type VARCHAR(50),
        product_id VARCHAR(50),
        category_id VARCHAR(50),
        category_code VARCHAR(50),
        brand VARCHAR(50),
        price FLOAT,
        user_id BIGINT,
        user_session VARCHAR(50)
        ) PARTITION BY RANGE (event_time);

        CREATE TABLE IF NOT EXISTS events_oct_2019 PARTITION OF events
        FOR VALUES FROM ('2019-10-01') TO ('2019-10-31');
        
        CREATE TABLE IF NOT EXISTS event_nov_2019 PARTITION OF events
        FOR VALUES FROM ('2019-11-01') TO ('2019-11-30');
        """)
        connection.commit()
        print('Success!')
    finally:
        cur.close()
        connection.close()
        print('Connection Closed!')
    print('Finished Table Creation!!')


if __name__=="__main__":
    create_table()