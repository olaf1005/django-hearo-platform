setfuncdoc "pg_enter" "Enter pgsql on (dbname:$PG_DB_NAME) (host:$PG_DB_HOST) (dbuser:$PG_DB_USER) (query}"
function pg_enter() {
    local database=${1:-$PG_DB_NAME}
    local host=${2:-$PG_DB_HOST}
    local user=${3:-$PG_DB_USER}
    local query=$4
    __funclog "Entering postgres (database:$database) (host:$host) (user:$user) (query:$query)"
    cd_project_root
    local dbcontainer="$(docker ps | grep "${P_PROJECT_NAME}_$host\." | awk '{print $1}')"
    if [ -z "$query" ]; then
        docker exec -it $dbcontainer psql -U $user $database
    else
        docker exec -it $dbcontainer psql -U $user -c "$query" $database
    fi
}

setfuncdoc "pg_kill_connections" "Kill postgres connections to (database:$PG_DB_NAME) (host:$PG_DB_HOST) with (user:$PG_DB_USER)"
function pg_kill_connections() {
    local database=${1:-$PG_DB_NAME}
    local host=${2:-$PG_DB_HOST}
    local user=${3:-$PG_DB_USER}
    __funclog "Killing postgres connections to (database:$database) (host:$host) (user:$user)"
    cd_project_root
    docker exec $(docker ps | grep "${P_PROJECT_NAME}_$host\." | awk '{print $1}') psql -U $user $database -c "
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE datname = current_database()
    AND pid <> pg_backend_pid();"
}

setfuncdoc "pg_backup" "Backup dbs to (tag:snap) from (database:$PG_DB_NAME) on (host:$PG_DB_HOST) (user:$PG_DB_USER) (pass:*****)"
function pg_backup() {
    local tag=${1:-snap}
    local database=${2:-$PG_DB_NAME}
    local host=${3:-$PG_DB_HOST}
    local user=${4:-$PG_DB_USER}
    local port=${5:-$PG_DB_PORT}
    local pass=${5:-$PG_PASS}
    __funclog "Backing up database from (database:$database) (tag:$tag) (host:$host) (user:$user) (port:$port) (pass:****)"
    [[ "$1" == "-h" ]] && return
    cd_project_root
    local filename="dump_${host}_${database}_$(date +%d-%m-%Y"_"%H_%M_%S)_${tag}.bak"
    local dbcontainer="$(docker ps | grep "${P_PROJECT_NAME}_${host}\." | awk '{print $1}')"
    {
        docker exec $dbcontainer pg_dump -U $user -Fc -f $filename $database
        docker cp $dbcontainer:/$filename .
        docker exec $dbcontainer rm -f $filename
    } || {
        __log "Using a hosted service? Attempting using pg_dump without docker..."
        PGPASSWORD=$pass pg_dump -h $host -U $user -p $port -Fc -f $filename $database
    }
    __success "Download using 'rsync -av --progress $SSH_USER@$DOCKERHOST:$LOCAL_PROJECT_ROOT/$filename .'"
}


setfuncdoc "pg_backup_table" "Backup table from (table) (database:$PG_DB_NAME) (host:$PG_DB_HOST) with (user:$PG_DB_USER)"
function pg_backup_table() {
    local table=$1
    local database=${2:-$PG_DB_NAME}
    local host=${3:-$PG_DB_HOST}
    local user=${4:-$PG_DB_USER}
    __funclog "Backing up table from (table:$table) (database:$database) (host:$host) with (user:$user)"
    cd_project_root
    filename="dump_${host}_${database}_table_${table}_$(date +%d-%m-%Y"_"%H_%M_%S).sql"
    local dbcontainer=$(docker ps | grep "${P_PROJECT_NAME}_${1}\." | awk '{print $1}')
    docker exec $dbcontainer pg_dump --column-inserts --data-only --table $table -U $user $database > $filename
    tar czf $filename.tar.gz $filename
    rm -f $filename
}

setfuncdoc "pg_backup_table_to_csv" "Backing up table to csv from (table) (database:$PG_DB_NAME) (host:$PG_DB_HOST) with (user:$PG_DB_USER)"
function pg_backup_table_to_csv() {
    local table=$1
    local database=${2:-$PG_DB_NAME}
    local host=${3:-$PG_DB_HOST}
    local user=${4:-$PG_DB_USER}
    __funclog "Backing up table to csv from (table:$table) (database:$database) (host:$host) with (user:$user)"
    cd_project_root
    local filename="dump_${host}_${database}_${table}_$(date +%d-%m-%Y"_"%H_%M_%S).csv"
    local dbcontainer=$(docker ps | grep "${P_PROJECT_NAME}_$host\." | awk '{print $1}')
    docker exec $dbcontainer psql -U $user $database -c "COPY (select * from $table) TO STDOUT WITH CSV HEADER" > $filename
    tar czf $filename.tar.gz $filename
    rm -f $filename
}

setfuncdoc "pg_vacuum" "Vacuuming (database:$PG_DB_NAME) on (host:$PG_DB_HOST) with (user:$PG_DB_USER)"
function pg_vacuum() {
    local database=${1:-$PG_DB_NAME}
    local host=${2:-$PG_DB_HOST}
    local user=${3:-$PG_DB_USER}
    __funclog "Vacuuming (database:$database) on (host:$host) with (user:$user)"
    cd_project_root
    local dbcontainer=$(docker ps | grep "${P_PROJECT_NAME}_$host\." | awk '{print $1}')
    docker exec $dbcontainer vacuumdb -U $user $database
}

setfuncdoc "pg_restore" "Restoring to (file:file) on (database:$PG_DB_NAME) (host:$PG_DB_HOST) with (user:$PG_DB_USER)"
function pg_restore() {
    local file=$1
    local database=${2:-$PG_DB_NAME}
    local host=${3:-$PG_DB_HOST}
    local user=${4:-$PG_DB_USER}
    __funclog "Restoring to (database:$database) (file:$file) on (host:$host) with (user:$user)"
    cd_project_root
    local dbcontainer="$(docker ps | grep "${P_PROJECT_NAME}_$host\." | awk '{print $1}')"
    docker cp $file $dbcontainer:/
    __log "..dropping and recreating $database"
    docker exec $dbcontainer dropdb -U $user $database
    docker exec $dbcontainer createdb -U $user $database
    # pg_enter $database $host $user "create extension timescaledb;"
    # pg_enter $database $host $user "alter database $database set timescaledb.restoring='on';"
    if [ ${file: -4} == ".sql" ]; then
        docker exec $dbcontainer psql -U $user -d $database -f $file
    elif [ ${file: -4} == ".bak" ]; then
        docker exec $dbcontainer pg_restore -U $user -Fc -d $database $file
    fi
    # pg_enter $database $host $user "alter database $database set timescaledb.restoring='off';"
    docker exec $dbcontainer rm -f $file
    pg_vacuum $database
}

setfuncdoc "mysql_enter" "Enter mysql on (dbname:$MYSQL_DB_NAME) (host:$MYSQL_DB_HOST) (dbuser:$MYSQL_DB_USER) (query:$4}"
function mysql_enter() {
    local database=${1:-$MYSQL_DB_NAME}
    local host=${2:-$MYSQL_DB_HOST}
    local user=${3:-$MYSQL_DB_USER}
    local query=$4
    __funclog "Entering mysql (database:$database) (host:$host) (user:$user) (query:$query)"
    cd_project_root
    local dbcontainer="$(docker ps | grep "${P_PROJECT_NAME}_$host\." | awk '{print $1}')"
    if [ -z "$query" ]; then
        docker exec -it $dbcontainer mysql -u $user -p $database
    else
        docker exec -it $dbcontainer mysql -u $user -p $database -e "$query"
    fi
}

setfuncdoc "mysql_kill_connections" "Kill mysql connections to (database:$MYSQL_DB_NAME) (host:$MYSQL_DB_HOST) with (user:$MYSQL_DB_USER)"
function mysql_kill_connections() {
    local database=${1:-$MYSQL_DB_NAME}
    local host=${2:-$MYSQL_DB_HOST}
    local user=${3:-$MYSQL_DB_USER}
    __funclog "Killing mysql connections to (database:$database) (host:$host) (user:$user)"
    cd_project_root
    docker exec $(docker ps | grep "${P_PROJECT_NAME}_$host\." | awk '{print $1}') mysql -u $user -p $database -c "
    SELECT
    CONCAT('KILL ', id, ';')
    FROM INFORMATION_SCHEMA.PROCESSLIST
    WHERE `db` = '$database';"
}

setfuncdoc "mysql_backup" "Backup dbs to (tag:snap) from (database:$MYSQL_DB_NAME) on (host:$MYSQL_DB_HOST) (user:$MYSQL_DB_USER)"
function mysql_backup() {
    local tag=${1:-snap}
    local database=${2:-$MYSQL_DB_NAME}
    local host=${3:-$MYSQL_DB_HOST}
    local user=${4:-$MYSQL_DB_USER}
    __funclog "Backing up database from (database:$database) (tag:$tag) (host:$host) (user:$user)"
    [[ "$1" == "-h" ]] && return
    cd_project_root
    local filename="dump_${host}_${database}_$(date +%d-%m-%Y"_"%H_%M_%S)_${tag}.bak"
    local dbcontainer="$(docker ps | grep "${P_PROJECT_NAME}_${host}\." | awk '{print $1}')"
    docker exec $dbcontainer mysqldump -u $user -p $database > $filename
    docker cp $dbcontainer:/$filename .
    docker exec $dbcontainer rm -f $filename
    echo "Done! Download using 'rsync -av --progress $SSH_USER@$DOCKERHOST:$LOCAL_PROJECT_ROOT/$filename .'"
}

setfuncdoc "mysql_restore" "Restoring to (file:file) on (database:$MYSQL_DB_NAME) (host:$MYSQL_DB_HOST) with (user:$MYSQL_DB_USER)"
function mysql_restore() {
    local file=$1
    local database=${2:-$MYSQL_DB_NAME}
    local host=${3:-$MYSQL_DB_HOST}
    local user=${4:-$MYSQL_DB_USER}
    __funclog "Restoring to (database:$database) (file:$file) on (host:$host) with (user:$user)"
    cd_project_root
    local dbcontainer="$(docker ps | grep "${P_PROJECT_NAME}_$host\." | awk '{print $1}')"
    docker cp $file $dbcontainer:/
    # docker exec $dbcontainer mysql -u $user $database < $file
    # docker exec $dbcontainer rm -f $file
}

