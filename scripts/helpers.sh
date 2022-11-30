# This file provides helper functions for deployment and setup and should
# not generally be modified
# Some functions suppose the following folder structure
# /docker
# /docker/images  -> contains and images to be build and tagged
# /docker/stacks  -> contains docker compose stacks
# /docker/secrets -> contains all env parameters create using create_secrets

# Hashmap that contains all command docs
unset funcdocs
declare -A funcdocs

# Takes command name and description
# Use this before a function which wants to be a command
function setfuncdoc() {
    funcdocs[$1]=$2
}

setfuncdoc "help" "Shows help"
function help() {
    __h1 "Available commands for ${P_COMPANY_NAME}/${P_PROJECT_NAME}"
    if [ -z "$1" ]; then
        for key in "${!funcdocs[@]}"; do printf "$(c c)%-25s$(c) %s\n" "$key" "${funcdocs[$key]}"; done | sort
    else
        for key in "${!funcdocs[@]}"; do printf "$(c c)%-25s$(c) %s\n" "$key" "${funcdocs[$key]}" | grep -i $1; done | sort
    fi
}

function __h1() {
    echo -e "$(c B)$*$(c)"
}

function __log() {
    echo -e "$(c y)► $*$(c)"
}

function __error() {
    echo -e "$(c r)✘ $*$(c)"
}

function __warn() {
    echo -e "$(c c)ℹ $*$(c)"
}

function __success() {
    echo -e "$(c g)✔ $*$(c)"
}

# Output function description when calling a command
# If argument is passed, use that instead
function __funclog() {
    if [ -z "$1" ]; then
        __h1 "${funcdocs[${FUNCNAME[1]}]}"
    else
        __h1 $1
    fi
}

# Fix and harden ssh deployment key permissions
function fix_perms() {
    __funclog "Fixing and hardening permissions..."
    local kdir=$(dirname $DEPLOY_SSH_KEY)
    [[ -d "$kdir" ]] && chmod 700 $kdir
    [[ -f "$DEPLOY_SSH_KEY" ]] && chmod 600 $DEPLOY_SSH_KEY && chmod 644 $DEPLOY_SSH_KEY.pub
}

# Toggles the value of set -x
function toggle_set_x() {
    save=$-
    if [[ $save =~ x ]]; then
        set +x
    else
        set -x
    fi
}

function is_remote() {
    if [[ -d "$P_REMOTE_PROJECT_ROOT" ]]; then
        return $(true)
    else
        return $(false)
    fi
}

function cd_project_root() {
    if is_remote; then
        cd $P_REMOTE_PROJECT_ROOT
    else
        cd $LOCAL_PROJECT_ROOT
    fi
}

function cd_remote_root() {
    mkdir -p $P_REMOTE_ROOT
    cd $P_REMOTE_ROOT
}

function load_env() {
    __funclog "Loading environment..."
    if is_remote; then
        toggle_set_x
    fi
    cd_project_root
    mkdir -p docker/secrets && cd docker/secrets
    for secret in *; do
        echo $secret
        local pass=$(cat $secret)
        export "$secret"="$pass"
    done
    unameOut="$(uname -s)"
    case "${unameOut}" in
    Linux*) machine=Linux ;;
    Darwin*) machine=Mac ;;
    CYGWIN*) machine=Cygwin ;;
    MINGW*) machine=MinGw ;;
    *) machine="UNKNOWN:${unameOut}" ;;
    esac
    export MACHINE=$machine
    if [ $machine == "Mac" ]; then
        export DOCKERHOST="$(ifconfig en0 inet | grep "inet " | awk -F'[: ]+' '{ print $2 }')"
    else
        {
            export DOCKERHOST="$(ip -4 addr show eth0 | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | head -1)"
        } || {
            export DOCKERHOST="$(ip -4 addr show docker0 | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | head -1)"
        }
    fi
    echo "DOCKERHOST=$DOCKERHOST"
    cd_project_root
    if is_remote; then
        toggle_set_x
    fi
}

function mkdirs() {
    __funclog "Making required directories"
    for dir in "${CREATE_DIRS[@]}"; do
        mkdir -p $dir
        __success $dir
    done
}

function add_deployment_keys() {
    __log "Adding keys $DEPLOY_SSH_KEY"
    eval $(ssh-agent -s)
    if is_remote; then
        DEPLOY_SSH_KEY="/root/hearo/hearo/creds/prod_creds"
    fi
    ssh-add $DEPLOY_SSH_KEY
}

setfuncdoc "startup" "Load startup configuration"
function startup() {
    __funclog "Loading startup configuration"
    fix_perms
    load_env
    mkdirs
    __funclog "Adding deployment key"
    {
        add_deployment_keys
    } || {
        __error "Failed adding deployment keys"
    }
    printf "\nRun $(c y)help$(c) to view available commands\n"
}

setfuncdoc "sls" "Docker service list"
function sls() {
    __funclog
    docker service ls
}

setfuncdoc "wsls" "Watch Docker service list"
function wsls() {
    __funclog
    watch docker service ls
}

setfuncdoc "sps" "Docker service process list (app)"
function sps() {
    local app=$1
    __funclog "Service process list for $app"
    cd_project_root
    docker service ps --no-trunc $(docker service ls -q -f name=${P_PROJECT_NAME}_$app)
}

setfuncdoc "enter" "Enter Docker container (app) with (cmd:bash)..."
function enter() {
    local app=${1:-$DEFAULT_APP}
    local exec_params="-it"
    shift
    local cmd=${*:-bash}
    __funclog "Entering Docker container ($app) with (cmd:$cmd)..."
    cd_project_root
    {
        docker exec $exec_params $(docker ps | grep "${P_PROJECT_NAME}_$app\." | head -n 1 | awk '{print $1}') $cmd
    } ||
        {

            docker exec $exec_params $(docker ps | grep ${P_PROJECT_NAME} | grep $app | head -n 1 | awk '{print $1}') $cmd
        }
}

setfuncdoc "logs" "View logs for (service:app)"
function logs() {
    local service=${1:-$DEFAULT_APP}
    __funclog "Viewing logs for $service..."
    cd_project_root
    {
        docker service logs --raw -f $(docker service ls | grep "${P_PROJECT_NAME}_$service" | head -n 1 | awk '{print $1}')
    } ||
        {
            docker service logs --raw -f $(docker service ls | grep $P_PROJECT_NAME | grep $service | head -n 1 | awk '{print $1}')
        }
}

setfuncdoc "create_secrets" "Create secrets"
function create_secrets() {
    __funclog "Creating secrets..."
    cd_project_root
    mkdir -p docker/secrets/ssh/
    cd docker/secrets/
    for secret in "${SECRETS[@]}"; do
        settings=(${secret//:/ })
        if [ ! -f "${settings[0]}" ]; then
            if [ -n "${settings[1]}" ]; then
                read -p "Enter ${settings[0]} (default ${settings[1]}):" res
                res=${res:-${settings[1]}}
                if [ ! -z "$res" ]; then
                    echo $res >"${settings[0]}"
                fi
            else
                read -p "Enter ${settings[0]}:" res
                if [ ! -z "$res" ]; then
                    echo "$res" >"${settings[0]}"
                fi
            fi
        fi
    done
    load_env
}

setfuncdoc "update_secrets" "Update secrets (secrets..)"
function update_secrets() {
    __funclog "Updating secrets.. $*"
    for file in $*; do
        rm docker/secrets/$file
    done
    create_secrets
}

setfuncdoc "remove_unused_secrets" "Removing unused secrets..."
function remove_unused_secrets() {
    __funclog
    cd_project_root
    mkdir -p docker/secrets/ssh/
    cd docker/secrets/
    for filename in *; do
        if [[ ! " ${SECRETS[@]} " =~ " ${filename} " ]]; then
            rm -i $filename
        fi
    done
}

setfuncdoc "run" "Run stacks (stacks:app)..."
function run() {
    local stacks=${@:-$DEFAULT_APP}
    __funclog "Running stacks ($stacks)..."
    cd_project_root
    for app in $stacks; do
        docker stack deploy -c docker/stacks/$app.yml $P_PROJECT_NAME
    done
}

setfuncdoc "del" "Delete stacks (stacks)"
function del() {
    local stacks="$@"
    __funclog "Deleting (stacks:$stacks)..."
    cd_project_root
    for app in $stacks; do
        {
            # allow partial match
            docker service rm $(docker service ls -q -f name=${P_PROJECT_NAME}_${app})
        } ||
            {
                # allow full name variant
                docker service rm $(docker service ls -q -f name=${app})
            }
    done
}

setfuncdoc "pull" "Pull required Docker images"
function pull() {
    __funclog "Pulling Docker images..."
    docker login -u $P_GITLAB_DEPLOY_USER -p $P_GITLAB_DEPLOY_TOKEN registry.gitlab.com
    for image in "${P_DOCKER_IMAGES[@]}"; do
        __log $image
        docker pull $image
        # clear up any unused images and volumes to reduce disk space usage
        yes | docker image prune
    done
    __success "Done!"
}

setfuncdoc "build" "Build Docker image for (app:all)"
function build() {
    # We use buildx here because docker build has a problem with some build log
    # filesize limit and buildx appears more flexible (and faster)
    app=${1:-Dockerfile}
    file=${2:-Dockerfile}
    cd_project_root
    {
        if [ -z "$1" ]; then
            for stack in "${P_DOCKER_BUILD_IMAGES[@]}"; do
                build $stack
            done
        else
            if [ -d "${SRC_DIR}${app}" ]; then
                # build local app
                __log "Building $app..."
                cd "${SRC_DIR}${app}"
                docker buildx build . -f $file --progress plain --rm --output "type=docker,name=$P_COMPANY_NAME/${app}:latest"
            elif [ -d "./docker/images/$app" ]; then
                # build externally scurced app
                local image="./docker/images/$app"
                __log "Building $image..."
                cd $image
                docker buildx build . -f $file--rm --progress plain --output "type=docker,name=$P_COMPANY_NAME/${app}:latest"
            fi
        fi
    } || {
        __error "Build failed"
    }
    cd_project_root
}

setfuncdoc "remote_install_ssh_keys" "Install deployment keys to (hosts..), run directly as 'remote_install_ssh_keys 192.x 192.y'"
function remote_install_ssh_keys() {
    __funclog "Installing keys to $*.."
    eval $(ssh-agent -s)
    ssh-add $DEPLOY_SSH_KEY
    for target in "$@"; do
        ssh-copy-id $SSH_USER@$target
    done
    scp -r $DEPLOY_SSH_KEY $SSH_USER@$target:~/
}

setfuncdoc "remote_copy_secrets" "Copy secrets to (hosts..)"
function remote_copy_secrets() {
    __funclog "Copying secrets to hosts $*.."
    for target in "$@"; do
        rsync -av --progress $LOCAL_PROJECT_ROOT/docker/secrets/ $SSH_USER@$target:$P_REMOTE_PROJECT_ROOT/docker/secrets
    done
}

setfuncdoc "copy_to_remote" "Copy (file) to (hosts..)"
function copy_to_remote() {
    local file="$1"
    shift
    __funclog "Copying (file:$file) to servers $*"
    for target in "$@"; do
        rsync -av --progress $file $SSH_USER@$target:$P_REMOTE_PROJECT_ROOT/
    done
}

setfuncdoc "copy_from_remote" "Copy file from remote (path) (host) to current directory"
function copy_from_remote() {
    local path="$1"
    local host="$2"
    shift
    __funclog "Copying file $host:$path to current directory"
    rsync -av --progress $SSH_USER@$host:$path .
}

setfuncdoc "clear_gitlab_pipeline_history" "Delete pipeline history using (token) for (project)"
function clear_gitlab_pipeline_history() {
    local TOKEN="$1"
    local PROJECT="$2"
    for PIPELINE in $(curl --header "PRIVATE-TOKEN: $TOKEN" "https://gitlab.com/api/v4/projects/$PROJECT/jobs?per_page=100" | jq '.[].pipeline.id' | uniq); do
        echo "deleting $PIPELINE"
        curl --header "PRIVATE-TOKEN: $TOKEN" --request "DELETE" "https://gitlab.com/api/v4/projects/$PROJECT/pipelines/$PIPELINE"
    done
}

setfuncdoc "run_x" "Simply runs the command specified (x) times (command)"
function run_x() {
    number=$1
    shift
    for i in `seq $number`; do
      $@
    done
}
