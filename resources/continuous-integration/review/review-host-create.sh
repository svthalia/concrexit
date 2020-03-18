#!/usr/bin/env bash

set -o errexit -o verbose 

if [ -z "${GITHUB_ACTIONS}" ]; then
    echo "Not running in Gitlab CI"
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
    --launch-template "LaunchTemplateId=lt-03762fc23450c2471,Version=5" \
    --user-data file://resources/continuous-integration/review/ec2-bootstrap.sh | 
        jq --raw-output ".Instances[0].InstanceId"
    )
aws ec2 wait instance-running --instance-ids "${new_instance_id}"

private_ipv4_address=$(aws ec2 describe-instances --instance-ids "${new_instance_id}" | jq --raw-output '.Reservations[0].Instances[0].PrivateIpAddress')
temporary_record_change_file=$(mktemp --suffix ".json") 
cat > "${temporary_record_change_file}" <<EOF
{
  "Comment": "Add or update private review host record",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "${CI_COMMIT_REF_SLUG}.private.review.technicie.nl",
        "Type": "A",
        "TTL": 10,
        "ResourceRecords": [{"Value": "${private_ipv4_address}"}]
      }
    }
  ]
}
EOF
route53_record_change_id=$(
    aws route53 change-resource-record-sets \
    --hosted-zone-id "Z3I4ZHBBD5NSHU" \
    --change-batch "file://${temporary_record_change_file}" | 
        jq --raw-output ".ChangeInfo.Id"
    )
aws route53 wait resource-record-sets-changed --id "${route53_record_change_id}"
