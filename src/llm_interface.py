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
        # 1. LLM initialisieren (Ollama muss im Hintergrund laufen)
        self.llm = ChatOllama(model=model_name, base_url="http://localhost:11434", verbose=True)

        # 2. JSON Output Parser vorbereiten
        self.output_parser = JsonOutputParser()
        # 3. Prompt Template definieren
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

        # 4. Die ausführbare Chain zusammenbauen
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
            # Sicherheits-Cast: Datums-Objekte (z.B. aus Pandas) vorab in String umwandeln
            if row.get("createdOn"):
                row["createdOn"] = str(row["createdOn"])

            # KI aufrufen und das fertige JSON-Ergebnis zurückgeben
            result = self.chain.invoke(row)
            # Metadaten aus der Original-Zeile in das Ergebnis übernehmen, damit man später nachvollziehen kann, welche Zeile genau analysiert wurde
            result.update(row)
            return result

        except Exception as e:
            # Fehler abfangen, damit ein externer Loop nicht komplett abstürzt
            return {"reason": f"Fehler bei der KI-Analyse: {str(e)}", "wrong": None}
