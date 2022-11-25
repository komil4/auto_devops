#!/bin/bash

set -e
set -u

function create_user_and_database() {
	local database=$1
	local password=$2
	echo "  Creating user and database '$database' with password '$password'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE USER $database WITH SUPERUSER PASSWORD '$password';
	    CREATE DATABASE $database;
	    GRANT ALL PRIVILEGES ON DATABASE $database TO $database;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
	for data in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
	  i=0;
    for p in $(echo $data | tr ':' ' '); do
      declare var$i="$p"
      let i=$i+1
    done
		create_user_and_database $var0 $var1
	done
	echo "Multiple databases created"
fi