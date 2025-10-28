#!/bin/bash
#
# A script to automatically start a remote Jupyter Lab server,
# create an SSH tunnel, and open it in the local browser.
#

# --- Configuration ---
# !!! IMPORTANT: EDIT THESE VARIABLES !!!
REMOTE_USER="user"
REMOTE_HOST="your_vps_address"
KEY_PATH="~/.ssh/id_ed25519"
# --- End of Configuration ---

REMOTE_PROJECT_DIR="~/poly-data"
LOCAL_PORT="8888"
REMOTE_PORT="8889"


echo "🚀 Starting/finding Jupyter Lab on remote server..."

# Command to start Jupyter Lab on the remote server in the background if not already running.
REMOTE_CMD="cd ${REMOTE_PROJECT_DIR} && source .venv/bin/activate && nohup jupyter lab --no-browser --port=${REMOTE_PORT} --allow-root > /dev/null 2>&1 &"
ssh -i "${KEY_PATH}" "${REMOTE_USER}@${REMOTE_HOST}" "${REMOTE_CMD}"
echo "Waiting a moment for server to be ready..."
sleep 3 # Give the server a few seconds to start

echo "🔎 Fetching connection token..."
# Use 'jupyter-server list' to get the URL with the token. This is the most reliable method.
SERVER_INFO=$(ssh -i "${KEY_PATH}" "${REMOTE_USER}@${REMOTE_HOST}" "source ${REMOTE_PROJECT_DIR}/.venv/bin/activate && jupyter-server list | grep ':${REMOTE_PORT}/'")

if [ -z "$SERVER_INFO" ]; then
    echo "❌ Could not find a running Jupyter server on port ${REMOTE_PORT}."
    echo "Please try starting it manually on the server and try this script again."
    exit 1
fi

# Extract the full URL (first field in the output)
REMOTE_URL=$(echo "$SERVER_INFO" | awk 
'{print $1}')
# Extract just the token from the URL
TOKEN=$(echo "$REMOTE_URL" | sed 
's/.*token=//')

echo "✅ Token found!"

# Construct the final URL for the local browser. Jupyter Lab uses /lab in the path.
FINAL_URL="http://localhost:${LOCAL_PORT}/lab?token=${TOKEN}"

# Check if the tunnel is already running to avoid creating duplicates
# The [s]sh is a trick to prevent grep from matching its own process
if ps aux | grep "[s]sh -i ${KEY_PATH} -f -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT}" > /dev/null; then
    echo "🚇 SSH tunnel already running."
else
    echo "🚇 Setting up SSH tunnel in the background..."
    ssh -i "${KEY_PATH}" -f -N -L "${LOCAL_PORT}:localhost:${REMOTE_PORT}" "${REMOTE_USER}@${REMOTE_HOST}"
fi

echo "🎉 All set! Opening Jupyter Lab in your browser..."
echo "If it doesn't open automatically, please copy and paste this URL:"
echo "${FINAL_URL}"

# Open the URL in the default browser
case "$(uname -s)" in
   Darwin)
     open "${FINAL_URL}"
     ;;
   Linux)
     xdg-open "${FINAL_URL}"
     ;;
   *)
     echo "Unsupported OS. Please open the URL manually."
     ;;
esac

echo ""
echo "---"
echo "🧹 When you are finished:"
echo "To stop the background SSH tunnel, run: kill $(ps aux | grep '[s]sh -i ${KEY_PATH} -f -N -L' | awk '{print $2}')"
echo "To stop the remote Jupyter server, run: ssh -i \"${KEY_PATH}\" \"${REMOTE_USER}@${REMOTE_HOST}\" \"pkill -f jupyter-lab\""
