export TERM=xterm-color

export SWARM_LEADER=""
export SWARM_FOLLOWERS=""
export ARR_SWARM_FOLLOWERS=( $SWARM_FOLLOWERS )
export STAGING_IP=""

export P_COMPANY_NAME=
export P_PROJECT_NAME=

export LOCAL_ROOT=$(dirname $PWD)
export LOCAL_PROJECT_ROOT=$LOCAL_ROOT/$P_PROJECT_NAME
export SSH_USER=root
export DEPLOY_SSH_KEY=$LOCAL_PROJECT_ROOT/creds/prod_creds

export P_REMOTE_ROOT=/root/$P_COMPANY_NAME
export P_REMOTE_PROJECT_ROOT=$P_REMOTE_ROOT/$P_PROJECT_NAME
export P_PROD_BRANCH=
export P_STAGE_BRANCH=
export P_GIT_REPO=gitlab.com/$P_COMPANY_NAME/$P_PROJECT_NAME.git
export P_GIT_RELEASE=$(git rev-parse --short HEAD)
export SRC_DIR="./"

# List of dirs required
export CREATE_DIRS=(
)

# This should only contain true secrets. Host names etc should be hard
# coded into the stack config since if a server is comprimised,
# changing one of these values could have a number of negative impacts
export SECRETS=(
    # "P_GITLAB_DEPLOY_TOKEN"
    # "P_GITLAB_DEPLOY_USER"
    # "PG_PASS"
    # "PG_DB_NAME"
    # "PG_DB_HOST"
    # "PG_DB_USER"
    # "PG_DB_PORT"
)

export P_DOCKER_PROD_STACK=(
)

export P_DOCKER_STAGING_STACK=(
)

export IMAGE_HTTPS="steveltn/https-portal:1.8.1"
export IMAGE_PGADMIN="fenglc/pgadmin4:latest"
export IMAGE_POSTGRES="postgres:11.5"
export IMAGE_SEMATEXT_AGENT="sematext/agent:latest"
export IMAGE_SEMATEXT_LOGAGENT="sematext/logagent:latest"

# Docker images to pull
export P_DOCKER_IMAGES=(
    $IMAGE_HTTPS
    $IMAGE_SEMATEXT_AGENT
    $IMAGE_SEMATEXT_LOGAGENT
    $IMAGE_PGADMIN
    $IMAGE_POSTGRES
)

export P_DOCKER_BUILD_IMAGES=(
    "app"
)
