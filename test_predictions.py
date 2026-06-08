"""
ONE-DELUX-FAST - Test des Prédictions
SOLITAIRE HACK - Architecture professionnelle

Script de test pour le moteur de prédiction
"""

import logging
from datetime import datetime

from one_delux_fast import (
    get_api_client,
    get_prediction_engine,
    PredictionType
)


def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_match_winner_prediction():
    """Teste la prédiction de vainqueur"""
    print("🎯 TEST PRÉDICTION VAINQUEUR DU MATCH")
    print("=" * 80)
    
    api_client = get_api_client()
    prediction_engine = get_prediction_engine()
    
    # Récupérer les événements
    response = api_client.get_events()
    
    if not response.is_valid():
        print(f"❌ Erreur: {response.error}")
        return
    
    events = response.data
    
    if not events:
        print("❌ Aucun événement disponible")
        return
    
    # Tester sur les 5 premiers événements
    for i, event in enumerate(events[:5], 1):
        print(f"\n📊 Événement {i}: {event.team1_name} vs {event.team2_name}")
        print("-" * 80)
        
        try:
            prediction = prediction_engine.predict_match(event)
            
            status = "🔴 LIVE" if event.is_live else "⏰ À venir"
            score_info = ""
            if event.score:
                score_info = f" | Score: {event.score.team1_score}-{event.score.team2_score}"
            
            print(f"Statut: {status}{score_info}")
            print(f"Prédiction: {prediction.predicted_value.upper()}")
            print(f"Confiance: {prediction.confidence:.2%}")
            print(f"Distribution: {prediction.probability_distribution}")
            print(f"Version modèle: {prediction.model_version}")
            
            # Comparer avec les cotes
            favorite = event.get_favorite_team()
            print(f"Favorite (selon cotes): {favorite}")
            
            # Analyse
            if prediction.predicted_value == 'team1':
                predicted_team = event.team1_name
            elif prediction.predicted_value == 'team2':
                predicted_team = event.team2_name
            else:
                predicted_team = "Match nul"
            
            print(f"Équipe prédite: {predicted_team}")
            
            # Validation basique
            if prediction.confidence > 0.7:
                print("✅ Confiance élevée")
            elif prediction.confidence > 0.5:
                print("⚠️ Confiance moyenne")
            else:
                print("❌ Confiance faible")
            
        except Exception as e:
            print(f"❌ Erreur lors de la prédiction: {e}")
            import traceback
            traceback.print_exc()


def test_over_under_prediction():
    """Teste les prédictions Over/Under"""
    print("\n\n🎯 TEST PRÉDICTIONS OVER/UNDER")
    print("=" * 80)
    
    api_client = get_api_client()
    prediction_engine = get_prediction_engine()
    
    # Récupérer les événements
    response = api_client.get_events()
    
    if not response.is_valid():
        print(f"❌ Erreur: {response.error}")
        return
    
    events = response.data
    
    if not events:
        print("❌ Aucun événement disponible")
        return
    
    # Tester sur un événement en live si disponible
    live_event = next((e for e in events if e.is_live), events[0])
    
    print(f"\n📊 Événement: {live_event.team1_name} vs {live_event.team2_name}")
    print("-" * 80)
    
    score_info = ""
    if live_event.score:
        score_info = f" | Score: {live_event.score.team1_score}-{live_event.score.team2_score}"
    
    print(f"Statut: {'🔴 LIVE' if live_event.is_live else '⏰ À venir'}{score_info}")
    
    # Tester différents seuils
    thresholds = [2.5, 3.5, 4.5, 5.5, 6.5]
    
    for threshold in thresholds:
        print(f"\n📈 Seuil {threshold}:")
        print("-" * 80)
        
        try:
            prediction = prediction_engine.predict_over_under(live_event, threshold)
            
            print(f"Prédiction: {prediction.predicted_value.upper()}")
            print(f"Confiance: {prediction.confidence:.2%}")
            print(f"Distribution: {prediction.probability_distribution}")
            
            # Analyse
            if prediction.confidence > 0.6:
                print("✅ Prédiction fiable")
            else:
                print("⚠️ Prédiction incertaine")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")


def test_all_predictions():
    """Teste toutes les prédictions pour un événement"""
    print("\n\n🎯 TEST TOUTES LES PRÉDICTIONS")
    print("=" * 80)
    
    api_client = get_api_client()
    prediction_engine = get_prediction_engine()
    
    # Récupérer les événements
    response = api_client.get_events()
    
    if not response.is_valid():
        print(f"❌ Erreur: {response.error}")
        return
    
    events = response.data
    
    if not events:
        print("❌ Aucun événement disponible")
        return
    
    # Tester sur le premier événement
    event = events[0]
    
    print(f"\n📊 Événement: {event.team1_name} vs {event.team2_name}")
    print("-" * 80)
    
    try:
        all_predictions = prediction_engine.predict_all(event)
        
        for pred_type, prediction in all_predictions.items():
            print(f"\n🎯 {pred_type.upper()}:")
            print(f"   Prédiction: {prediction.predicted_value}")
            print(f"   Confiance: {prediction.confidence:.2%}")
            print(f"   Modèle: {prediction.model_version}")
            
            if prediction.probability_distribution:
                print(f"   Distribution: {prediction.probability_distribution}")
        
        # Résumé
        print(f"\n📋 RÉSUMÉ DES PRÉDICTIONS:")
        print("-" * 80)
        
        high_confidence = [
            pred_type for pred_type, pred in all_predictions.items()
            if pred.confidence > 0.7
        ]
        
        if high_confidence:
            print(f"✅ Prédictions à haute confiance: {', '.join(high_confidence)}")
        else:
            print("⚠️ Aucune prédiction à haute confiance")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def run_prediction_tests():
    """Exécute tous les tests de prédiction"""
    print("🚀 ONE-DELUX-FAST - Tests du Moteur de Prédiction")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    setup_logging()
    
    try:
        # Test des prédictions de vainqueur
        test_match_winner_prediction()
        
        # Test des prédictions Over/Under
        test_over_under_prediction()
        
        # Test de toutes les prédictions
        test_all_predictions()
        
        print("\n\n🎉 TESTS DE PRÉDICTION TERMINÉS AVEC SUCCÈS")
        print("=" * 80)
        print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interruption par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur globale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_prediction_tests()