#!/bin/bash

############################################################################
# Container Entrypoint script
############################################################################

# Configure Git for the container
echo "Configuring Git for Docker environment..."
GIT_USER_NAME=${GIT_USER_NAME:-admin-gulpanzer}
GIT_USER_EMAIL=${GIT_USER_EMAIL:-admin@gulpanzer.xyz}
git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"
echo "Git configured with user: $GIT_USER_NAME <$GIT_USER_EMAIL>"

if [[ "$PRINT_ENV_ON_LOAD" = true || "$PRINT_ENV_ON_LOAD" = True ]]; then
  echo "=================================================="
  printenv
  echo "=================================================="
fi

if [[ "$WAIT_FOR_DB" = true || "$WAIT_FOR_DB" = True ]]; then
  dockerize \
    -wait tcp://$DB_HOST:$DB_PORT \
    -timeout 300s
fi

############################################################################
# Start App
############################################################################

case "$1" in
  chill)
    ;;
  *)
    echo "Running: $@"
    exec "$@"
    ;;
esac

echo ">>> Hello World!"
while true; do sleep 18000; done
