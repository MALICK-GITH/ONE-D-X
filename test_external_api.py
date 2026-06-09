"""
ONE-DELUX-FAST - Test External API Direct
SOLITAIRE HACK - Architecture professionnelle

Script de test direct pour l'API externe
"""

import requests
import json

def test_external_api_direct():
    """Teste l'API externe directement"""
    
    url = "https://ai-p-hcuo.onrender.com/api/predict"
    
    # Payload de test
    payload = {
        "league": "Premier League",
        "homeTeam": "Manchester United",
        "awayTeam": "Liverpool",
        "home_odds": 2.5,
        "draw_odds": 3.2,
        "away_odds": 2.8,
        "match_datetime": "2026-06-15T15:00:00Z",
        "home_form_rate": 0.65,
        "away_form_rate": 0.72,
        "home_attack_avg": 1.8,
        "away_attack_avg": 2.1,
        "home_defense_avg": 1.2,
        "away_defense_avg": 1.4,
        "head_to_head_matches": 45,
        "head_to_head_home_winrate": 0.42
    }
    
    print("TEST DIRECT API EXTERNE")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        print("Envoi de la requete...")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        print(f"Response Body: {json.dumps(response.json(), indent=2) if response.text else response.text}")
        
    except requests.exceptions.Timeout:
        print("[ERROR] Timeout apres 30 secondes")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Erreur de connexion - API inaccessible")
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_external_api_direct()
