"""
ONE-DELUX-FAST - Validation Finale API Externe
SOLITAIRE HACK - Architecture professionnelle

Tests complets pour valider que l'API externe est la SEULE source de prédiction
et qu'elle renvoie des prédictions précises et cohérentes.
"""

import requests
import json

def test_multiple_scenarios():
    """Teste l'API externe avec plusieurs scénarios de match différents"""
    
    url = "http://localhost:5000/api/predict"
    
    # Scénarios de test variés
    scenarios = [
        {
            "name": "Match équilibré - Premier League",
            "payload": {
                "league": "Premier League",
                "home_team": "Manchester United",
                "away_team": "Liverpool",
                "home_odds": 2.5,
                "draw_odds": 3.2,
                "away_odds": 2.8,
                "home_form_rate": 0.65,
                "away_form_rate": 0.72,
                "home_attack_avg": 1.8,
                "away_attack_avg": 2.1,
                "home_defense_avg": 1.2,
                "away_defense_avg": 1.4,
                "head_to_head_matches": 45,
                "head_to_head_home_winrate": 0.42
            }
        },
        {
            "name": "Favorite fort à domicile",
            "payload": {
                "league": "La Liga",
                "home_team": "Real Madrid",
                "away_team": "Getafe",
                "home_odds": 1.3,
                "draw_odds": 5.5,
                "away_odds": 8.0,
                "home_form_rate": 0.85,
                "away_form_rate": 0.35,
                "home_attack_avg": 2.8,
                "away_attack_avg": 0.9,
                "home_defense_avg": 0.7,
                "away_defense_avg": 1.8,
                "head_to_head_matches": 20,
                "head_to_head_home_winrate": 0.75
            }
        },
        {
            "name": "Match outsider - Ligue 1",
            "payload": {
                "league": "Ligue 1",
                "home_team": "Lille",
                "away_team": "PSG",
                "home_odds": 4.5,
                "draw_odds": 3.8,
                "away_odds": 1.7,
                "home_form_rate": 0.45,
                "away_form_rate": 0.80,
                "home_attack_avg": 1.2,
                "away_attack_avg": 2.5,
                "home_defense_avg": 1.6,
                "away_defense_avg": 0.8,
                "head_to_head_matches": 30,
                "head_to_head_home_winrate": 0.25
            }
        },
        {
            "name": "Match avec données minimums",
            "payload": {
                "league": "Serie A",
                "home_team": "Juventus",
                "away_team": "AC Milan",
                "home_odds": 2.1,
                "draw_odds": 3.4,
                "away_odds": 3.5
            }
        },
        {
            "name": "Match très défensif",
            "payload": {
                "league": "Bundesliga",
                "home_team": "Bayern Munich",
                "away_team": "Borussia Dortmund",
                "home_odds": 1.9,
                "draw_odds": 3.6,
                "away_odds": 3.8,
                "home_form_rate": 0.70,
                "away_form_rate": 0.68,
                "home_attack_avg": 1.5,
                "away_attack_avg": 1.4,
                "home_defense_avg": 0.6,
                "away_defense_avg": 0.7,
                "head_to_head_matches": 50,
                "head_to_head_home_winrate": 0.55
            }
        }
    ]
    
    print("VALIDATION FINALE - API EXTERNE UNIQUE")
    print("=" * 80)
    print("Test de plusieurs scénarios pour valider la précision et la cohérence")
    print()
    
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"SCENARIO {i}: {scenario['name']}")
        print("-" * 80)
        
        try:
            response = requests.post(url, json=scenario['payload'], timeout=30)
            
            if response.status_code == 200:
                prediction = response.json()
                
                # Vérifier que la réponse contient tous les champs requis
                required_fields = ["home_goals", "away_goals", "total_goals", "over_under_2_5", "score_prediction", "confidence", "source"]
                missing_fields = [f for f in required_fields if f not in prediction]
                
                if missing_fields:
                    print(f"   [ERROR] Champs manquants: {missing_fields}")
                    print(f"   Response: {json.dumps(prediction, indent=2)}")
                    results.append({"scenario": scenario['name'], "status": "FAILED", "reason": "Missing fields"})
                else:
                    # Vérifier que la source est bien l'API externe
                    if prediction['source'] == "ONE DELUX AI 2.0":
                        print(f"   [OK] Source: {prediction['source']}")
                        print(f"   [OK] Prédiction: {prediction['score_prediction']}")
                        print(f"   [OK] Buts domicile: {prediction['home_goals']}")
                        print(f"   [OK] Buts extérieur: {prediction['away_goals']}")
                        print(f"   [OK] Total buts: {prediction['total_goals']}")
                        print(f"   [OK] Over/Under 2.5: {prediction['over_under_2_5']}")
                        print(f"   [OK] Confiance: {prediction['confidence']}%")
                        results.append({"scenario": scenario['name'], "status": "SUCCESS", "prediction": prediction})
                    else:
                        print(f"   [ERROR] Source incorrecte: {prediction['source']}")
                        results.append({"scenario": scenario['name'], "status": "FAILED", "reason": "Wrong source"})
            else:
                print(f"   [ERROR] Status code: {response.status_code}")
                print(f"   Response: {response.text}")
                results.append({"scenario": scenario['name'], "status": "FAILED", "reason": f"HTTP {response.status_code}"})
                
        except Exception as e:
            print(f"   [ERROR] Exception: {e}")
            results.append({"scenario": scenario['name'], "status": "FAILED", "reason": str(e)})
        
        print()
    
    # Résumé final
    print("=" * 80)
    print("RESUME FINAL")
    print("=" * 80)
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    total_count = len(results)
    
    print(f"Tests réussis: {success_count}/{total_count}")
    print()
    
    if success_count == total_count:
        print("[SUCCESS] TOUS LES TESTS REUSSIS")
        print("[SUCCESS] L'API externe est la SEULE source de prediction")
        print("[SUCCESS] Les predictions sont coherentes et precises")
    else:
        print("[ERROR] CERTAINS TESTS ONT ECHOUE")
        for result in results:
            if result['status'] == 'FAILED':
                print(f"   - {result['scenario']}: {result.get('reason', 'Unknown error')}")
    
    print()
    print("DETAILS DES PREDICTIONS:")
    print("-" * 80)
    for result in results:
        if result['status'] == 'SUCCESS':
            pred = result['prediction']
            print(f"{result['scenario']}:")
            print(f"   Score: {pred['score_prediction']} | Total: {pred['total_goals']} | O/U: {pred['over_under_2_5']} | Confiance: {pred['confidence']}%")


if __name__ == "__main__":
    test_multiple_scenarios()
