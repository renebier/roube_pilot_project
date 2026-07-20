import time
from typing import Any, Dict, List, Optional
import pandas as pd
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate


class LLMBenchmarker:
    """Benchmarks local Ollama LLMs on structured time-tracking data for JSON compliance, latency, and anomaly detection performance."""
    SYSTEM_PROMPT = """Du bist ein automatisierter Prüf-Agent für Lohnbuchhaltung und HR-Compliance. Deine Aufgabe ist es, Zeiterfassungsdaten aus einem ERP-System auf Anomalien, Fehler und Unplausibilitäten zu untersuchen.

    Analysiere jede übergebene Buchung streng nach folgenden Kriterien:
    1. Abgleich von Tätigkeit und Zeitaufwand: Ist die erfasste Dauer für die spezifische Bezeichnung der Tätigkeit plausibel? (z.B. 8 Stunden für 'Kurze Kaffeepause' oder 'Tägliches Sync-Meeting' sind hochgradig unplausibel. Ebenso 5 Minuten für 'Komplette Neuentwicklung Modul X').
    2. Arbeitszeit-Überschreitungen: Tägliche Arbeitszeiten über 10 Stunden verstoßen gegen das Gesetz und sind als kritisch einzustufen.
    3. Unplausible Werte: Buchungen mit 0 Stunden, negativen Werten oder extrem utopischen Stundenzahlen.

    Ausgabe-Format:
    Antworte AUSSCHLIESSLICH in einem gültigen JSON-Format. Füge keinen Smalltalk, keine Einleitung und keine Markdown-Formatierung (wie ```json) hinzu. Das JSON muss exakt diese Struktur haben:
    {{"reason": "Hier steht die kurze Begründung auf Deutsch", "wrong": true}}

    Falls die Buchung vollkommen plausibel, fehlerfrei und unauffällig ist, antworte exakt so:
    {{"reason": "Keine Auffälligkeiten erkannt.", "wrong": false}}

    Beispiele für deine Ausgabe:
    Beispiel 1 (Fehler gefunden): {{"reason": "Ein Zeitaufwand von 7.5 Stunden für ein wöchentliches Abstimmungsmeeting ist unplausibel.", "wrong": true}}
    Beispiel 2 (Kein Fehler): {{"reason": "Keine Auffälligkeiten erkannt.", "wrong": false}}"""

    def __init__(self, models: Optional[List[str]] = None):
        self.models = models or ["qwen2.5:7b", "llama3.1:8b", "qwen2.5:3b"]
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.SYSTEM_PROMPT),
                (
                    "user",
                    (
                        "Prüfe diese Buchung:\n"
                        "- ID: {Oid}\n"
                        "- Mitarbeiter: {UserName}\n"
                        "- Datum: {createdOn}\n"
                        "- Kunde: {ClientName}\n"
                        "- Auftrag: {ProjectName}\n"
                        "- Typ: {ActivityTypeName}\n"
                        "- Beschreibung: {Subject}\n"
                        "- Stunden: {Duration}\n"
                    ),
                )
            ]
        )

    def _benchmark_single_model(
        self, model_name: str, records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Executes execution loop for a specific model and collects runtime metrics."""
        llm = ChatOllama(model=model_name, temperature=0.0)
        chain = self.prompt | llm | self.parser

        valid_json_count = 0
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        true_negatives = 0
        total_duration = 0.0
        total_records = len(records)

        print(
            f"Evaluating model '{model_name}' on {total_records} records..."
        )

        for record in records:
            # Ensure timestamps are string-serializable for the prompt
            input_data = record.copy()
            result_list = list()
            if input_data.get("createdOn"):
                input_data["createdOn"] = str(input_data["createdOn"])

            start_time = time.perf_counter()
            try:
                result = chain.invoke(input_data)
                elapsed = time.perf_counter() - start_time
                total_duration += elapsed

                # Validate JSON structure adherence
                if isinstance(result, dict) and "wrong" in result:
                    valid_json_count += 1
                    if result.get("wrong") is True and input_data.get("anomaly") is True:
                        true_positives += 1
                    if result.get("wrong") is True and input_data.get("anomaly") is False:
                        false_positives += 1
                    if result.get("wrong") is False and input_data.get("anomaly") is True:
                        false_negatives += 1
                    if result.get("wrong") is False and input_data.get("anomaly") is False:
                        true_negatives += 1

            except Exception as e:
                elapsed = time.perf_counter() - start_time
                total_duration += elapsed
                print(f"[{model_name}] Parsing error: {str(e)}")

        avg_latency = (
            total_duration / total_records if total_records > 0 else 0.0
        )
        json_validity_pct = (
            (valid_json_count / total_records) * 100 if total_records > 0 else 0
        )
        presicion = (
            true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        )
        recall = (
            true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        )
        f1_score = (
            2 * (presicion * recall) / (presicion + recall) if (presicion + recall) > 0 else 0
        )
        flagged_anomalies = true_positives + false_positives

        return {
            "Model": model_name,
            "Total Samples": total_records,
            "JSON Validity (%)": round(json_validity_pct, 2),
            "Flagged Anomalies": flagged_anomalies,
            "Avg Latency (s)": round(avg_latency, 3),
            "Total Time (s)": round(total_duration, 2),
            "True Positives": true_positives,
            "False Positives": false_positives,
            "False Negatives": false_negatives,
            "True Negatives": true_negatives,
            "Precision": round(presicion, 2),
            "Recall": round(recall, 2),
            "F1 Score": round(f1_score, 2)
        }

    def run(
        self, df: pd.DataFrame, sample_size: Optional[int] = None
    ) -> pd.DataFrame:
        """Runs evaluation over the provided DataFrame and returns a summary DataFrame."""
        if df.empty:
            raise ValueError("Provided DataFrame is empty.")

        # Sample data if specified to limit benchmark runtime
        eval_df = (
            df.sample(n=sample_size, random_state=42)
            if sample_size and len(df) > sample_size
            else df
        )
        records = eval_df.to_dict(orient="records")

        results = []
        for model_name, parametersize in self.models:
            try:
                metrics = self._benchmark_single_model(model_name, records)
                results.append(metrics.update({"Parameter Size": parametersize}) or metrics)
            except Exception as e:
                print(f"Failed to benchmark model '{model_name}': {str(e)}")

        return pd.DataFrame(results)

if __name__ == "__main__":

    example_data = pd.DataFrame(
        [
            {
        "Oid":"881c85c7-bf7a-e911-b4a2-4c526221648e",
        "createdOn":1558337195317,
        "Subject":"R\u00fcckruf",
        "Duration":24.0,
        "ProjectName":None,
        "ClientName":"HUSS gmbh",
        "UserName":"VenDoc",
        "ActivityTypeName":"Telefon",
        "anomaly": True
    },
    {
        "Oid":"61e027e6-bf7a-e911-b4a2-4c526221648e",
        "createdOn":1558337244013,
        "Subject":"Anruf neue Version",
        "Duration":1.0,
        "ProjectName":None,
        "ClientName":"HUSS gmbh",
        "UserName":"VenDoc",
        "ActivityTypeName":"Telefon",
                "anomaly": False
    },
    {
        "Oid":"f514cfb9-c07a-e911-b4a2-4c526221648e",
        "createdOn":1558337595403,
        "Subject":"Anruf",
        "Duration":1.0,
        "ProjectName":None,
        "ClientName":"HUSS gmbh",
        "UserName":"VenDoc",
        "ActivityTypeName":"Telefon",
                "anomaly": False
    },
    {
        "Oid":"ab480688-c17a-e911-b4a2-4c526221648e",
        "createdOn":1558337948763,
        "Subject":"R\u00fcckruf",
        "Duration":24.0,
        "ProjectName":None,
        "ClientName":"HUSS gmbh",
        "UserName":"VenDoc",
        "ActivityTypeName":"Telefon",
                    "anomaly": True

    },
    {
        "Oid":"26f68241-c27a-e911-b4a2-4c526221648e",
        "createdOn":1558338282203,
        "Subject":"Abgabe Angebot",
        "Duration":1.0,
        "ProjectName":None,
        "ClientName":"HUSS gmbh",
        "UserName":"VenDoc",
        "ActivityTypeName":"Aufgabe",
                "anomaly": False
    },
    {
        "Oid":"f1f44aaa-c27a-e911-b4a2-4c526221648e",
        "createdOn":1558338436593,
        "Subject":"R\u00fcckruf",
        "Duration":24.0,
        "ProjectName":None,
        "ClientName":"HUSS gmbh",
        "UserName":"VenDoc",
        "ActivityTypeName":"Telefon",
                "anomaly": True

    },
    {
        "Oid":"0a5d184e-c37a-e911-b4a2-4c526221648e",
        "createdOn":1558338704817,
        "Subject":"R\u00fcckruf",
        "Duration":24.0,
        "ProjectName":None,
        "ClientName":"HUSS gmbh",
        "UserName":"VenDoc",
        "ActivityTypeName":"Telefon",
                "anomaly": True

    },
    {
        "Oid":"2de1008e-c37a-e911-b4a2-4c526221648e",
        "createdOn":1558338811127,
        "Subject":"Abgabetermin Angebot",
        "Duration":1.0,
        "ProjectName":None,
        "ClientName":"HUSS gmbh",
        "UserName":"VenDoc",
        "ActivityTypeName":"Aufgabe",
                "anomaly": False
    },
        ]
    )

    benchmarker = LLMBenchmarker(
        models=[("qwen2.5:7b", "7Mrd."), ("llama3.1:8b", "8Mrd."), ("qwen2.5:3b", "3Mrd.")]
    )
    results_df = benchmarker.run(df=example_data)

    print("\nBenchmark Summary:")
    print(results_df.to_string(index=False))