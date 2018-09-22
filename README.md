# NAME
delete_default_vpc.py : The python tool to delete the default VPC for each region
# SYNOPSIS
    usage: delete.vpc.py [-h] [-d] [-w WAIT_TIME] -a ACCESS_KEY_ID -s SECRET_ACCESS_KEY 

# DESCRIPTION
- positional arguments:
    - -a ACCESS_KEY_ID     :Specify a target account's ACCESS KEY ID
    - -s SECRET_ACCESS_KEY :Specify a target account's SECRET KEY ID
    
- optional arguments:  
    - -h, --help : show this help message and exit  
    - -d, --dry-run : Dry-Run(Do not change resouces)
    - -w WAIT_TIME, --wait-time WAIT_TIME : Wait time(second) for delete instance and natgw
# Required environment
- Required Pakages
    - python 2.7
    - boto3 (AWS SDK for Python)
    - git (for setup)
# How to
## Setup
### install boto3
refer [AWS documents: boto3 QuickStart](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html)
### clone this repository
clone git repository to a ppropriate folder.
    git clone https://github.com/Noppy/delete_default_vpc.git
## used
    ./delete.vpc.py -a 'AWS_ACCESS_KEY_ID' -s 'AWS_SECRET_KEY_ID'
# ATTENTION!! 
You must promptly delete user access key id and secret key id for security. Because there is some possibility that those keys are maybe logged to os  logs(e.g. command history, /var/log/messages, /var/log/secure...).
