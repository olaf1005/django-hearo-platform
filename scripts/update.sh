setfuncdoc "update_codebase" "Update git repo to a (branch:$P_PROD_BRANCH)"
function update_codebase(){
    local branch=${1:-$P_PROD_BRANCH}
    shift
    __funclog "Update the codebase to $branch"
    cd_project_root
    add_deployment_keys
    git stash
    git checkout -f $branch
    git pull origin $branch
    git submodule update --init --recursive
}

setfuncdoc "install_codebase" "Install git codebase (branch:$P_PROD_BRANCH)"
function install_codebase(){
    local repo=$P_GIT_REPO
    local branch=${1:-$P_PROD_BRANCH}
    __funclog "Installing $repo@$branch to to remote root .."
    cd_remote_root
    add_deployment_keys
    git clone -b $branch git@$repo
    cd_project_root
    git submodule set-url hts git@gitlab.com:hearo/hts.git
    git submodule update --init --recursive
}

setfuncdoc "setup_server" "Setup hardend centos server with Docker"
function setup_server() {
    __funclog "Setting up server.."

    # When setting up the staging server you may also want to install postgresql-server
    # for a local database.

    local epel_release_latest=$(dnf -y install epel-release)
    if [[ $epel_release_latest == *"is already installed"* ]]; then
        echo "Your on the latest centos release"
    else
        dnf -y update
        __funclog "Rebooting after update"
        reboot
    fi

    dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo

    dnf install -y \
        redhat-lsb \
        docker-ce docker-ce-cli containerd.io \
        bash-completion \
        net-tools \
        bind-utils \
        man-pages \
        unzip \
        tmux \
        htop \
        git \
        postgresql \
        srm \
        tree \
        mosh \
        hstr \
        lnav \
        gcc \
        mlocate \
        gcc-c++

    hh --show-configuration >> ~/.bashrc

    service docker start

    systemctl enable docker.service
    systemctl start docker

    # should state experimental: true
    docker version

    # enable ip forwarding
    sysctl net.ipv4.ip_forward=1

    # setting required for elasticsearch
    sysctl -w vm.max_map_count=262144

    dnf install -y fail2ban rkhunter

    rkhunter --update
    rkhunter --propupd

    systemctl enable firewalld
    systemctl start firewalld

    # setup mosh
    echo '''<?xml version="1.0" encoding="utf-8"?>
<service>
  <short>MOSH</short>
  <description>Mosh (mosh.mit.edu) is a free replacement for SSH that allows roaming and supports intermittent connectivity.</description>
  <port protocol="udp" port="60001-60009"/>
</service>
''' > /etc/firewalld/services/mosh.xml
    firewall-cmd --zone=public --add-service=mosh --permanent

    # # Fix iptables and firewall + docker
    # # https://github.com/docker/docker/issues/16137
    # nmcli connection modify docker0 connection.zone trusted
    # systemctl stop NetworkManager.service
    # firewall-cmd --permanent --zone=trusted --change-interface=docker0
    # systemctl start NetworkManager.service
    # nmcli connection modify docker0 connection.zone trusted
    # systemctl restart docker.service

    # fix docker swarm ips
    # https://www.digitalocean.com/community/tutorials/how-to-configure-the-linux-firewall-for-docker-swarm-on-centos-7
    firewall-cmd --add-port=2376/tcp --permanent
    firewall-cmd --add-port=2377/tcp --permanent
    firewall-cmd --add-port=7946/tcp --permanent
    firewall-cmd --add-port=7946/udp --permanent
    firewall-cmd --add-port=4789/udp --permanent

    # open http ports
    firewall-cmd --zone=public --add-port=80/tcp --permanent
    firewall-cmd --zone=public --add-port=443/tcp --permanent

    firewall-cmd --reload

    # ctop
    wget https://github.com/bcicen/ctop/releases/download/v0.5/ctop-0.5-linux-amd64 -O /usr/local/bin/ctop
    chmod +x /usr/local/bin/ctop

    mkdir -p $P_REMOTE_ROOT

    ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts
    ssh-keyscan -t rsa gitlab.com >> ~/.ssh/known_hosts

    git config --global pull.rebase false

    install_codebase
}

function deploy_prod() {
    __log "Deploying.. ${P_DOCKER_PROD_STACK[*]}"
    cd_project_root
    # need to ensure env is preset
    load_env
    for app in "${P_DOCKER_PROD_STACK[@]}"
    do
       run $app
       sleep 10
    done
}

function deploy_staging() {
    __log "Deploying.. ${P_DOCKER_PROD_STACK[*]}"
    cd_project_root
    # need to ensure env is preset
    load_env
    for app in "${P_DOCKER_STAGING_STACK[@]}"
    do
       run $app
       sleep 10
    done
}
