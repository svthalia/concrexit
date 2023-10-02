#! /bin/sh

# This script sets a server up to run concrexit, by installing Docker, creating
# users, and some filesystem setup. It should be run as root, and expects
# a domain (e.g. "staging.thalia.nu", used to set hostname) as an argument.
# For example: `sudo sh debian-install.sh staging.thalia.nu`
#
# If anything goes wrong, you'll have to fix it manually.

# Stop if anything fails.
set -e

# Check input.
DOMAIN=$1
if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain>"
    exit 1
fi

if [ $(id -u) -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Some functions used later.
export COLOR='\e[1;34m' # Bold blue.
export NO_COLOR='\e[0m'

step() {
    echo "\n$COLOR$1$NO_COLOR\n"
}

create_user() {
    username=$1
    ssh_key=$2

    # Create the user and add the SSH key.
    adduser --disabled-password --gecos "" $username
    adduser $username sudo
    mkdir /home/$username/.ssh
    echo "$ssh_key" > /home/$username/.ssh/authorized_keys
    chown -R $username:$username /home/$username/.ssh
    chmod 700 /home/$username/.ssh
    chmod 600 /home/$username/.ssh/authorized_keys

    # Allow the user to run sudo without a password.
    echo "$username ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$username
}

if [ -f .debian-install-started ]; then
    echo ".debian-install-started already exists, so this script has already run."
    exit 1
fi

touch .debian-install-started

# Set hostname.
step "Setting hostname ($DOMAIN)..."
hostnamectl set-hostname $DOMAIN
echo "preserve_hostname: true" | sudo tee -a /etc/cloud/cloud.cfg

# Set up a swapfile and some performance settings (https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-debian-11).
step "Setting up swapfile and performance settings..."
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
sysctl vm.swappiness=20
sysctl vm.vfs_cache_pressure=50

# Persist the swapfile and performance settings.
echo "/swapfile none swap sw 0 0" | tee -a /etc/fstab
echo vm.swappiness=20 | tee -a /etc/sysctl.conf
echo vm.vfs_cache_pressure=80 | tee -a /etc/sysctl.conf

# Set up the postgres volume (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-using-volumes.html).
step "Setting up postgres volume..."

# Format the volume if it's not already formatted as ext4.
if ! file -L -s /dev/sdf | grep ext4; then
    mkfs -t ext4 /dev/sdf
fi

# Mount the volume.
mkdir -p /volumes/postgres
mount /dev/sdf /volumes/postgres

# Persist the mount.
POSTGRES_VOL_UUID=$(blkid /dev/sdf -s UUID -o value)
echo "UUID=$POSTGRES_VOL_UUID /volumes/postgres ext4 defaults,nofail 0 2" | tee -a /etc/fstab

# Install rsync.
step "Installing rsync..."
apt-get update -q -y
apt-get install -y rsync

# Install Docker Engine (https://docs.docker.com/engine/install/debian/).
step "Installing Docker Engine..."
apt-get update -q -y
apt-get install -q -y \
    ca-certificates \
    curl \
    gnupg

mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -q -y

apt-get install -q -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker on boot (https://docs.docker.com/engine/install/linux-postinstall/).
step "Setting up Docker to start on boot..."
systemctl enable docker.service
systemctl enable containerd.service

# Set up deployment user. This user will be used by GitHub Actions to deploy.
step "Creating deployment user..."
create_user deploy "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOj2jPKZloJuWgVaZUKJ0n8J+Zpj34+GiPgNiX1N31hP"

# Create directory for concrexit.
step "Creating directory for concrexit..."
mkdir /var/lib/concrexit
chown -R deploy:deploy /var/lib/concrexit


# Set up users.
step "Creating users..."
create_user dirk "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIgMsOXBM1i1/GHoZIJpXQIm+dU5SRMat7HtZSKVrl5T"
create_user quinten "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII8GLsrAXmnzd7ps5BI12KG/sN4apUPGksVZq6n6jtY2 quinten@epsilon"
create_user ties "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIYxMh74Ocgn0l7I0rrWiQ4uTcWgYo6UX3WgNZWPpUXF tiesdirksen@gmail.com"

step "Done :)"
