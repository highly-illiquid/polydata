#!/bin/bash
set -e
set -o pipefail

# --- Configuration ---
FETCHER_NAME="poly-fetcher"
ANALYZER_NAME="poly-analyzer"
VOLUME_NAME="poly-data-volume"
SNAPSHOT_NAME="poly-analyzer-base-v1"
ANALYZER_TYPE="ccx33"
LOCATION="hel1"
SSH_KEY_NAME="my_vps_key"

echo ">>> Starting analysis environment..."

# 1. Power down fetcher to allow volume detachment
echo "--> Powering down ${FETCHER_NAME}..."
hcloud server poweroff "${FETCHER_NAME}"

# 2. Detach volume
echo "--> Detaching ${VOLUME_NAME}..."
# Wait for the server to be off before detaching
while [[ $(hcloud server describe "${FETCHER_NAME}" -o '{{.Status}}') != "off" ]]; do
  echo "    Waiting for ${FETCHER_NAME} to power off..."
  sleep 3
done
hcloud volume detach "${VOLUME_NAME}"

# 3. Create analyzer server from snapshot
echo "--> Creating ${ANALYZER_NAME} from snapshot..."
hcloud server create --name "${ANALYZER_NAME}" --snapshot "${SNAPSHOT_NAME}" --type "${ANALYZER_TYPE}" --location "${LOCATION}" --ssh-key "${SSH_KEY_NAME}"

# 4. Attach volume to analyzer
echo "--> Attaching ${VOLUME_NAME} to ${ANALYZER_NAME}..."
hcloud volume attach "${VOLUME_NAME}" --server "${ANALYZER_NAME}"

# 5. Mount the volume inside the analyzer
echo "--> Waiting for server to boot..."
sleep 15 # Give server time to boot before attempting SSH
echo "--> Mounting volume inside ${ANALYZER_NAME}..."
MOUNT_CMD="mkdir -p /mnt/poly-data && mount /dev/sda /mnt/poly-data && echo 'Volume mounted successfully.'"
hcloud server ssh "${ANALYZER_NAME}" "${MOUNT_CMD}"

# 6. Update the code repository
echo "--> Pulling latest code from GitHub..."
GIT_PULL_CMD="cd /root/poly-data && git pull"
hcloud server ssh "${ANALYZER_NAME}" "${GIT_PULL_CMD}"

# 7. Get IP and provide instructions
ANALYZER_IP=$(hcloud server ip "${ANALYZER_NAME}")
echo ""
echo "-----------------------------------------------------"
echo ">>> Analysis environment is READY."
echo ">>> IP Address: ${ANALYZER_IP}"
echo ">>> SSH command:"
echo "ssh -i ~/.ssh/my_vps_key root@${ANALYZER_IP}"
echo "-----------------------------------------------------"
