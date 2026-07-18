from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate


class LLMInterface(object):

    def __init__(self, model_name: str = "hr-analyst"):
        """Initialisiert die isolierte LangChain-Pipeline für die Lohnanalyse."""
        # 1. LLM initialisieren (Ollama muss im Hintergrund laufen)
        self.llm = ChatOllama(model=model_name, base_url="http://localhost:11434", verbose=True)

        # 2. JSON Output Parser vorbereiten
        self.output_parser = JsonOutputParser()
        # 3. Prompt Template definieren
        self.prompt = ChatPromptTemplate.from_messages(
            [
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

    def analyze_row(self, row: dict) -> dict:
        """Analysiert eine einzelne Buchung und gibt ein geparstes JSON-Dict zurück.

        Erwartet ein Dict mit den Keys: Mitarbeiter, Erstellungsdatum, Kunde,
        Auftrag, Tätigkeit, Stunden
        """
        try:
            # Sicherheits-Cast: Datums-Objekte (z.B. aus Pandas) vorab in String umwandeln
            if row.get("createdOn"):
                row["createdOn"] = str(row["createdOn"])

            # KI aufrufen und das fertige JSON-Ergebnis zurückgeben
            return self.chain.invoke(row)

        except Exception as e:
            # Fehler abfangen, damit ein externer Loop nicht komplett abstürzt
            return {"reason": f"Fehler bei der KI-Analyse: {str(e)}", "wrong": None}
