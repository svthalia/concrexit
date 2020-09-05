#!/usr/bin/env bash

set -o errexit -o verbose 

if [ -z "${GITHUB_ACTIONS}" ]; then
    echo "Not running in GitHub Actions."
    exit 1;
fi

mapfile -t running_instance_ids < <(
    aws ec2 describe-instances  \
    --filters "Name=tag:Name,Values=concrexit-review-${COMMIT_SHA}" \
              "Name=instance-state-name,Values=running,shutting-down,stopping,stopped" \
    --query "Reservations[].Instances[].[InstanceId]" \
    --output "text" 
)
if [ "${#running_instance_ids[@]}" -gt 0 ]; then
    aws ec2 terminate-instances --instance-ids "${running_instance_ids[@]}"
fi

new_instance_id=$(
    aws ec2 run-instances \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=concrexit-review-${COMMIT_SHA}}]" \
    --image-id "ami-02df9ea15c1778c9c" \
    --security-group-ids "sg-0a9de5925f983f6c1" \
    --subnet-id "subnet-072547905992bb9a1" \
    --instance-type "t2.micro" \
    --key-name "concrexit-review" \
    --instance-initiated-shutdown-behavior "terminate" \
    --user-data file://resources/continuous-integration/review/ec2-bootstrap.sh | 
        jq --raw-output ".Instances[0].InstanceId"
    )
aws ec2 wait instance-running --instance-ids "${new_instance_id}"
