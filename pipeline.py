import os
from os import getenv
import pandas as pd
from sqlalchemy import create_engine
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, IntegerType, FloatType, TimestampType
from pyspark.sql import DataFrameWriter
from prefect import flow , task
from helper import create_table, get_spark_table_schema
from glob import glob

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
def concat_data(sample=True):
    print('Reading Data...')
    with SparkSession.builder.master("local[*]").appName("zoomcamp_project").getOrCreate() as spark:
        if sample:
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
        result= oct.union(nov)
        print('Schema: ', result.printSchema())
        print(f'total data size is: {result.count()}')
        print('Finished Concatenation.')
        # os.system("rm -r data/") #remove csv files
        result.write.format("parquet")\
            .option("mode", "overwrite")\
            .save("concatenated_data") #create csv file for the combined data
    print("Finished Concatentaning the Data")        
@task
def clean_data():
    os.system("mkdir temp")
    with SparkSession.builder.master("local[*]").appName("zoomcamp_project").config("spark.local.dir", f"{os.getcwd()}/temp").getOrCreate() as spark:
        concatenated_data= spark.read.schema(get_spark_table_schema()).parquet("./concatenated_data/")
        print('Before droping nulls: ', concatenated_data.count())
        concatenated_data= concatenated_data.na.drop(subset=["event_time"])
        print('After droping nulls: ', concatenated_data.count())
        print("Combined Data Schema: ", concatenated_data.printSchema())
        print('Before droping duplicates: ', concatenated_data.count())
        concatenated_data= concatenated_data.distinct() #drop duplicates
        print('After droping duplicates: ', concatenated_data.count())
        concatenated_data.repartition(20)\
            .write.option("mode", "overwrite").parquet('cleaned_data')
        print('Finished Data Cleaning!')

@task
def insert_data_indo_datalake(bucket_name= "zoomcamp-project", unzipped=False):
    if unzipped:
            os.system(f"aws s3 cp data/2019-Nov.csv s3://{bucket_name}/original_data/")
            os.system(f"aws s3 cp data/2019-Oct.csv s3://{bucket_name}/original_data/")
    os.system(f"aws s3 cp ecommerce-behavior-data-from-multi-category-store.zip s3://{bucket_name}/original_data/")
    os.system(f"aws s3 cp cleaned_data/ s3://{bucket_name}/cleaned_data/ --recursive")
    print("Finished Inserting Data into S3 bucket")


# @task
# def insert_data_into_db():
#     create_table()
#     files= glob('cleaned_data/*.parquet')
#     for f in files:
#         print(f)
#         df= pd.read_parquet(f)
#         print(df.head())
#         connection= create_engine(f'postgresql://{getenv("username")}:{getenv("password")}@{getenv("host")}:{getenv("port")}/{getenv("database")}')
#         df.to_sql(name="events", con= connection, if_exists="append", index=False, chunksize=int(10e5))
#     print("Finished Inserting Data into Database")

@task
def insert_data_into_db(clean_data_path="./cleaned_data/"):
    clean_data_files= os.listdir(clean_data_path)
    clean_data_files= [str(os.getcwd())+'/cleaned_data/'+i for i in clean_data_files]
    i=1
    with SparkSession.builder.master("local[*]").appName("zoomcamp_project").getOrCreate() as spark:
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


@flow(name='main flow')
def run_flow():
    download_data(download=True)
    concat_data(sample=False)
    clean_data()
    insert_data_indo_datalake(unzipped=False)
    insert_data_into_db()
    

if __name__=="__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_flow()


