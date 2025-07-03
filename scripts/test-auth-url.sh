#!/bin/bash

echo "Testing Backlog OAuth URL generation..."
echo ""

# Get authorization URL
response=$(curl -s "http://localhost/api/v1/auth/backlog/authorize")
auth_url=$(echo $response | jq -r '.authorization_url')
state=$(echo $response | jq -r '.state')

echo "Generated Authorization URL:"
echo $auth_url
echo ""
echo "State: $state"
echo ""

# Extract and decode redirect_uri
redirect_uri=$(echo $auth_url | grep -o 'redirect_uri=[^&]*' | cut -d= -f2)
decoded_uri=$(python3 -c "import urllib.parse; print(urllib.parse.unquote('$redirect_uri'))")

echo "Encoded redirect_uri: $redirect_uri"
echo "Decoded redirect_uri: $decoded_uri"
echo ""

# Test if the OAuth endpoint exists
echo "Testing Backlog OAuth endpoint..."
curl -I "https://nulab-exam.backlog.jp/OAuth2AccessRequest.action" 2>/dev/null | head -n 1