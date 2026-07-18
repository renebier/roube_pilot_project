IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'VenDocDemo')
BEGIN
    RESTORE DATABASE [VenDocDemo]
    FROM DISK = '/var/opt/mssql/backup/database.bak'
    WITH MOVE 'VenDocDemo' TO '/var/opt/mssql/data/VenDocDemo.mdf',
         MOVE 'VenDocDemo_log' TO '/var/opt/mssql/data/VenDocDemo_log.ldf',
    REPLACE;
    PRINT 'VenDocDemo successfully restored and created!';
END
ELSE
BEGIN
    PRINT 'Database exists already, skipping restore';
END
GO