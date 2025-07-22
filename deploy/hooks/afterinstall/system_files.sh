#!/usr/bin/env bash
set -xeE

set -a
source /var/www/every_election/code/.env
METADATA_TOKEN=$(curl -X PUT "http://instance-data/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" --fail --silent)
INSTANCE_ID=$(curl "http://instance-data/latest/meta-data/instance-id" -H "X-aws-ec2-metadata-token: $METADATA_TOKEN" --fail --silent)
set +a

SYSTEMD_SRC="${PROJECT_ROOT}/code/deploy/files/systemd"
SYSTEMD_DST="/etc/systemd/system"
CONF_SRC="${PROJECT_ROOT}/code/deploy/files/conf"

# -------------
# Service files
# -------------
for service in "$SYSTEMD_SRC"/*.service; do
  service_name="$PROJECT_NAME"_$(basename "$service")
  # shellcheck disable=SC2016
  envsubst '$PROJECT_NAME' < "$service" > ${SYSTEMD_DST}/"$service_name"
done

# -------
# Scripts
# -------
for script in "$PROJECT_ROOT"/code/deploy/files/scripts/user_scripts/*; do
  script_name=$(basename "$script")
  # shellcheck disable=SC2016
  envsubst '$PROJECT_NAME' < "$script" > /usr/bin/"$script_name"
  chmod 755 /usr/bin/"$script_name"
done


# ------
# bashrc
# ------
echo 'cd && cd ../repo && source venv/bin/activate' > "$PROJECT_ROOT"/home/.bashrc

# --------------------
# replication log file
# --------------------
mkdir -p /var/log/db_replication && chmod 0777 /var/log/db_replication
touch /var/log/db_replication/logs.log && chmod 0777 /var/log/db_replication/logs.log
