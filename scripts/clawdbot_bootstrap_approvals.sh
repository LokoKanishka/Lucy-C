#!/bin/bash
# scripts/clawdbot_bootstrap_approvals.sh
# Set up a minimal allowlist for Clawdbot using the official CLI.

echo "Bootstrapping Clawdbot execution approvals..."

# Add wildcard allowlist for essential tools
clawdbot approvals allowlist add --agent "*" "/usr/bin/ls"
clawdbot approvals allowlist add --agent "*" "/usr/bin/pwd"
clawdbot approvals allowlist add --agent "*" "/usr/bin/uptime"

echo "Clawdbot approvals bootstrapped successfully."
echo "You can check them with: clawdbot approvals get"
