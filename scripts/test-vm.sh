set -e

machine=$(./scripts/build-nix.sh vm)

# Remove the VM disk after this script finishes
trap 'rm --force staging.qcow2' EXIT

QEMU_NET_OPTS='hostfwd=tcp::8001-:80' $machine/bin/run-staging-vm -nographic
