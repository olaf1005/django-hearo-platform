# NOTE: We only read variables from the first target if its declared with P_
export TERM=xterm-color

export P_COMPANY_NAME=hearo
export P_PROJECT_NAME=hearo
export P_REMOTE_ROOT=/root/$P_COMPANY_NAME
export P_REMOTE_PROJECT_ROOT=$P_REMOTE_ROOT/$P_PROJECT_NAME
export P_PROD_BRANCH="production"
export P_STAGE_BRANCH="staging-andrew"
export P_GIT_REPO=gitlab.com:hearo/hearo.git
export P_GIT_RELEASE=$(git rev-parse --short HEAD)

export SWARM_LEADER="167.172.253.169"
export SWARM_FOLLOWERS=""
export ARR_SWARM_FOLLOWERS=( $SWARM_FOLLOWERS )
export STAGING_IP="104.131.94.200"
export SSH_USER=root

export DEPLOY_SSH_KEY=$LOCAL_PROJECT_ROOT/creds/prod_creds

export LOCAL_ROOT=$(dirname $PWD)
export LOCAL_PROJECT_ROOT=$LOCAL_ROOT/$P_PROJECT_NAME

export SRC_DIR="./"
export DEFAULT_APP=django_app

# List of dirs required
export CREATE_DIRS=(
    "../media"
    "../mixingbowl"
    "../static"
)

# This should only contain true secrets. Host names etc should be hard
# coded into the stack config since if a server is comprimised,
# changing one of these values could have a number of negative impacts
export SECRETS=(
    "SECRET_KEY"
    "EMAIL_HOST_PASSWORD"
    "EMAIL_HOST_USER"
    "EMAIL_HOST"
    "CLOUDFILES_USERNAME"
    "CLOUDFILES_PASSWORD"
    "CLOUDFILES_REGION"
    "PG_PASS"
    "PG_DB_NAME"
    "PG_DB_HOST"
    "PG_DB_USER"
    "PG_DB_PORT"
    "ELASTICSEARCH_HOST"
    "GOOGLE_MAPS_GEOCODING_API_KEY"
    "YOUTUBE_DATA_API_KEY"
    "S3_SECRET_KEY"
    "S3_ACCESS_KEY"
    "SSH_PRIVATE_KEY"
    "DJANGO_SETTINGS_MODULE"
    "SENDGRID_EMAIL_VALIDATION_API_KEY"
    "QUICKEMAILVERIFICATION_API_KEY"
    # "STRIPE_SECRET"
    # "STRIPE_KEY"
)

export P_DOCKER_PROD_STACK=(
    "dbs_prod"
    "django_app_prod"
    "hts_prod"
    "https_prod"
    "logging"
)

export P_DOCKER_STAGING_STACK=(
    "dbs"
    "django_app_staging"
    "hts"
    "logging"
)

export IMAGE_HTTPS="steveltn/https-portal:1.8.1"
export IMAGE_PGADMIN="fenglc/pgadmin4:latest"
export IMAGE_POSTGRES="postgres:11.5"
export IMAGE_RETHINKDB="rethinkdb:2.4.0"
export IMAGE_MEMCACHED="memcached:1.5"
export IMAGE_ELASTICSEARCH="elasticsearch:2.4.3-alpine"
export IMAGE_DJANGO_APP="registry.gitlab.com/${P_COMPANY_NAME}/${P_PROJECT_NAME}/django_app:latest"
export IMAGE_DJANGO_APP_DEV="registry.gitlab.com/${P_COMPANY_NAME}/${P_PROJECT_NAME}/django_app:dev"
export IMAGE_HTS="registry.gitlab.com/${P_COMPANY_NAME}/${P_PROJECT_NAME}/hts:latest"
export IMAGE_SEMATEXT_AGENT="sematext/agent:latest"
export IMAGE_SEMATEXT_LOGAGENT="sematext/logagent:latest"

# Docker images to pull
export P_DOCKER_IMAGES=(
    # https
    $IMAGE_HTTPS
    # logging
    $IMAGE_SEMATEXT_AGENT
    $IMAGE_SEMATEXT_LOGAGENT
    # dbs
    $IMAGE_RETHINKDB
    $IMAGE_MEMCACHED
    $IMAGE_ELASTICSEARCH
    $IMAGE_PGADMIN
    $IMAGE_POSTGRES
    # hearo
    $IMAGE_DJANGO_APP
    $IMAGE_HTS
)

export P_DOCKER_BUILD_IMAGES=(
    "django_app"
    "hts"
)
