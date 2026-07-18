from dotenv import load_dotenv
from db_connector import DatabaseConnector
import pandas as pd

query = """
SELECT act.Oid, act.createdOn, act.Subject, act.Duration, proj.Name AS ProjectName, cli.Name AS ClientName, usr.UserName AS UserName, actTy.Name AS ActivityTypeName
FROM dbo.Activity act 
LEFT JOIN dbo.Client cli ON act.Client = cli.Oid 
LEFT JOIN dbo.[User] usr ON act.CreatedBy = usr.Oid 
LEFT JOIN dbo.ActivityType actTy ON act.ActivityType = actTy.Oid
LEFT JOIN dbo.Project proj ON act.Project = proj.Oid
WHERE
not actTy.Name = 'Urlaub' ORDER BY act.CreatedOn, act.Duration DESC;
"""



if __name__ == "__main__":
    load_dotenv()
    try:
        db = DatabaseConnector()
    except Exception as e:
        print(f"Error occurred: {e}")
    print(pd.DataFrame(db.execute_query(query))
    