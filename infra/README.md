# Infrastructure

We use AWS to host our infrastructure. Each environment (production, staging) runs on a
separate EC2 instance running Debian with Docker Compose. The AWS infrastructure can be
managed with Terraform.

## Terraform
To use Terraform, you need to have the AWS CLI installed (https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli), and have AWS IAM user credentials configured, with a `~/.aws/credentials` file that looks like this:

```
[thalia]
aws_access_key_id=***
aws_secret_access_key=*****
```

You can then run `terraform init` and `terraform apply` from `terraform/stages/<stage>`
to update the infrastructure according to your changes. Note that you should probably
know what this means before doing so.

The infrastructure consists of the following components:

- An EC2 instance, with an EBS volume for the database.
- An S3 bucket for storing media files.
- Cloudfront for serving the media files from S3.
- Some DNS records and virtual network stuff.

## Server

Once an EC2 instance with Debian is running, it needs to be configured to mount its
postgres EBS volume, have Docker installed, etc. `debian-install.sh` should do this,
or at least be a good starting point even if it breaks for some reason.

When you have a new EC2 instance, you can SSH into it, copy-paste the script into it,
and run it with `sudo sh debian-install.sh <stage>`. If everything works, that should
prepare the instance to be working server. At that point, a GitHub Actions workflow can
release to it, by writing some env files and running `docker compose up -d`.

`docker-compose.yaml` expects 3 things:
- An environment variable `TAG` that specifies the docker tag to run. This can be set in a `.env` file.
- A `env.public` file with the public environment variables needed for both `concrexit` and `nginx`.
  You can copy e.g. `env.public.staging` for this.
- A `env.secret` file with the secret environment variables needed for `concrexit`.
  You can fill in `env.secret.example` with the actual values.

## Deploying

Once a server is running properly, you can update it to a new release by simply updating
`docker-compose.yaml` and the env files, running `docker compose pull`, and then switching
to the newly pulled images with `docker compose up -d`. Afterwards, you may wish to clean
up old images and containers.

You can view which containers are running with `docker ps` and
you can view the logs of the containers with `docker compose logs -f`.
