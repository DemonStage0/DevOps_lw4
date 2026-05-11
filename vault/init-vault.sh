#!/bin/sh
export VAULT_ADDR='http://vault:8200'
echo "Waiting for Vault API..." && until vault status > /dev/null 2>&1; do echo "  Still waiting..." && sleep 2; done
echo "Vault is ready. Logging in..." && vault login devops-lw3-root-token && echo "Writing secrets..." && vault kv put secret/db DB_HOST=db DB_PORT=5432 DB_USER=postgres DB_PASS=postgres DB_NAME=glass_db && echo "Vault secrets initialized successfully."