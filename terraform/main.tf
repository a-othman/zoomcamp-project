provider "aws" {
    region = "us-east-1"
}

# Create a security group that allows SSH access only from your IP address
resource "aws_security_group" "ssh_access" {
  name_prefix = "ssh_access_"
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = [var.my_ip_address]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Launch an EC2 instance with 50 GB additional storage
resource "aws_instance" "zoomcamp_ec2" {
  ami = "ami-02396cdd13e9a1257"
  instance_type = "t3.xlarge"
  # instance_type = "t2.micro"

  user_data = <<-EOF
              #!/bin/bash
              sudo yum -y install git
              wget https://jdbc.postgresql.org/download/postgresql-42.6.0.jar
              git clone https://github.com/a-othman/zoomcamp-project.git
              EOF

  key_name = "zoomcamp" # Replace with your SSH key name, make sure you have created one with same name
  vpc_security_group_ids = [aws_security_group.ssh_access.id]
  iam_instance_profile = aws_iam_instance_profile.ec2_instance_profile.name
  root_block_device {
    volume_size = 100 # Replace with your desired root volume size
    # volume_size = 20
  }

}

resource "aws_s3_bucket" "zoomcamp-project" {
  bucket = "zoomcamp-project"
  force_destroy= true
}



# Create an IAM role for EC2 instance
resource "aws_iam_role" "ec2_role" {
  name = "ec2_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Attach S3 full access policy to IAM role
resource "aws_iam_role_policy_attachment" "s3_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  role       = aws_iam_role.ec2_role.name
}

# Create an IAM Instance Profile and associate it with the IAM role
resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "ec2-instance-profile"
  role = aws_iam_role.ec2_role.name
}


# Grant S3 access to the EC2 instance
resource "aws_iam_role_policy" "s3_access" {
  name = "s3_access"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:*"
        ]
        Resource = [
          "${aws_s3_bucket.zoomcamp-project.arn}",
          "${aws_s3_bucket.zoomcamp-project.arn}/*"
        ]
      }
    ]
  })
}


# Create a security group that allows access to db
resource "aws_security_group" "db_security_group" {
  name_prefix = "db_security_group"
  ingress {
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Create a PostgreSQL database instance
resource "aws_db_instance" "zoomcamp_db" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "13.4"
  instance_class       = "db.t4g.micro"
  db_name              = "zoomcamp_db"
  username             = "othman"
  password             = "mysecretpassword"
  parameter_group_name  = "default.postgres13"
  skip_final_snapshot  = true
  vpc_security_group_ids = [aws_security_group.db_security_group.id]
  # Make the database publicly accessible
  publicly_accessible = true
}

output "database_endpoint" {
  value = aws_db_instance.zoomcamp_db.endpoint
}