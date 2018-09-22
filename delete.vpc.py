#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  delete_default_vpc.py
#  ======
#  Copyright (C) 2018 n.fujita
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from __future__ import print_function

import sys
import argparse
import time
import boto3
from botocore.exceptions import ClientError


import pprint

# global values
dry_run = True
wait_time_second = 180

#---------------------------
# Arguments
#---------------------------
def get_args():
    parser = argparse.ArgumentParser( \
        description='delete default vpcs.')

    parser.add_argument('-d','--dry-run', \
        action='store_true',             \
        default=False,                   \
        required=False,                  \
        help='Enable dry-run')

    parser.add_argument('-w','--wait-time', \
        action='store',                  \
        type=int,                        \
        default=180,                     \
        required=False,                  \
        help='Wait time(second) for deleting instances')

    parser.add_argument('-a','--access_key_id', \
        action='store',                         \
        default='',                             \
        type=str,                               \
        required=True,                          \
        help='Specify "access key".')

    parser.add_argument('-s','--secret_access_key', \
        action='store',                         \
        default='',                             \
        type=str,                               \
        required=True,                          \
        help='Specify "secret key".')

    return( parser.parse_args() )


#---------------------------
# "yes or no question" logiA functionsc
#---------------------------
def prompt_for_input(prompt = "", val = None):
    if val is not None:
        return val
    print( prompt + " ")
    return sys.stdin.readline().strip()


def yes_or_no(s):
    s = s.lower()
    if s in ("y", "yes", "1", "true", "t"):
        return True
    elif s in ("n", "no", "0", "false", "f"):
        return False
    raise ValueError, "A yes or no response is required"


def answer(message):
    ret = False
    while 1:
        print( "\n" + message )
        res = prompt_for_input("Yes or No?")
        try:
            if yes_or_no(res):
                ret = True
            else:
                ret = False
            break
        except ValueError, e:
            print("ERROR: ", e)

    return ret


#---------------------------
# Initialize functions
#---------------------------
def get_session( access_key, secret_key, region):

    s = boto3.session.Session(              \
        aws_access_key_id     = access_key, \
        aws_secret_access_key = secret_key, \
        region_name           = region)
    return s


def get_GetCallerIdentity(session):
    sts = session.client('sts')
    return sts.get_caller_identity()['Account']


def get_regions(session):
    regions = []
    regions = session.get_available_regions('ec2')

    return regions

#---------------------------
# delete resources functions
#---------------------------
def delete_instances(c, vpcid):

    response = c.describe_instances( \
        Filters=[ { 'Name': 'vpc-id', 'Values':[ vpcid ], } ] )
 
    ids = [] 
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            ids.append(instance['InstanceId'])
  
    if len(ids) > 0:
        try:
            print("    Remove Instance(s):", ids)
            c.terminate_instances( InstanceIds=ids, DryRun=dry_run)
        except ClientError as e:
            print(e.message)
   
        if dry_run:
            return
    
        #Wait and check
        for i in ids:
            wait_timeout = time.time() + wait_time_second
            while wait_timeout > time.time():
                r = c.describe_instances( \
                    Filters=[ { 'Name': 'instance-id', 'Values':[ i ], } ] )
                stat = r['Reservations'][0]['Instances'][0]['State']['Name'] 
                print("    InstanceId:",i,"  Status->",stat)
                if stat == 'terminated':
                    break

                # Wait 10 seconds
                time.sleep(10)
    return    


def delete_natgw(c, vpcid):

    response = c.describe_nat_gateways( \
        Filters=[ { 'Name': 'vpc-id', 'Values':[ vpcid ], } ] )

    natgws = map(lambda x:x['NatGatewayId'], response['NatGateways'])
    
    for natgw in natgws:
        try:
            print("    Remove NatGW:", natgw)
            c.delete_nat_gateway(NatGatewayId=natgw)
        except ClientError as e:
            print(e.message)

        #Wait and check
        wait_timeout = time.time() + wait_time_second
        while wait_timeout > time.time():
            response = c.describe_nat_gateways( \
                Filters=[ { 'Name': 'nat-gateway-id', 'Values':[ natgw ], } ] )
            stat = response['NatGateways'][0]['State']
            print("    InstanceId:",natgw,"  Status->",stat)
            if stat == 'deleted':
                break

            # Wait 10 seconds
            time.sleep(10)

    return


def delete_sg(c, vid):

    response = c.describe_security_groups( \
        Filters=[ { 'Name': 'vpc-id', 'Values':[ vid ], } ] )

    for sgs in response['SecurityGroups']:
        if sgs['GroupName'] != 'default':
            try:
                print("    Remove SecurityGroup:", sgs['GroupId'])
                c.delete_security_group(GroupId=sgs['GroupId'], DryRun=dry_run)
            except ClientError as e:
                print(e.message)


def delete_acl(c, vid):

    response = c.describe_network_acls( \
        Filters=[ { 'Name': 'vpc-id', 'Values':[ vid ], } ] )

    for acls in response['NetworkAcls']:
        if not acls['IsDefault']:
            try:
                print("    Remove Network ACL:", acls['NetworkAclId'])
                c.delete_network_acl(NetworkAclId=acls['NetworkAclId'], DryRun=dry_run)
            except ClientError as e:
                print(e.message)

    return


def delete_rtb(c, vid):

    response = c.describe_route_tables( \
        Filters=[ { 'Name': 'vpc-id', 'Values':[ vid ], } ] )

    for rtb in response['RouteTables']:

        # Detach a route table from a subnet.
        main = False
        for association in  rtb['Associations']:
            # Skip, when it is a default route table. 
            if association['Main']:
                main = True
                continue

            # Detach a route table from a subnet.
            try:
                print("    Detach RouteTable: ",association['RouteTableId']," from ",association['SubnetId'])
                c.disassociate_route_table(  \
                    AssociationId = association['RouteTableAssociationId'], \
                    DryRun = dry_run)
            except ClientError as e:
                print(e.message)
        
        # Delete a route table 
        if not main:
            try:
                print("    Remove RouteTable:", rtb['RouteTableId'])
                c.delete_route_table(RouteTableId=rtb['RouteTableId'], DryRun=dry_run)
            except ClientError as e:
                print(e.message)

    return


def delete_sub(c, vid):

    response = c.describe_subnets( \
        Filters=[ { 'Name': 'vpc-id', 'Values':[ vid ], } ] )

    subs = map(lambda x:x['SubnetId'], response['Subnets']) 

    for sub in subs:
        try:
            print("    Remove Subnet:", sub)
            c.delete_subnet(SubnetId=sub, DryRun=dry_run)
        except ClientError as e:
            print(e.message)

    return


def delete_igw(c, vid):

    response = c.describe_internet_gateways( \
        Filters=[ { 'Name': 'attachment.vpc-id', 'Values':[ vid ], } ] )

    for igw in response['InternetGateways']:
        # Detach from vpc
        for attach in igw['Attachments']:
            if attach['State'] == 'available':
                c.detach_internet_gateway( \
                    InternetGatewayId = igw['InternetGatewayId'], \
                    VpcId = attach['VpcId'],                      \
                    DryRun=dry_run )

        # Delete a igw
        try:
            print("    Remove IGW:", igw['InternetGatewayId'])
            c.delete_internet_gateway(InternetGatewayId=igw['InternetGatewayId'], DryRun=dry_run)
        except ClientError as e:
            print(e.message)

    return


def delete_vpc(c, vid):

    try:
        print("    Remove VPC:", vid)
        c.delete_vpc(VpcId=vid, DryRun=dry_run)
    except ClientError as e:
        print(e.message)

    return


#---------------------------
# Main functionG
#---------------------------
def main():
    global dry_run
    global wait_time_second

    # Initialize
    args = get_args()
    dry_run = args.dry_run
    wait_time_second = args.wait_time

    # Get Account-ID and regions
    session = get_session(                   \
        access_key = args.access_key_id,     \
        secret_key = args.secret_access_key, \
        region     = 'us-east-1')
    account = get_GetCallerIdentity(session);
    regions = get_regions(session);

    # Comfirm the target accunt.
    if not answer( "Account: " + account + "\nDo you delete the default VPCs for this account?" ):
        return False

    # Delete 
    for region in regions:
        try:
            session = get_session(                   \
                access_key = args.access_key_id,     \
                secret_key = args.secret_access_key, \
                region     = region )
            client = session.client('ec2')
            attributes = client.describe_account_attributes( \
                AttributeNames = ['default-vpc'] )
        except ClientError as e:
            print(e.message)
            return False
        else:
            print( region.upper() )

            for attribute in attributes['AccountAttributes'][0]['AttributeValues']:
                vpcid = attribute['AttributeValue']
                print("  Default VPC-ID:", vpcid)

                if vpcid != 'none':
                    delete_instances(client, vpcid)
                    delete_sg( client, vpcid)
                    delete_acl(client, vpcid)
                    delete_rtb(client, vpcid)
                    delete_natgw(client, vpcid)
                    delete_sub(client, vpcid)
                    delete_igw(client, vpcid)    
                    delete_vpc(client, vpcid)

    return True


if __name__ == "__main__":
    sys.exit(main())

