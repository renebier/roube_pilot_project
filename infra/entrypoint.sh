#!/bin/bash

# Start server detached
/opt/mssql/bin/sqlservr &

# Wait for readiness
echo "Starting readiness probes"
for i in {1..60}; do
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT 1" &> /dev/null
    if [ $? -eq 0 ]; then
        echo "Server is ready. Connecting ..."
        break
    fi
    sleep 2
done

# Execute restore
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P  "$MSSQL_SA_PASSWORD" -C -i /usr/config/restore.sql 

# Prevent container stopping
wait