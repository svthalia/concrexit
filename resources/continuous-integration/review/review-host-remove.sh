#!/usr/bin/env bash

set -o errexit -o verbose 

if [ -z "${GITLAB_CI}" ]; then
    echo "Not running in Gitlab CI"
    exit 1;
fi

mapfile -t running_instance_ids < <(
    aws ec2 describe-instances  \
    --filters "Name=tag:Name,Values=concrexit-review-${CI_COMMIT_REF_SLUG}" \
              "Name=instance-state-name,Values=running,shutting-down,stopping,stopped" \
    --query "Reservations[].Instances[].[InstanceId]" \
    --output "text" 
)
if [ "${#running_instance_ids[@]}" -gt 0 ]; then
    aws ec2 terminate-instances --instance-ids "${running_instance_ids[@]}"
fi

resource_record_set=$(
    aws route53 list-resource-record-sets \
    --hosted-zone-id "Z3I4ZHBBD5NSHU" \
    --query "ResourceRecordSets[?Name == '${CI_COMMIT_REF_SLUG}.private.review.technicie.nl.']" |
        jq --raw-output ".[0]"
    ) 

if [ "${resource_record_set}" != "null" ]; then
    temporary_record_change_file=$(mktemp --suffix ".json") 
    cat > "${temporary_record_change_file}" <<EOF
{
  "Comment": "Delete private review host record",
  "Changes":  [
        {
            "Action": "DELETE",
            "ResourceRecordSet": ${resource_record_set}
        }
    ]
}
EOF
    aws route53 change-resource-record-sets --hosted-zone-id "Z3I4ZHBBD5NSHU" --change-batch "file://${temporary_record_change_file}"
fi
