## How to deploy concrexit host config

Ssh to the server you want the new nixos config on. Run the following command:

```bash
sudo nixos-rebuild switch --flake 'github:svthalia/concrexit/<COMMIT>'
```

This sets up the host with the NixOS configuration you defined.

## How to deploy a new version of concrexit

```bash
sudo systemctl restart concrexit.service
```

On production, the `latest` docker tag always runs. This is the latest release,
see the `publish-container.yaml` GitHub Action to see how these are tagged.

On staging the `master` docker tag runs. This is the latest master build.

Currently it's not possible to run different tags in staging or production. This
can be changed in `concrexit-server.nix`.
