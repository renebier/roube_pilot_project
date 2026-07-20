from dotenv import load_dotenv
from db_connector import DatabaseConnector
import pandas as pd

from llm_interface import LLMInterface
from teams_handler import TeamsConnector

QUERY = """
SELECT act.Oid, act.createdOn, act.Subject, (act.Duration / 3600) AS Duration, proj.Name AS ProjectName, cli.Name AS ClientName, usr.UserName AS UserName, actTy.Name AS ActivityTypeName
FROM dbo.Activity act 
LEFT JOIN dbo.Client cli ON act.Client = cli.Oid 
LEFT JOIN dbo.[User] usr ON act.CreatedBy = usr.Oid 
LEFT JOIN dbo.ActivityType actTy ON act.ActivityType = actTy.Oid
LEFT JOIN dbo.Project proj ON act.Project = proj.Oid
WHERE
actTy.Name != 'Urlaub' ORDER BY act.CreatedOn, act.Duration DESC;
"""



if __name__ == "__main__":
    load_dotenv()
    try:
        with DatabaseConnector() as db:
            res = db.execute_query(query=QUERY)
    except Exception as e:
        print(f"Error occurred: {e}")
    rows = res.to_dict(orient="records")
    try:
        with LLMInterface(model_name="qwen2.5:7b") as llmInterface:
            analysis_results = [llmInterface.analyze_row(row) for row in rows]
    except Exception as e:
        print(f"Error occurred during LLM analysis: {e}")
    failed_rows = [result for result in analysis_results if result.get("wrong")]
    try:
        with TeamsConnector() as teams:
            for row in failed_rows:
                reason = row.get("reason", "Keine Begründung verfügbar.")
                teams.send_anomaly_alert(row, reason)
    except Exception as e:
        print(f"Error occurred while sending alerts to Teams: {e}")


    