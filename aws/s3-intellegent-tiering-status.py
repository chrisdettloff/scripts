import boto3
from botocore.exceptions import ClientError

def main():
    s3 = boto3.client('s3')

    # Get a list of all buckets
    response = s3.list_buckets()
    buckets = response['Buckets']

    # Iterate over each bucket
    for bucket in buckets:
        bucket_name = bucket['Name']
        intelligent_tiering_enabled = False

        # Check for Intelligent-Tiering configurations
        try:
            configs = []
            paginator = s3.get_paginator('list_bucket_intelligent_tiering_configurations')
            page_iterator = paginator.paginate(Bucket=bucket_name)

            for page in page_iterator:
                configs.extend(page.get('IntelligentTieringConfigurationList', []))

            for config in configs:
                if config['Status'] == 'Enabled':
                    intelligent_tiering_enabled = True
                    break

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                print(f"Bucket {bucket_name} does not exist.")
                continue
            elif error_code == 'NoSuchConfiguration':
                # No Intelligent-Tiering configurations found; proceed to check lifecycle rules
                pass
            else:
                print(f"Error checking Intelligent-Tiering for bucket {bucket_name}: {e}")
                continue

        # If not found in Intelligent-Tiering configurations, check lifecycle configurations
        if not intelligent_tiering_enabled:
            try:
                lifecycle = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                rules = lifecycle.get('Rules', [])
                for rule in rules:
                    if rule.get('Status') == 'Enabled':
                        transitions = rule.get('Transitions', [])
                        for transition in transitions:
                            if transition.get('StorageClass') == 'INTELLIGENT_TIERING':
                                intelligent_tiering_enabled = True
                                break
                        if intelligent_tiering_enabled:
                            break
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'NoSuchLifecycleConfiguration':
                    # No lifecycle configurations found
                    pass
                else:
                    print(f"Error checking lifecycle configuration for bucket {bucket_name}: {e}")
                    continue

        status = 'Enabled' if intelligent_tiering_enabled else 'Disabled'
        print(f"Bucket: {bucket_name}, Intelligent-Tiering: {status}")

if __name__ == '__main__':
    main()

