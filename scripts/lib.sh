
function hello() {
    echo "Hello, $(uname)!"
}

setfuncdoc "remote_ssh" "Wrapper around ssh to connect to new deployments, e.g. connect to host 'remote_ssh 192.xxx', run a command 'remote_ssh 192.xxx ls'"
function remote_ssh() {
    local host="$1"
    __funclog "Running command on remote (host:$host)..."
    shift

    # use two -t -t to force a pseudo-tty allocation
    ssh-agent bash -c "ssh-add $DEPLOY_SSH_KEY; ssh $SSH_USER@$host \"$*\"";
}

setfuncdoc "remote" "Run a local function or remote command on one or more servers through ssh in the given paths. e.g. remote hello somehost: otherhost:/path/to/test"
function remote() {
    __funclog "Remoting function..."
    DEPLOY_SSH_KEY="/root/hearo/hearo/creds/prod_creds"

    local do="$1"
    local do_params=$(echo $do)
    local do_first=${do_params%% *}

    shift
    local targets="$*"

    local target=""
    local target_host=""
    local target_path=""

    local lib=""

    # We use this instead of loading init because for some reason we can't load files using 'source'
    local loadfiles=("settings" "settings.local" "bash-colors" "helpers" "lib" "update" "main")
    for file in "${loadfiles[@]}"
    do
        for x in $(grep -o 'function [a-z1-9_]*' $LOCAL_PROJECT_ROOT/scripts/$file.sh | sed 's/function //')
        do
            func=$(declare -f $x)
            # enable the next line if there is an issue with a function not being declared
            # echo -e "declaring $func"
            if [[ -n $func ]]; then
                lib="$lib $func;"
            fi
        done
    done

    # We only read variables from the first target if its declared with P_
    local libarr=""
    readarray -d '' -t arr < <(declare -ax | grep 'declare -ax P_')
    readarray -t arr <<<"$arr"
    for x in "${arr[@]}"
    do
        if [[ -n $x ]]; then
            libarr="$libarr $x;"
        fi
    done

    local env="$(env | grep '^P_' | tr '\n' ' ')"

    local prepare="$lib $libarr export $env && cd $target_path"

    for target in $targets
    do
        target_host="${target%%:*}"
        target_path="${target/$target_host:/}"
        if [ "$target_path" == "$target_host" ]; then
            target_path="~"
        fi
        if [[ -n "$(declare -f $do_first)" ]]; then
            __log "Running $do on $target_host in $target_path"
            (ssh -oStrictHostKeyChecking=no $SSH_USER@$target_host "$prepare && $(declare -f $do_first) && set -x && cd $target_path && $do")
        else
            __log "Running $do on $target_host in $target_path"
            (ssh -oStrictHostKeyChecking=no $SSH_USER@$target_host "$prepare && set -x && cd $target_path && $do")
        fi
    done
    wait
    __success "Done!"
}

