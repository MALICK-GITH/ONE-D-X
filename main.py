"""
ONE-DELUX-FAST - Point d'Entrée Principal
SOLITAIRE HACK - Architecture Professionnelle

Script principal pour tester l'intégration API
"""

import logging
import os
import sys
from datetime import datetime

from one_delux_fast.api_client import get_api_client, BetType
from one_delux_fast.data_manager import get_data_manager
from config import get_config


def setup_logging():
    """Configure le logging"""
    config = get_config()
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format=config.logging.format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.get_log_path())
        ]
    )


def analyze_events(events):
    """Analyse les événements récupérés"""
    if not events:
        print("❌ Aucun événement à analyser")
        return
    
    print(f"📊 ANALYSE DE {len(events)} ÉVÉNEMENTS")
    print("=" * 80)
    
    # Statistiques générales
    live_events = [e for e in events if e.is_live]
    upcoming_events = [e for e in events if not e.is_live]
    
    print(f"🔴 Événements en direct: {len(live_events)}")
    print(f"⏰ Événements à venir: {len(upcoming_events)}")
    print()
    
    # Analyse par ligue
    leagues = {}
    for event in events:
        if event.league_name not in leagues:
            leagues[event.league_name] = []
        leagues[event.league_name].append(event)
    
    print("🏆 ÉVÉNEMENTS PAR LIGUE:")
    print("-" * 80)
    for league_name, league_events in sorted(leagues.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"• {league_name}: {len(league_events)} événements")
    print()
    
    # Top 5 des événements
    print("🎯 TOP 5 ÉVÉNEMENTS:")
    print("-" * 80)
    for i, event in enumerate(events[:5], 1):
        status = "🔴 LIVE" if event.is_live else "⏰ À venir"
        score_str = ""
        if event.score:
            score_str = f" | Score: {event.score.team1_score}-{event.score.team2_score} ({event.score.status})"
        
        favorite = event.get_favorite_team()
        
        print(f"{i}. {status} {event.team1_name} vs {event.team2_name}")
        print(f"   Ligue: {event.league_name}{score_str}")
        print(f"   Favorite: {favorite}")
        print(f"   Cotes disponibles: {len(event.odds)} principales + {len(event.additional_odds)} additionnelles")
        print()
    
    # Analyse des cotes
    print("📈 ANALYSE DES COTES:")
    print("-" * 80)
    
    # Compter les types de paris
    bet_types_count = {}
    for event in events:
        for odds in event.odds:
            bet_type = odds.bet_type
            if bet_type not in bet_types_count:
                bet_types_count[bet_type] = 0
            bet_types_count[bet_type] += 1
    
    for bet_type_code in sorted(bet_types_count.keys()):
        count = bet_types_count[bet_type_code]
        description = BetType.get_description(bet_type_code)
        print(f"• Type {bet_type_code:2d} ({description:30s}): {count:3d} occurrences")
    print()
    
    # Statistiques du client API
    api_client = get_api_client()
    api_stats = api_client.get_statistics()
    print("⚡ STATISTIQUES CLIENT API:")
    print("-" * 80)
    print(f"• Requêtes totales: {api_stats['total_requests']}")
    print(f"• Erreurs: {api_stats['total_errors']}")
    print(f"• Taux de succès: {api_stats['success_rate']:.2%}")
    print()


def test_integration():
    """Teste l'intégration complète"""
    print("🚀 ONE-DELUX-FAST - Test d'Intégration API")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialisation
    setup_logging()
    config = get_config()
    api_client = get_api_client()
    data_manager = get_data_manager()
    
    print(f"📋 Configuration:")
    print(f"• Application: {config.app_name} v{config.app_version}")
    print(f"• Environnement: {config.environment}")
    print(f"• API URL: {config.api.base_url}")
    print(f"• Timeout: {config.api.timeout}s")
    print()
    
    # Récupération des événements
    print("📡 Récupération des événements depuis l'API...")
    api_response = api_client.get_events()
    
    if not api_response.is_valid():
        print(f"❌ Erreur lors de la récupération: {api_response.error}")
        return
    
    events = api_response.data
    print(f"✅ {len(events)} événements récupérés avec succès")
    print()
    
    # Analyse des événements
    analyze_events(events)
    
    # Mise en cache
    print("💾 Mise en cache des événements...")
    data_manager.cache_events(events, ttl=config.cache.events_ttl)
    print("✅ Événements mis en cache")
    print()
    
    # Statistiques du cache
    cache_stats = data_manager.cache.get_statistics()
    print("🗄️ STATISTIQUES DU CACHE:")
    print("-" * 80)
    print(f"• Taille du cache: {cache_stats['cache_size']} entrées")
    print(f"• Hits: {cache_stats['hits']}")
    print(f"• Misses: {cache_stats['misses']}")
    print(f"• Taux de hit: {cache_stats['hit_rate']:.2%}")
    print()
    
    # Sauvegarde en base de données
    print("🗃️ Sauvegarde des événements en base de données...")
    saved_count = 0
    for event in events[:10]:  # Sauvegarder seulement les 10 premiers pour le test
        if data_manager.database.save_event(event):
            saved_count += 1
    
    print(f"✅ {saved_count} événements sauvegardés en base de données")
    print()
    
    # Test du cache
    print("🔄 Test du cache (récupération depuis le cache)...")
    cached_events = data_manager.get_events_with_cache()
    if cached_events:
        print(f"✅ {len(cached_events)} événements récupérés depuis le cache")
    else:
        print("ℹ️ Pas d'événements dans le cache (normal pour le premier test)")
    print()
    
    print("🎉 TEST D'INTÉGRATION TERMINÉ AVEC SUCCÈS")
    print("=" * 80)
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def test_specific_bet_types():
    """Teste l'analyse de types de paris spécifiques"""
    print("🎯 TEST DES TYPES DE PARIS SPÉCIFIQUES")
    print("=" * 80)
    
    api_client = get_api_client()
    api_response = api_client.get_events()
    
    if not api_response.is_valid():
        print(f"❌ Erreur: {api_response.error}")
        return
    
    events = api_response.data
    event = events[0] if events else None
    
    if not event:
        print("❌ Aucun événement disponible")
        return
    
    print(f"📊 Analyse des cotes pour: {event.team1_name} vs {event.team2_name}")
    print("-" * 80)
    
    # Analyser les cotes principales
    print("COTES PRINCIPALES (1X2):")
    print("-" * 80)
    
    main_odds_types = [1, 2, 3, 4]  # Types de paris 1X2
    for bet_type in main_odds_types:
        odds = event.get_main_odds(bet_type)
        if odds:
            description = BetType.get_description(bet_type)
            param_str = f" ({odds.parameter:+})" if odds.parameter is not None else ""
            print(f"• Type {bet_type} ({description}): {odds.coefficient:.3f}{param_str}")
    
    print()
    print("ÉQUIPE FAVORITE:")
    print("-" * 80)
    favorite = event.get_favorite_team()
    print(f"🏆 {favorite}")
    print()
    
    # Analyser les handicaps
    print("HANDICAPS DISPONIBLES:")
    print("-" * 80)
    
    handicap_types = [7, 8]  # Handicap positif/négatif
    handicaps = {}
    
    for odds in event.odds + event.additional_odds:
        if odds.bet_type in handicap_types and odds.parameter is not None:
            if odds.parameter not in handicaps:
                handicaps[odds.parameter] = []
            handicaps[odds.parameter].append(odds)
    
    for param in sorted(handicaps.keys()):
        odds_list = handicaps[param]
        for odds in odds_list:
            description = BetType.get_description(odds.bet_type)
            print(f"• Handicap {param:+.1f} ({description}): {odds.coefficient:.3f}")
    
    print()
    print("OVER/UNDER DISPONIBLES:")
    print("-" * 80)
    
    over_under_types = [9, 10]
    over_under = {}
    
    for odds in event.odds + event.additional_odds:
        if odds.bet_type in over_under_types and odds.parameter is not None:
            if odds.parameter not in over_under:
                over_under[odds.parameter] = {}
            over_under[odds.parameter][odds.bet_type] = odds
    
    for param in sorted(over_under.keys()):
        print(f"• Seuil {param:.1f}:")
        if 9 in over_under[param]:
            print(f"  - Over: {over_under[param][9].coefficient:.3f}")
        if 10 in over_under[param]:
            print(f"  - Under: {over_under[param][10].coefficient:.3f}")


def start_web_server():
    """
    Démarre l'application FastAPI conforme au manifeste d'intégration.
    Utilisé en production et sur Render via la variable PORT.
    """
    from platform_service import app as web_app

    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")

    print("Demarrage du serveur API ONE-DELUX-FAST...")
    print(f"Ecoute sur {host}:{port}")
    import uvicorn

    uvicorn.run(web_app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # En environnement de déploiement, main.py doit garder un port ouvert.
    # En local, on conserve les tests d'intégration par défaut.
    run_server = os.getenv("PORT") or os.getenv("RENDER") == "true" or os.getenv("RUN_WEB_SERVER") == "true"

    if run_server:
        start_web_server()
    else:
        try:
            # Test d'intégration complet
            test_integration()

            print("\n")

            # Test des types de paris spécifiques
            test_specific_bet_types()

        except KeyboardInterrupt:
            print("\n⚠️ Interruption par l'utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
