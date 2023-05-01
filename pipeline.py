import os
from os import getenv
import pandas as pd
from sqlalchemy import create_engine
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, count
from pyspark.sql.functions import sum as _sum
from prefect import flow , task
from helper import create_table, get_spark_table_schema, create_staging_schema

@task(name='Download Data')
def download_data(download=False, source="mkechinov/ecommerce-behavior-data-from-multi-category-store"):
    os.system("mkdir samples")
    if download:
        os.system("mkdir data")
        print('Started Downloading Data...')
        command= f"kaggle datasets download -d {source}"
        os.system(command) #get data from kaggle
        print('Finished Downloading Data')
        os.system(f"unzip {command.split('/')[-1]}.zip -d data/")
    os.system(f"head -n 100000 data/2019-Nov.csv > samples/nov-sample.csv")
    os.system(f"head -n 100000 data/2019-Oct.csv > samples/oct-sample.csv")
    print('Finished Downloading Data')   

@task(name='Concat Data')
def clean_data(sample=True):
    print('Reading Data...')
    with SparkSession.builder.master("local[*]").appName("zoomcamp_project").config("spark.local.dir", f"{os.getcwd()}/temp").getOrCreate() as spark:
        if sample: #used this for testing purposes
            oct = spark.read.option('header', True).schema(get_spark_table_schema()).csv("samples/nov-sample.csv")
            print('Read Oct')
            nov = spark.read.option('header', True).schema(get_spark_table_schema()).csv("samples/oct-sample.csv")
            print('Read Nov')
        else:
            oct = spark.read.option('header', True).schema(get_spark_table_schema()).csv("data/2019-Oct.csv")
            print('Read Oct')
            nov = spark.read.option('header', True).schema(get_spark_table_schema()).csv("data/2019-Nov.csv")
            print('Read Nov')
        print('Concatentating Data...')
        print(f'Oct data size is: {oct.count()}\n Nov data size is: {nov.count()}')
        concatenated_data= oct.union(nov)
        print('Schema: ', concatenated_data.printSchema())
        print(f'total data size is: {concatenated_data.count()}')
        print('Finished Concatenation.')
        concatenated_data= concatenated_data.na.drop(subset=["event_time"]) #droping nulls
        concatenated_data= concatenated_data.distinct() #drop duplicates
        concatenated_data= concatenated_data.withColumn('date', to_date(col('event_time'))) #partitioning by date
        concatenated_data.repartition(20).write.option("header", "True")\
            .partitionBy("date")\
            .mode('overwrite')\
            .parquet('cleaned_data')
    print("Finished Cleaning the Data")        

@task
def transform(cleaned_data_path='./cleaned_data'):
    with SparkSession.builder.master("local[*]").appName("zoomcamp_project").config("spark.local.dir", f"{os.getcwd()}/temp").getOrCreate() as spark:
        # processing data for first visualization tile: user actions grouped
        df= spark.read.schema(get_spark_table_schema()).parquet(cleaned_data_path) 
        actions_type_count = df.groupBy('event_type').agg(count('*').alias('No of Events'))
        actions_type_count.write.option('header', True).mode('overwrite').csv('./actions_type_count')
        # processing data for second visualization tile: daily sales 
        sales_df= df.filter(col("event_type")=='purchase')
        daily_sales= sales_df.groupBy('date').agg(_sum('price').alias('Total Sales'))
        daily_sales.write.option('header', True).mode('overwrite').csv('./daily_sales')

@task
def insert_data_indo_datalake(bucket_name= "zoomcamp-project", unzipped=False):
    if unzipped:
            os.system(f"aws s3 cp data/2019-Nov.csv s3://{bucket_name}/original_data/")
            os.system(f"aws s3 cp data/2019-Oct.csv s3://{bucket_name}/original_data/")
    os.system(f"aws s3 cp ecommerce-behavior-data-from-multi-category-store.zip s3://{bucket_name}/original_data/")
    os.system(f"aws s3 cp cleaned_data/ s3://{bucket_name}/cleaned_data/ --recursive")
    print("Finished Inserting Data into S3 bucket")


@task
def insert_data_into_db(clean_data_path="./cleaned_data/"):
    create_staging_schema()
    create_table()
    clean_data_files= os.listdir(clean_data_path)
    clean_data_files= [str(os.getcwd())+'/cleaned_data/'+i for i in clean_data_files]
    i=1
    with SparkSession.builder.master("local[*]").appName("zoomcamp_project").getOrCreate() as spark:
        # raw data after cleaning
        for file in clean_data_files:
            df= spark.read.option('header', True).schema(get_spark_table_schema()).parquet(file)
            df.write \
            .format("jdbc") \
            .option("url", f"jdbc:postgresql://{getenv('host')}:{getenv('port')}/{getenv('database')}") \
            .option("dbtable", "events") \
            .option("user", getenv("username")) \
            .option("password", getenv("password")) \
            .option("driver", "org.postgresql.Driver") \
            .mode("append")\
            .save()
            print(f"Finished insertion {i}/{len(clean_data_files)}")
            i+=1
        # transformed data table 1
        df= spark.read.option('header', True).csv("actions_type_count")
        df.write \
            .format("jdbc") \
            .option("url", f"jdbc:postgresql://{getenv('host')}:{getenv('port')}/{getenv('database')}") \
            .option("dbtable", "staging.actions_type_count") \
            .option("user", getenv("username")) \
            .option("password", getenv("password")) \
            .option("driver", "org.postgresql.Driver") \
            .mode("overwrite")\
            .save()
        # transformed data table 2
        df= spark.read.option('header', True).csv("./daily_sales")
        df.write \
            .format("jdbc") \
            .option("url", f"jdbc:postgresql://{getenv('host')}:{getenv('port')}/{getenv('database')}") \
            .option("dbtable", "staging.daily_sales") \
            .option("user", getenv("username")) \
            .option("password", getenv("password")) \
            .option("driver", "org.postgresql.Driver") \
            .mode("overwrite")\
            .save()
        

@flow(name='main flow')
def run_flow():
    # download_data(download=True)
    clean_data(sample=False)
    # insert_data_indo_datalake(unzipped=False)
    transform()
    insert_data_into_db()
    

if __name__=="__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_flow()


