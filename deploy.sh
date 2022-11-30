#!/bin/bash
source scripts/init.sh

if [ "$1" == "production" ]; then
    remote pull $SWARM_LEADER $SWARM_FOLLOWERS
    remote "update_codebase $P_PROD_BRANCH" $SWARM_LEADER $SWARM_FOLLOWERS
    remote "enter django_app ./manage.py migrate --noinput" ${ARR_SWARM_FOLLOWERS[0]}
    remote deploy_prod $SWARM_LEADER
elif [ "$1" == "staging" ]; then
    remote pull $STAGING_IP
    remote "update_codebase $P_STAGE_BRANCH" $STAGING_IP
    remote "enter django_app ./manage.py migrate --noinput" $STAGING_IP
    remote deploy_staging $STAGING_IP
else
    __log "Specify staging or production"
fi
