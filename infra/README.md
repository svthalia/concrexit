## How to deploy concrexit using Terraform

The only dependency you need is Nix.
If you are running Nix OS you will already have Nix.
Otherwise install it using the [official installation instructions]

[official installation instructions]: https://nixos.org/download.html#nix-quick-install

Next, get your access token from AWS. 
You can find this in the IAM section.
Setup a `~/.aws/credentials` file like the so:

```ini
[thalia]
aws_access_key_id = ...
aws_secret_access_key = ........
```

The profile should be `thalia`. 

Enter the Nix develop shell using the following command, your working directory should be the repo root.

```bash
nix develop '.#deployment'
```

Change your directory either to the `infra/stages/staging` or `infra/stages/production` directory.

Run `terraform init` to initialize the needed Terraform plugins.

Now you can deploy with the command `terraform apply`. 
It may seem to hang for a while, this is because the Nix configuration is being built, and Terraform doesn't show these logs live.
If an error occurs with this part you will still see the logs.
