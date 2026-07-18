import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# Tausche ChatOllama einfach gegen ChatOpenAI oder ChatAnthropic aus, je nachdem was du nutzt
from langchain_community.chat_models import ChatOllama 

# 1. LLM und Output Parser initialisieren
llm = ChatOllama(model="llama3", temperature=0.2) # Niedrige Temp für präzise Analyse
output_parser = StrOutputParser()

# 2. Prompt Template definieren
# Die Platzhalter im Text müssen EXAKT so heißen wie deine Spaltennamen im DataFrame!
prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "Du bist ein Experte für Lohnbuchhaltung und HR-Compliance. "
        "Analysiere die folgende Arbeitszeitbuchung auf Auffälligkeiten, Fehler oder Optimierungspotenziale. "
        "Antworte kurz und knackig in maximal 3 Sätzen."
    )),
    ("user", (
        "Bitte prüfe diese Buchung:\n"
        "- Mitarbeiter: {Mitarbeiter}\n"
        "- Datum der Buchung: {Erstellungsdatum}\n"
        "- Kunde: {Kunde}\n"
        "- Auftrag/Projekt: {Auftrag}\n"
        "- Tätigkeit: {Tätigkeit}\n"
        "- Erfasste Stunden: {Stunden}\n"
    ))
])

# 3. Chain zusammenbauen
chain = prompt | llm | output_parser

# 4. Der Loop über alle Zeilen
print(f"Starte Analyse von {len(rows)} Buchungen...\n")

for index, row in enumerate(rows):
    print(f"--- Analyse für Zeile {index + 1} ({row['Mitarbeiter']}) ---")
    
    # LangChain matcht die Dict-Keys automatisch mit den {} Platzhaltern im Prompt
    response = chain.invoke(row)
    
    print(response)
    print("\n" + "="*50 + "\n")