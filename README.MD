## This is Final Project for Zoomcamp Data Engineering Course
### Project Descreption:
I have selected a [dataset](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store) for an ecommerce platform, where users' activity is stroed. The dataset contains around 110 million rows.
The data contains the following columns:
- event_time: Time when event happened at (in UTC).
- event_type: Only one kind of event: purchase.
- product_id: ID of a product
- category_id: Product's category ID
- category_code: Product's category taxonomy (code name) if it was possible to make it. Usually present for meaningful categories and skipped for different kinds of accessories.
- brand: Downcased string of brand name. Can be missed.
- price: Float price of a product. Present.
- user_id: Permanent user ID.
- user_session:	Temporary user's session ID. Same for each user's session. Is changed every time user come back to online store from a long pause.

I did a batch job on the data using pyspark, cleaned the dataset, drop the duplicates, and the nulls and did transformations on the dataset to find the distributions of users actions, and daily sales during these two months.
I have used tableau public to create the dashboard representing these final visualizations.
### Visualizations:
     
    ![I have created two tiles:
    - The first one is a bar chart showing the count of each event users did while shopping. 
    - The second is a time series data showing total daily sales customers.]
    (https://github.com/a-othman/zoomcamp-project/blob/main/dashboard.png))
image.png

### How to run the project: 
- Step 1:create the infra structure on aws using three commands: terraform init, terraform plan, terraform apply
    
    Note 1: in variables.tf add your ip address so you can ssh connect to the ec2 instance followed by "/32".

    For example: 192.158.1.38/32


    Note 2: To use your IAM credentials to authenticate the Terraform AWS provider follow this [link](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-build)
- Step 2: create an access key for the ec2 instance and call it  **zoomcamp**. I have used this exact name in terraform script so you can ssh the ec2 instance.
    
    Note: If you need to know how to create a key pair on aws, follow this [link](https://docs.aws.amazon.com/servicecatalog/latest/adminguide/getstarted-keypair.html)
- Step 3: connect to the ec2 instance machine using the command below, make sure to replace EC2-IP with the machine ip address: 
    ```
        ssh -i "zoomcamp.pem" EC2-IP
    ```

- Step 4: on the ec2 machine clone the repo using the following command:
    ```
        git clone https://github.com/a-othman/zoomcamp-project.git
    ```
- Step 5: 
        
        1. Create a kaggle token for authenticaltion and download the data initially. Follow this link for [steps](https://www.kaggle.com/docs/api).
        
        2. Once you have created the token, you should have be able to download a json file containing username, and token which you will use on the remote ec2 instance.
        
        3.execute the following commands:
            ```
            mkdir ~/.kaggle
            touch ~/.kaggle/kaggle.json
            ```
        5. Add the kaggle.json credentials onto the directroy you have created on the ec2 instance.
- Step 6: Change directroy "zoomcamp-project"
- Step 7: add the database host into the .env file. 
- Step 8: run the bash ec2_configure.sh. This file installs all pyspark, jar file to connect with the postgres database, pip requirements, and runs the pipeline once the installation finishes. 
- Step 9: One the pipeline finishes, you can connect onto the database yourself to check that data has been inserted properly.
- Step 10: Once you finish, you can run the command below, to delete all the resources you have created on aws. 
  ```
    terrform destroy
  ```

