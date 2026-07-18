from dotenv import load_dotenv
from db_connector import DatabaseConnector
import pandas as pd

from llm_interface import LLMInterface
from teams_handler import TeamsConnector





if __name__ == "__main__":
    load_dotenv()
    try:
        with DatabaseConnector() as db:
            res = db.execute_query()
    except Exception as e:
        print(f"Error occurred: {e}")
    res["Duration"] = res["Duration"].apply(lambda x: x / 3600 if pd.notnull(x) else 0)
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


    