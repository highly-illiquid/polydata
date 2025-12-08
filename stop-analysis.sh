#!/bin/bash
set -e
set -o pipefail

# --- Configuration ---
FETCHER_NAME="poly-fetcher"
ANALYZER_NAME="poly-analyzer"
VOLUME_NAME="poly-data-volume"

echo ">>> Tearing down analysis environment..."

# 0. Safety Check: Look for unsaved git changes
echo "--> Checking for unsaved work on ${ANALYZER_NAME}..."
# Check for uncommitted changes (porcelain gives clean output, empty if clean)
CHANGES=$(hcloud server ssh "${ANALYZER_NAME}" "cd /root/poly-data && git status --porcelain" 2>/dev/null || true)

if [ -n "$CHANGES" ]; then
  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  echo "CRITICAL ERROR: UNSAVED CHANGES DETECTED!"
  echo "Aborting shutdown to prevent data loss."
  echo ""
  echo "You have uncommitted files on the analyzer:"
  echo "$CHANGES"
  echo ""
  echo "ACTION REQUIRED: SSH in and push your changes to GitHub before stopping."
  echo "SSH Command: ssh -i ~/.ssh/my_vps_key root@$(hcloud server ip ${ANALYZER_NAME})"
  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  exit 1
fi

# 1. Delete the analyzer server
echo "--> Deleting ${ANALYZER_NAME}..."
hcloud server delete "${ANALYZER_NAME}"

# 2. Attach volume back to the fetcher
echo "--> Attaching ${VOLUME_NAME} to ${FETCHER_NAME}..."
# The volume is detached automatically when a server is deleted.
# We need to wait until the server is fully gone before attaching.
while [[ $(hcloud server describe "${ANALYZER_NAME}" 2>/dev/null) ]]; do
  echo "    Waiting for ${ANALYZER_NAME} to be deleted..."
  sleep 3
done
hcloud volume attach "${VOLUME_NAME}" --server "${FETCHER_NAME}"

# 3. Power on the fetcher server
echo "--> Powering on ${FETCHER_NAME}..."
hcloud server poweron "${FETCHER_NAME}"

echo ""
echo "-----------------------------------------------------"
echo ">>> Teardown complete. ${FETCHER_NAME} is running."
echo "-----------------------------------------------------"
