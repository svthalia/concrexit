#! /bin/sh

# This script installs docker on a Debian system.

# Install Docker Engine (https://docs.docker.com/engine/install/debian/).
sudo apt-get update -q -y
sudo apt-get install -q -y \
    ca-certificates \
    curl \
    gnupg

sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -q -y

sudo apt-get install -q -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker on boot (https://docs.docker.com/engine/install/linux-postinstall/).
sudo systemctl enable docker.service
sudo systemctl enable containerd.service

# Set up a swapfile and some performance settings (https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-debian-11).
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo sysctl vm.swappiness=20
sudo sysctl vm.vfs_cache_pressure=50

# Persist the swapfile and performance settings.
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
echo vm.swappiness=20 | sudo tee -a /etc/sysctl.conf
echo vm.vfs_cache_pressure=80 | sudo tee -a /etc/sysctl.conf

# Set up users.
create_user() {
    username=$1
    ssh_key=$2

    # Create the user and add the SSH key.
    sudo adduser --disabled-password --gecos "" $username
    sudo $username sudo
    sudo mkdir /home/$username/.ssh
    sudo echo "$ssh_key" > /home/$username/.ssh/authorized_keys
    sudo chown -R $username:$username /home/$username/.ssh
    sudo chmod 700 /home/$username/.ssh
    sudo chmod 600 /home/$username/.ssh/authorized_keys

    # Allow the user to run sudo without a password.
    sudo echo "$username ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$username
}

create_user dirk "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIgMsOXBM1i1/GHoZIJpXQIm+dU5SRMat7HtZSKVrl5T"
create_user job "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJylC3OVDYt+JqJv1LStZpogMv04lr2XRW4yfddAT5JR MacBook-Pro-van-Job"
create_user quinten "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII8GLsrAXmnzd7ps5BI12KG/sN4apUPGksVZq6n6jtY2 quinten@epsilon"

# Setup directory for concrexit.
sudo mkdir /var/lib/concrexit
