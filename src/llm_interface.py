from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate


class LLMInterface(object):
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

    
    def __init__(self, model_name: str = "hr-analyst"):
        """Initialise LLM-Pipeline with Ollama"""
        # 1. Initialize the LLM (Ollama must be running in the background)
        self.llm = ChatOllama(model=model_name, base_url="http://localhost:11434", verbose=True, temperature=0.1, num_ctx=4096, top_p=0.9)
        # 2. Prepare the JSON output parser
        self.output_parser = JsonOutputParser()
        # 3. Define the prompt template
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.SYSTEM_PROMPT),
                (
                    "user",
                    (
                        "Prüfe diese Buchung:\n"
                        "- Mitarbeiter: {UserName}\n"
                        "- Datum: {createdOn}\n"
                        "- Typ der Tätigkeit: {ActivityTypeName}\n"
                        "- Auftrag: {ProjectName}\n"
                        "- Tätigkeit: {Subject}\n"
                        "- Stunden: {Duration}\n"
                    ),
                )
            ]
        )

        # 4. Build the executable chain
        self.chain = self.prompt | self.llm | self.output_parser
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.llm = None

    def analyze_row(self, row: dict) -> dict:
        """
        Analyse a single row of data for anomalies and return the result as a dictionary.
        """
        try:
            # Safety cast: convert date objects (e.g. from Pandas) to strings up front
            if row.get("createdOn"):
                row["createdOn"] = str(row["createdOn"])

            # Invoke the model and return the final JSON result
            result = self.chain.invoke(row)
            # Merge metadata from the original row into the result so the exact source row can be traced later
            result.update(row)
            return result

        except Exception as e:
            raise Exception("Error initializing the LLM. The Ollama download may not have finished yet or Ollama may not be running in the background.")
