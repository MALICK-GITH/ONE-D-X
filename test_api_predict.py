"""
ONE-DELUX-FAST - Test API Predict Endpoint
SOLITAIRE HACK - Architecture professionnelle

Script de test pour l'endpoint /api/predict avec le format spécifié
"""

import requests
import json

def test_predict_endpoint():
    """Teste l'endpoint /api/predict avec le format specifie"""
    
    # URL de l'endpoint
    url = "http://localhost:5000/api/predict"
    
    # Payload de test selon les specifications
    payload = {
        "league": "Premier League",
        "home_team": "Manchester United",
        "away_team": "Liverpool",
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
    
    print("TEST API PREDICT - Format snake_case")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Verifier que la reponse contient les champs attendus
        expected_fields = ["home_goals", "away_goals", "total_goals", "over_under_2_5", "score_prediction", "confidence", "source"]
        response_data = response.json()
        
        print("\nVerification des champs de reponse:")
        for field in expected_fields:
            if field in response_data:
                print(f"   [OK] {field}: {response_data[field]}")
            else:
                print(f"   [MISSING] {field}: MANQUANT")
        
        # Test avec camelCase
        print("\n\nTEST API PREDICT - Format camelCase")
        print("=" * 80)
        
        payload_camel = {
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
        
        response_camel = requests.post(url, json=payload_camel)
        print(f"Status Code: {response_camel.status_code}")
        print(f"Response: {json.dumps(response_camel.json(), indent=2)}")
        
        # Test avec champs minimums
        print("\n\nTEST API PREDICT - Champs minimums")
        print("=" * 80)
        
        payload_min = {
            "league": "Premier League",
            "home_team": "Manchester United",
            "away_team": "Liverpool",
            "home_odds": 2.5,
            "draw_odds": 3.2,
            "away_odds": 2.8
        }
        
        response_min = requests.post(url, json=payload_min)
        print(f"Status Code: {response_min.status_code}")
        print(f"Response: {json.dumps(response_min.json(), indent=2)}")
        
        # Test de validation des erreurs
        print("\n\nTEST API PREDICT - Validation des erreurs")
        print("=" * 80)
        
        payload_invalid = {
            "league": "Premier League",
            "home_team": "Manchester United",
            "away_odds": 2.8
        }
        
        response_invalid = requests.post(url, json=payload_invalid)
        print(f"Status Code: {response_invalid.status_code}")
        print(f"Response: {json.dumps(response_invalid.json(), indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("[ERROR] Erreur: Impossible de connecter au serveur. Assurez-vous que le serveur est demarre.")
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_predict_endpoint()
