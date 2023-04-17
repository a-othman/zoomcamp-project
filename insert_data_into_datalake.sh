sudo yum update
sudo yum install python3
sudo yum install python3-pip
pip3 install kaggle
# ensure ec2 instace or your pc has an kaggle api token to be able to download data
kaggle datasets download -d mkechinov/ecommerce-behavior-data-from-multi-category-store
unzip ecommerce-behavior-data-from-multi-category-store.zip
head -n 1000 2019-Nov.csv > nov-sample.csv
head -n 1000 2019-Oct.csv > oct-sample.csv
aws s3 cp ecommerce-behavior-data-from-multi-category-store.zip s3://zoomcamp
aws s3 cp 2019-Nov.csv s3://zoomcamp
aws s3 cp 2019-Oct.csv s3://zoomcamp
aws s3 cp nov-sample.csv s3://zoomcamp
aws s3 cp oct-sample.csv s3://zoomcamp

