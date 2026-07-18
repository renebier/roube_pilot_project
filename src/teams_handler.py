import os
import requests


class TeamsConnector:

    def __init__(self, webhook_url: str = None):
        """Init Teams connector with optional webhook URL. If not provided, it will look for the TEAMS_WEBHOOK_URL environment variable."""
        self.webhook_url = webhook_url or os.getenv("TEAMS_WEBHOOK_URL")

        if not self.webhook_url:
            print(
                "⚠️ Warnung: Keine TEAMS_WEBHOOK_URL gefunden. "
                "Nachrichten werden nur in der Konsole ausgegeben."
            )
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass
    
    def send_anomaly_alert(self, row: dict, reason: str) -> bool:
        """Format the anomaly alert as an Adaptive Card and send it to MS Teams. Returns True if successful, False otherwise."""
        if not self.webhook_url:
            return False

        # Adaptive Card payload for MS Teams
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "🚨 Lohn-Audit: Anomalie erkannt",
                                "weight": "Bolder",
                                "size": "Medium",
                                "color": "Attention",
                            },
                            {
                                "type": "TextBlock",
                                "text": f"**Grund:** {reason}",
                                "wrap": True,
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {
                                        "title": "Mitarbeiter:",
                                        "value": str(row.get("Mitarbeiter")),
                                    },
                                    {
                                        "title": "Datum:",
                                        "value": str(
                                            row.get("Erstellungsdatum")
                                        ),
                                    },
                                    {
                                        "title": "Kunde:",
                                        "value": str(
                                            row.get("Kunde") or "Keine Angabe"
                                        ),
                                    },
                                    {
                                        "title": "Auftrag:",
                                        "value": str(
                                            row.get("Auftrag") or "Keine Angabe"
                                        ),
                                    },
                                    {
                                        "title": "Tätigkeit:",
                                        "value": str(row.get("Tätigkeit")),
                                    },
                                    {
                                        "title": "Stunden:",
                                        "value": f"{row.get('Stunden')} Std.",
                                    },
                                ],
                            },
                        ],
                    },
                }
            ],
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in [200, 201, 202]:
                return True
            else:
                print(
                    f"Fehler beim Senden an Teams (Status: {response.status_code}): {response.text}"
                )
                return False
        except Exception as e:
            print(f"Verbindungsfehler zu MS Teams: {e}")
            return False