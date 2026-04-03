#!/bin/sh
export VAULT_ADDR='http://vault:8200'
export VAULT_TOKEN='myroot'

echo "⏳ Waiting for Vault to start..."
until vault status > /dev/null 2>&1; do
  sleep 1
done

echo "🚀 Configuring secrets..."
vault secrets enable -path=secret kv-v2 || true

# Используем переменные, которые передает docker-compose
vault kv put secret/oracle-db-creds \
    DB_USER="${DB_APP_USER}" \
    DB_PASSWORD="${DB_APP_PASSWORD}"

echo "✅ Vault initialization complete."