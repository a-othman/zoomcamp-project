# installing pip3
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
echo "export PATH=~/.local/bin:$PATH" >> .bash_profile
source ~/PROFILE_SCRIPT
# installing java for pyspark
sudo amazon-linux-extras enable corretto8
sudo yum install java-1.8.0-amazon-corretto
sudo yum install java-1.8.0-amazon-corretto-devel

pip3 install -r requirements.txt
python3 pipeline.py