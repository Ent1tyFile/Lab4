import os

import boto3
import botocore


def create_key_pair(key_pair_name, region, file_name):
    ec2_client = boto3.client("ec2", region_name=region)

    try:
        key_pair = ec2_client.create_key_pair(KeyName=key_pair_name)
        private_key = key_pair["KeyMaterial"]

        with os.fdopen(os.open(file_name, os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:
            handle.write(private_key)
    except botocore.exceptions.ClientError as e:
        print('Error:', e)


def create_instance(instance_type, key_pair_name, region, ami_id):
    ec2_client = boto3.client("ec2", region_name=region)

    try:
        instances = ec2_client.run_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_type,
            KeyName=key_pair_name)

        print(instances["Instances"][0]["InstanceId"])

        return instances["Instances"][0]["InstanceId"]
    except botocore.exceptions.ClientError as e:
        print('Error:', e)


def get_public_ip(instance_id, region):
    ec2_client = boto3.client("ec2", region_name=region)

    try:
        reservations = ec2_client.describe_instances(InstanceIds=[instance_id]).get("Reservations")

        for reservation in reservations:
            for instance in reservation['Instances']:
                ip = instance.get("PublicIpAddress")
                print(ip)

                return ip
    except botocore.exceptions.ClientError as e:
        print('Error:', e)


def get_running_instances(region):
    ec2_client = boto3.client("ec2", region_name=region)
    reservations = ec2_client.describe_instances(Filters=[{
        "Name": "instance-state-name",
        "Values": ["running"],
    }, {
        "Name": "instance-type",
        "Values": ["t4g.nano"]
    }
    ]).get("Reservations")
    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            public_ip = instance["PublicIpAddress"]
            private_ip = instance["PrivateIpAddress"]
            print(f"{instance_id}, {instance_type}, {public_ip}, {private_ip}")


def stop_instance(instance_id, region):
    ec2_client = boto3.client("ec2", region_name=region)
    try:
        response = ec2_client.stop_instances(InstanceIds=[instance_id])

        print(response)

        return response
    except botocore.exceptions.ClientError as e:
        print('Error:', e)


def terminate_instance(instance_id, region):
    ec2_client = boto3.client("ec2", region_name=region)
    try:
        response = ec2_client.terminate_instances(InstanceIds=[instance_id])

        print(response)

        return response
    except botocore.exceptions.ClientError as e:
        print('Error:', e)


def create_bucket(bucket_name, region):
    s3_client = boto3.client('s3', region_name=region)

    try:
        location = {'LocationConstraint': region}
        response = s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)

        print(response)

        return response
    except botocore.exceptions.ClientError as e:
        print('Error:', e)


def s3_upload_file(file_name, bucket_name, s3_obj_name):
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(Filename=file_name, Bucket=bucket_name, Key=s3_obj_name)

        print("Successfully uploaded the file")

        return response
    except botocore.exceptions.ClientError as e:
        print('Error:', e)
    except FileNotFoundError as e:
        print('File error:', e)
    except boto3.exceptions.S3UploadFailedError as e:
        print('S3 error:', e)
    except botocore.exceptions.ParamValidationError as e:
        print('S3 file error:', e)


def s3_delete_file(bucket_name, s3_obj_name):
    s3_client = boto3.client('s3')
    try:
        response = s3_client.delete_object(Bucket=bucket_name, Key=s3_obj_name)

        print(response)

        return response
    except botocore.exceptions.ClientError as e:
        print('Error:', e)
    except FileNotFoundError as e:
        print('File error:', e)
    except boto3.exceptions.S3UploadFailedError as e:
        print('S3 error:', e)
    except botocore.exceptions.ParamValidationError as e:
        print('S3 file error:', e)


def destroy_bucket(bucket_name):
    s3_client = boto3.client('s3')
    try:
        objects = s3_client.list_objects(Bucket=bucket_name)

        if 'Contents' in objects:
            for obj in objects['Contents']:
                s3_delete_file(bucket_name, obj['Key'])

        response = s3_client.delete_bucket(Bucket=bucket_name)

        print(response)

        return response
    except botocore.exceptions.ClientError as e:
        print('Error:', e)


def main():
    key_pair_name = "ec2-keypair"
    region_name = "us-west-2"
    write_file = "aws_ec2_key.pem"

    # create_key_pair(key_pair_name, region_name, write_file)

    instance_type = "t4g.nano"
    ami_id = "ami-0b0154d3d8011b0cd"

    instance_id = create_instance(instance_type, key_pair_name, region_name, ami_id)
    get_public_ip(instance_id, region_name)
    stop_instance(instance_id, region_name)
    terminate_instance(instance_id, region_name)

    bucket_name = "lnu-lab4-b1"

    create_bucket(bucket_name, region_name)
    s3_upload_file("usd_course.csv", bucket_name, "usd.csv")
    s3_delete_file(bucket_name, "file1.csv")
    destroy_bucket(bucket_name)


if __name__ == '__main__':
    main()
