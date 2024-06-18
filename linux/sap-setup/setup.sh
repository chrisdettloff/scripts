#!/bin/bash

# Function to print a message
print_message() {
    echo "===================="
    echo "$1"
    echo "===================="
}

# Function to read the configuration file
read_config() {
    local config_file=$1
    if [[ -f $config_file ]]; then
        source $config_file
    else
        echo "Configuration file $config_file not found!"
        exit 1
    fi
}

# Function to get the device path from volume ID
get_device_from_volume_id() {
    local volume_id=$1
    local device_path=$(readlink -f /dev/disk/by-id/$volume_id)
    echo $device_path
}

# Function to update /etc/sssd/sssd.conf
update_sssd_conf() {
    local ad_groups=("$@")
    local sssd_conf="/etc/sssd/sssd.conf"

    print_message "Updating /etc/sssd/sssd.conf..."

    # Ensure simple_allow_groups line is present
    if grep -q "^simple_allow_groups" $sssd_conf; then
        current_groups=$(grep "^simple_allow_groups" $sssd_conf | cut -d= -f2 | tr -d ' ')
        for group in "${ad_groups[@]}"; do
            if [[ ! $current_groups =~ $group ]]; then
                current_groups+=",${group}"
            fi
        done
        sudo sed -i "s/^simple_allow_groups.*/simple_allow_groups = ${current_groups}/" $sssd_conf
    else
        sudo bash -c "echo 'simple_allow_groups = ${ad_groups[*]// /,}' >> $sssd_conf"
    fi

    # Restart sssd service to apply changes
    sudo systemctl restart sssd
}

# Function to grant sudo access to AD groups
grant_sudo_access() {
    local ad_groups=("$@")
    local sudoers_dir="/etc/sudoers.d"

    print_message "Granting sudo access to AD groups..."

    for group in "${ad_groups[@]}"; do
        local sudoers_file="$sudoers_dir/cah-$group"
        if [[ ! -f $sudoers_file ]]; then
            echo "%$group ALL=(ALL) NOPASSWD:ALL" | sudo tee $sudoers_file
            # Set the correct permissions for the sudoers file
            sudo chmod 440 $sudoers_file
        fi
    done
}

# Main script execution starts here

# Read the configuration file
read_config $1

# Collect AD groups from the configuration file
ad_groups=("${ad_groups[@]}")

# Update /etc/sssd/sssd.conf
update_sssd_conf "${ad_groups[@]}"

# Grant sudo access to AD groups
grant_sudo_access "${ad_groups[@]}"

# Format and mount filesystems
print_message "Formatting and mounting filesystems..."
for fs in ${!filesystem_*}; do
    IFS=':' read -r volume_id mount_point <<< "${!fs}"
    device=$(get_device_from_volume_id $volume_id)
    if [[ -z $device ]]; then
        echo "Device for volume ID $volume_id not found!"
        continue
    fi
    echo "Formatting $device to xfs..."
    sudo mkfs.xfs $device
    
    # Get the UUID of the device
    uuid=$(sudo blkid -s UUID -o value $device)
    if [[ -z $uuid ]]; then
        echo "UUID for device $device not found!"
        continue
    fi

    echo "Mounting $device to $mount_point..."
    sudo mkdir -p $mount_point
    sudo mount $device $mount_point

    # Add to /etc/fstab if not already present
    if ! grep -q "$uuid" /etc/fstab; then
        echo "UUID=$uuid $mount_point xfs defaults 0 2" | sudo tee -a /etc/fstab
    fi
done

# Mount NFS shares
print_message "Mounting NFS shares..."
for nfs in ${!nfs_share_*}; do
    IFS=':' read -r server share_path mount_point <<< "${!nfs}"
    echo "Mounting $server:$share_path to $mount_point..."
    sudo mkdir -p $mount_point
    sudo mount -t nfs $server:$share_path $mount_point

    # Add to /etc/fstab if not already present
    if ! grep -q "$server:$share_path" /etc/fstab; then
        echo "$server:$share_path $mount_point nfs rw,hard,rsize=65536,wsize=65536,vers=3,tcp,defaults 0 0" | sudo tee -a /etc/fstab
    fi
done

# Create local users and groups
print_message "Creating local users and groups..."
for user in ${!user_*}; do
    IFS=':' read -r username groupname uid gid <<< "${!user}"
    echo "Creating group $groupname with GID $gid..."
    sudo groupadd -g $gid $groupname
    echo "Creating user $username with UID $uid and adding to group $groupname..."
    sudo useradd -m -u $uid -g $gid $username
    echo "Setting password for user $username..."
    MYPASS=$(</dev/urandom tr -dc_A-Z-a-z-0-9 | head -c${1:-32};echo;)
    echo -e "$MYPASS\n$MYPASS" | sudo passwd $username
done

# Configure file permissions
print_message "Configuring file permissions..."
for perm in ${!permission_*}; do
    IFS=':' read -r path owner group permissions <<< "${!perm}"
    echo "Setting ownership of $path to $owner:$group..."
    sudo chown -R $owner:$group $path
    echo "Setting permissions of $path to $permissions..."
    sudo chmod -R $permissions $path
done

print_message "Configuration complete!"
