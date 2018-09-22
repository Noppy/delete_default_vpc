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

