# specific aws cli version
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-2.11.4.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# create kaggle dir
mkdir ~/.kaggle
touch ~/.kaggle/kaggle.json

# add POSTGRES JDBC jar file
wget -P /home/ec2-user/.local/lib/python3.9/site-packages/pyspark/jars/ https://jdbc.postgresql.org/download/postgresql-42.6.0.jar 
# create json to add kaggle token inside
touch ~/.kaggle/kaggle.json

# installing pip3
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
echo "export PATH=~/.local/bin:$PATH" >> .bash_profile
source ~/bash_profile
# installing java for pyspark
sudo amazon-linux-extras enable corretto8
sudo yum install java-1.8.0-amazon-corretto
sudo yum install java-1.8.0-amazon-corretto-devel

pip3 install -r requirements.txt
python3 pipeline.py