"""
ONE-DELUX-FAST - Interface CLI Principale
SOLITAIRE HACK - Architecture professionnelle

Interface en ligne de commande interactive pour la plateforme
"""

import sys
import logging
from datetime import datetime
from typing import Optional

from one_delux_fast import (
    get_api_client,
    get_data_manager,
    get_prediction_engine
)


class CLIMenu:
    """
    Menu interactif en ligne de commande
    Interface utilisateur principale
    """
    
    def __init__(self):
        self.api_client = get_api_client()
        self.data_manager = get_data_manager()
        self.prediction_engine = get_prediction_engine()
        self.running = True
        
        self.setup_logging()
    
    def setup_logging(self):
        """Configure le logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def display_header(self):
        """Affiche l'en-tête de l'application"""
        print("\n" + "=" * 80)
        print("🚀 ONE-DELUX-FAST - Plateforme de Prédiction Sportive")
        print("   SOLITAIRE HACK - Excellence Professionnelle")
        print("=" * 80)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def display_main_menu(self):
        """Affiche le menu principal"""
        print("📋 MENU PRINCIPAL:")
        print("-" * 80)
        print("1. 📊 Voir les événements actuels")
        print("2. 🎯 Prédictions pour un événement")
        print("3. 📈 Statistiques de l'API")
        print("4. 💾 Gestion du cache")
        print("5. 🗃️ Statistiques de la base de données")
        print("6. 🔄 Rafraîchir les données")
        print("7. 🧪 Tester les prédictions")
        print("8. ℹ️ Information système")
        print("0. 🚪 Quitter")
        print()
    
    def display_events_menu(self, events):
        """Affiche le menu des événements"""
        if not events:
            print("❌ Aucun événement disponible")
            return
        
        print(f"📊 {len(events)} ÉVÉNEMENTS DISPONIBLES:")
        print("-" * 80)
        
        for i, event in enumerate(events[:20], 1):  # Limiter à 20 pour l'affichage
            status = "🔴 LIVE" if event.is_live else "⏰ "
            score = ""
            if event.score and event.is_live:
                score = f" ({event.score.team1_score}-{event.score.team2_score})"
            
            print(f"{i:2d}. {status} {event.team1_name:25s} vs {event.team2_name:25s}{score}")
        
        if len(events) > 20:
            print(f"... et {len(events) - 20} autres événements")
        
        print()
    
    def show_current_events(self):
        """Affiche les événements actuels"""
        print("\n📊 RÉCUPÉRATION DES ÉVÉNEMENTS...")
        print("-" * 80)
        
        response = self.api_client.get_events()
        
        if not response.is_valid():
            print(f"❌ Erreur: {response.error}")
            return
        
        events = response.data
        print(f"✅ {len(events)} événements récupérés")
        print()
        
        self.display_events_menu(events)
        
        # Statistiques rapides
        live_count = sum(1 for e in events if e.is_live)
        upcoming_count = len(events) - live_count
        
        print(f"📈 STATISTIQUES RAPIDES:")
        print("-" * 80)
        print(f"🔴 En direct: {live_count}")
        print(f"⏰ À venir: {upcoming_count}")
        
        # Ligues
        leagues = {}
        for event in events:
            leagues[event.league_name] = leagues.get(event.league_name, 0) + 1
        
        print(f"\n🏆 LIGUES:")
        for league, count in sorted(leagues.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {league}: {count} événements")
    
    def show_predictions_menu(self, events):
        """Affiche le menu des prédictions"""
        if not events:
            print("❌ Aucun événement disponible pour les prédictions")
            return
        
        print("\n🎯 SÉLECTIONNER UN ÉVÉNEMENT:")
        print("-" * 80)
        
        for i, event in enumerate(events[:10], 1):
            status = "🔴 LIVE" if event.is_live else "⏰ "
            print(f"{i}. {status} {event.team1_name} vs {event.team2_name}")
        
        print("\n0. Retour au menu principal")
        print()
        
        try:
            choice = input("👉 Choix: ").strip()
            
            if choice == "0":
                return
            
            event_idx = int(choice) - 1
            if 0 <= event_idx < min(len(events), 10):
                self.show_event_predictions(events[event_idx])
            else:
                print("❌ Choix invalide")
        
        except (ValueError, IndexError):
            print("❌ Choix invalide")
    
    def show_event_predictions(self, event):
        """Affiche les prédictions pour un événement"""
        print(f"\n🎯 PRÉDICTIONS: {event.team1_name} vs {event.team2_name}")
        print("=" * 80)
        
        # Informations de l'événement
        status = "🔴 LIVE" if event.is_live else "⏰ À venir"
        score_info = ""
        if event.score and event.is_live:
            score_info = f" | Score: {event.score.team1_score}-{event.score.team2_score}"
        
        print(f"Statut: {status}{score_info}")
        print(f"Ligue: {event.league_name}")
        print(f"Favorite: {event.get_favorite_team()}")
        print()
        
        try:
            # Prédiction du vainqueur
            print("🏆 PRÉDICTION VAINQUEUR:")
            print("-" * 80)
            winner_pred = self.prediction_engine.predict_match(event)
            
            predicted_team = (
                event.team1_name if winner_pred.predicted_value == 'team1'
                else event.team2_name if winner_pred.predicted_value == 'team2'
                else "Match nul"
            )
            
            print(f"Équipe prédite: {predicted_team}")
            print(f"Confiance: {winner_pred.confidence:.2%}")
            print(f"Distribution: {winner_pred.probability_distribution}")
            print()
            
            # Prédictions Over/Under
            print("📈 PRÉDICTIONS OVER/UNDER:")
            print("-" * 80)
            
            thresholds = [2.5, 3.5, 4.5, 5.5]
            for threshold in thresholds:
                try:
                    ou_pred = self.prediction_engine.predict_over_under(event, threshold)
                    confidence_emoji = "✅" if ou_pred.confidence > 0.6 else "⚠️"
                    print(f"{confidence_emoji} Seuil {threshold}: {ou_pred.predicted_value.upper()} ({ou_pred.confidence:.2%})")
                except Exception as e:
                    print(f"❌ Erreur pour seuil {threshold}: {e}")
            
            print()
            
            # Recommandation
            print("💡 RECOMMANDATION:")
            print("-" * 80)
            
            if winner_pred.confidence > 0.7:
                print(f"✅ Forte confiance: Pariez sur {predicted_team}")
            elif winner_pred.confidence > 0.5:
                print(f"⚠️ Confiance moyenne: {predicted_team} semble légèrement favori")
            else:
                print("❌ Faible confiance: Match difficile à prédire")
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération des prédictions: {e}")
            import traceback
            traceback.print_exc()
    
    def show_api_statistics(self):
        """Affiche les statistiques de l'API"""
        print("\n📊 STATISTIQUES DE L'API:")
        print("-" * 80)
        
        stats = self.api_client.get_statistics()
        
        print(f"📡 Requêtes totales: {stats['total_requests']}")
        print(f"❌ Erreurs: {stats['total_errors']}")
        print(f"✅ Taux de succès: {stats['success_rate']:.2%}")
        print()
        
        cache_stats = self.data_manager.cache.get_statistics()
        print("🗄️ STATISTIQUES DU CACHE:")
        print("-" * 80)
        print(f"📦 Taille: {cache_stats['cache_size']} entrées")
        print(f"✅ Hits: {cache_stats['hits']}")
        print(f"❌ Misses: {cache_stats['misses']}")
        print(f"📊 Taux de hit: {cache_stats['hit_rate']:.2%}")
    
    def show_cache_management(self):
        """Affiche le menu de gestion du cache"""
        print("\n💾 GESTION DU CACHE:")
        print("-" * 80)
        print("1. Vider le cache")
        print("2. Nettoyer les entrées expirées")
        print("3. Voir les statistiques du cache")
        print("0. Retour au menu principal")
        print()
        
        try:
            choice = input("👉 Choix: ").strip()
            
            if choice == "1":
                self.data_manager.cache.clear()
                print("✅ Cache vidé")
            elif choice == "2":
                cleaned = self.data_manager.cache.cleanup_expired()
                print(f"✅ {cleaned} entrées expirées nettoyées")
            elif choice == "3":
                stats = self.data_manager.cache.get_statistics()
                print(f"📊 Statistiques: {stats}")
            elif choice == "0":
                return
            else:
                print("❌ Choix invalide")
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    def show_database_statistics(self):
        """Affiche les statistiques de la base de données"""
        print("\n🗃️ STATISTIQUES DE LA BASE DE DONNÉES:")
        print("-" * 80)
        
        try:
            # Statistiques de base
            print(f"📁 Chemin: {self.data_manager.database.db_path}")
            print(f"📊 Statut: Active")
            
            # Compter les enregistrements
            import sqlite3
            conn = sqlite3.connect(self.data_manager.database.db_path)
            cursor = conn.cursor()
            
            # Événements
            cursor.execute("SELECT COUNT(*) FROM events")
            event_count = cursor.fetchone()[0]
            print(f"🏆 Événements: {event_count}")
            
            # Cotes
            cursor.execute("SELECT COUNT(*) FROM odds")
            odds_count = cursor.fetchone()[0]
            print(f"📈 Cotes: {odds_count}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}")
    
    def refresh_data(self):
        """Rafraîchit les données depuis l'API"""
        print("\n🔄 RAFRAÎCHISSEMENT DES DONNÉES...")
        print("-" * 80)
        
        # Forcer le rafraîchissement
        response = self.api_client.get_events()
        
        if response.is_valid():
            events = response.data
            
            # Mettre en cache
            self.data_manager.cache_events(events, ttl=60)
            
            # Sauvegarder en base
            saved_count = 0
            for event in events[:10]:
                if self.data_manager.database.save_event(event):
                    saved_count += 1
            
            print(f"✅ {len(events)} événements récupérés")
            print(f"💾 {saved_count} événements sauvegardés en base")
            print("✅ Cache mis à jour")
        else:
            print(f"❌ Erreur: {response.error}")
    
    def test_predictions(self):
        """Exécute les tests de prédiction"""
        print("\n🧪 TESTS DE PRÉDICTION")
        print("-" * 80)
        
        response = self.api_client.get_events()
        
        if not response.is_valid():
            print(f"❌ Erreur: {response.error}")
            return
        
        events = response.data
        
        if not events:
            print("❌ Aucun événement disponible")
            return
        
        # Tester sur 3 événements
        for i, event in enumerate(events[:3], 1):
            print(f"\n📊 Test {i}: {event.team1_name} vs {event.team2_name}")
            print("-" * 80)
            
            try:
                predictions = self.prediction_engine.predict_all(event)
                
                for pred_type, pred in predictions.items():
                    print(f"{pred_type}: {pred.predicted_value} ({pred.confidence:.2%})")
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def show_system_info(self):
        """Affiche les informations système"""
        print("\nℹ️ INFORMATIONS SYSTÈME:")
        print("-" * 80)
        
        print(f"🚀 Application: ONE-DELUX-FAST")
        print(f"📅 Version: 1.0.0")
        print(f"👤 Auteur: SOLITAIRE HACK")
        print()
        
        print(f"⏰ Heure actuelle: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Version Python: {sys.version.split()[0]}")
        print()
        
        print("📦 MODULES ACTIFS:")
        print("   ✅ API Client")
        print("   ✅ Data Manager")
        print("   ✅ Prediction Engine")
        print("   ✅ Cache Manager")
        print("   ✅ Database Manager")
    
    def run(self):
        """Exécute la boucle principale du menu"""
        while self.running:
            try:
                self.display_header()
                self.display_main_menu()
                
                choice = input("👉 Choix: ").strip()
                
                if choice == "0":
                    self.running = False
                    print("\n👋 Au revoir!")
                elif choice == "1":
                    self.show_current_events()
                elif choice == "2":
                    response = self.api_client.get_events()
                    if response.is_valid():
                        self.show_predictions_menu(response.data)
                elif choice == "3":
                    self.show_api_statistics()
                elif choice == "4":
                    self.show_cache_management()
                elif choice == "5":
                    self.show_database_statistics()
                elif choice == "6":
                    self.refresh_data()
                elif choice == "7":
                    self.test_predictions()
                elif choice == "8":
                    self.show_system_info()
                else:
                    print("❌ Choix invalide")
                
                input("\nAppuyez sur Entrée pour continuer...")
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Interruption par l'utilisateur")
                self.running = False
            except Exception as e:
                print(f"\n❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
                input("\nAppuyez sur Entrée pour continuer...")


def main():
    """Fonction principale"""
    cli = CLIMenu()
    cli.run()


if __name__ == "__main__":
    main()