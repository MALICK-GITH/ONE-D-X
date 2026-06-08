"""
ONE-DELUX-FAST - Analyse de l'API 888starz (mode offline avec données déjà récupérées)
SOLITAIRE HACK - Analyse professionnelle et rigoureuse
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class APIParameter:
    """Représentation d'un paramètre de l'API"""
    name: str
    value: str
    description: str
    type: str
    
@dataclass 
class BetType:
    """Représentation d'un type de pari"""
    code: int
    description: str
    example_odds: float
    
@dataclass
class EventInfo:
    """Informations sur un événement sportif"""
    event_id: int
    sport_name: str
    league_name: str
    team1: str
    team2: str
    start_time: int
    is_live: bool
    current_score: Dict[str, int]
    odds: List[Dict[str, Any]]


class APIAnalyzer:
    """
    Analyseur professionnel de l'API 888starz
    Analyse structurelle, fonctionnelle et performance
    """
    
    def analyze_parameters(self) -> List[APIParameter]:
        """Analyse tous les paramètres de l'API"""
        parameters = [
            APIParameter("sports", "85", "Identifiant du sport (85 = FIFA/eSports)", "integer"),
            APIParameter("count", "40", "Nombre d'événements à retourner", "integer"),
            APIParameter("lng", "fr", "Langue de la réponse", "string"),
            APIParameter("gr", "789", "Groupe de règles/filtre", "integer"),
            APIParameter("mode", "4", "Mode de récupération des données", "integer"),
            APIParameter("country", "96", "Code pays pour les restrictions", "integer"),
            APIParameter("partner", "233", "Identifiant partenaire", "integer"),
            APIParameter("getEmpty", "true", "Inclure les événements sans cotes", "boolean"),
            APIParameter("virtualSports", "true", "Inclure les sports virtuels", "boolean"),
            APIParameter("noFilterBlockEvent", "true", "Désactiver les filtres d'événements bloqués", "boolean")
        ]
        return parameters
    
    def analyze_bet_types(self, data: Dict) -> List[BetType]:
        """Analyse les types de paris disponibles"""
        bet_types_mapping = {
            1: "Victoire équipe 2 (Outsider)",
            2: "Victoire équipe 1 (Outsider)",
            3: "Victoire équipe 1 (Favorite)",
            4: "Victoire équipe 2 (Favorite)",
            5: "Double chance 1X ou 12",
            6: "Double chance X2 ou 12",
            7: "Handicap positif équipe 1",
            8: "Handicap négatif équipe 1",
            9: "Over (plus de) buts/points",
            10: "Under (moins de) buts/points",
            11: "Équipe 1 marque plus de",
            12: "Équipe 1 marque moins de",
            13: "Équipe 2 marque plus de",
            14: "Équipe 2 marque moins de"
        }
        
        found_types = set()
        bet_types = []
        
        for event in data.get('Value', []):
            for odd in event.get('E', []):
                type_code = odd.get('T')
                if type_code not in found_types and type_code in bet_types_mapping:
                    found_types.add(type_code)
                    bet_types.append(BetType(
                        code=type_code,
                        description=bet_types_mapping[type_code],
                        example_odds=odd.get('C', 0.0)
                    ))
        
        return sorted(bet_types, key=lambda x: x.code)
    
    def analyze_response_structure(self, data: Dict) -> Dict[str, Any]:
        """Analyse la structure de la réponse API"""
        analysis = {
            "metadata": {
                "success": data.get('Success', False),
                "error": data.get('Error', ''),
                "error_code": data.get('ErrorCode', 0),
                "guid": data.get('Guid', ''),
                "timestamp": datetime.now().isoformat()
            },
            "events_count": len(data.get('Value', [])),
            "events_structure": {}
        }
        
        if data.get('Value'):
            sample_event = data['Value'][0]
            analysis["events_structure"] = {
                "main_fields": {
                    "I": "Event ID",
                    "N": "Event Number",
                    "T": "Type (50 = Virtual Sport)",
                    "SI": "Sport ID",
                    "SN": "Sport Name",
                    "L": "League Name",
                    "O1": "Team 1 Name",
                    "O2": "Team 2 Name",
                    "S": "Start Time (timestamp)",
                    "SC": "Score Information",
                    "ICY": "Is Currently Playing (live)"
                },
                "score_structure": {
                    "FS": "Final Score {S1: team1, S2: team2}",
                    "TS": "Time Seconds",
                    "SLS": "Status String"
                },
                "odds_structure": {
                    "E": "Main odds array (T: type, C: coefficient, CV: coefficient value, P: parameter)",
                    "AE": "Additional odds with handicaps (G: group, ME: market events)"
                }
            }
        
        return analysis
    
    def extract_events(self, data: Dict) -> List[EventInfo]:
        """Extrait et structure les informations des événements"""
        events = []
        
        for event_data in data.get('Value', []):
            score_info = event_data.get('SC', {})
            final_score = score_info.get('FS', {})
            
            event = EventInfo(
                event_id=event_data.get('I', 0),
                sport_name=event_data.get('SN', 'Unknown'),
                league_name=event_data.get('L', 'Unknown'),
                team1=event_data.get('O1', 'Unknown'),
                team2=event_data.get('O2', 'Unknown'),
                start_time=event_data.get('S', 0),
                is_live=event_data.get('ICY', False),
                current_score={
                    'team1': final_score.get('S1', 0),
                    'team2': final_score.get('S2', 0)
                },
                odds=event_data.get('E', [])
            )
            events.append(event)
        
        return events
    
    def analyze_odds_patterns(self, data: Dict) -> Dict[str, Any]:
        """Analyse les patterns dans les cotes"""
        odds_analysis = {
            "total_odds_count": 0,
            "odds_by_type": {},
            "average_odds": {},
            "min_max_odds": {}
        }
        
        type_odds = {}
        
        for event in data.get('Value', []):
            for odd in event.get('E', []):
                odd_type = odd.get('T')
                odd_value = odd.get('C', 0)
                
                if odd_type not in type_odds:
                    type_odds[odd_type] = []
                type_odds[odd_type].append(odd_value)
                odds_analysis["total_odds_count"] += 1
        
        # Calculer les statistiques par type
        for type_code, values in type_odds.items():
            odds_analysis["odds_by_type"][type_code] = len(values)
            odds_analysis["average_odds"][type_code] = sum(values) / len(values)
            odds_analysis["min_max_odds"][type_code] = {
                "min": min(values),
                "max": max(values)
            }
        
        return odds_analysis
    
    def analyze_additional_odds(self, data: Dict) -> Dict[str, Any]:
        """Analyse les cotes additionnelles avec handicaps"""
        additional_odds = {
            "groups_found": set(),
            "total_markets": 0,
            "handicap_ranges": {}
        }
        
        for event in data.get('Value', []):
            for additional_group in event.get('AE', []):
                group_id = additional_group.get('G')
                if group_id not in additional_odds["handicap_ranges"]:
                    additional_odds["handicap_ranges"][group_id] = []
                
                additional_odds["groups_found"].add(group_id)
                additional_odds["total_markets"] += len(additional_group.get('ME', []))
                
                for market in additional_group.get('ME', []):
                    param = market.get('P')
                    if param is not None:
                        additional_odds["handicap_ranges"][group_id].append(param)
        
        # Convertir set en list pour la sérialisation
        additional_odds["groups_found"] = sorted(list(additional_odds["groups_found"]))
        
        return additional_odds
    
    def generate_full_report(self, data: Dict) -> str:
        """Génère un rapport complet d'analyse"""
        print("🔍 Génération du rapport d'analyse API 888starz...")
        print("=" * 80)
        
        # Analyser tous les aspects
        parameters = self.analyze_parameters()
        bet_types = self.analyze_bet_types(data)
        response_structure = self.analyze_response_structure(data)
        events = self.extract_events(data)
        odds_patterns = self.analyze_odds_patterns(data)
        additional_odds = self.analyze_additional_odds(data)
        
        # Générer le rapport
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ONE-DELUX-FAST - RAPPORT D'ANALYSE API                     ║
║                              SOLITAIRE HACK                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 MÉTADONNÉES DE RÉPONSE
{'─' * 80}
• Succès: {response_structure['metadata']['success']}
• Erreur: {response_structure['metadata']['error'] if response_structure['metadata']['error'] else 'Aucune'}
• Code erreur: {response_structure['metadata']['error_code']}
• Timestamp: {response_structure['metadata']['timestamp']}
• Nombre d'événements: {response_structure['events_count']}

🔧 PARAMÈTRES DE L'API
{'─' * 80}
"""
        for param in parameters:
            report += f"• {param.name:20s} = {param.value:10s} ({param.type:8s}) - {param.description}\n"
        
        report += f"""
🎯 TYPES DE PARIS DÉTECTÉS
{'─' * 80}
"""
        for bet_type in bet_types:
            report += f"• Type {bet_type.code:2d}: {bet_type.description:40s} (Ex: cote {bet_type.example_odds:.2f})\n"
        
        report += f"""
📈 ANALYSE DES COTES PRINCIPALES
{'─' * 80}
• Total des cotes analysées: {odds_patterns['total_odds_count']}
"""
        for type_code in sorted(odds_patterns['odds_by_type'].keys()):
            count = odds_patterns['odds_by_type'][type_code]
            avg = odds_patterns['average_odds'].get(type_code, 0)
            min_max = odds_patterns['min_max_odds'].get(type_code, {})
            report += f"• Type {type_code:2d}: {count:3d} cotes | Moy: {avg:.3f} | Min: {min_max.get('min', 0):.3f} | Max: {min_max.get('max', 0):.3f}\n"
        
        report += f"""
🔧 ANALYSE DES COTES ADDITIONNELLES (HANDICAPS)
{'─' * 80}
• Groupes de marchés trouvés: {additional_odds['groups_found']}
• Total des marchés additionnels: {additional_odds['total_markets']}
"""
        for group_id, ranges in additional_odds['handicap_ranges'].items():
            if ranges:
                report += f"• Groupe {group_id}: Handicaps de {min(ranges)} à {max(ranges)} ({len(ranges)} valeurs)\n"
        
        report += f"""
🏆 ÉVÉNEMENTS ACTUELS (TOP 10)
{'─' * 80}
"""
        for i, event in enumerate(events[:10], 1):
            status = "🔴 LIVE" if event.is_live else "⏰ À venir"
            score = f"{event.current_score['team1']}-{event.current_score['team2']}" if event.is_live else "N/A"
            report += f"{i}. {status} {event.team1} vs {event.team2}\n"
            report += f"   Ligue: {event.league_name} | Score: {score} | Sport: {event.sport_name}\n"
            report += f"   Cotes disponibles: {len(event.odds)} | Event ID: {event.event_id}\n\n"
        
        if len(events) > 10:
            report += f"... et {len(events) - 10} autres événements\n"
        
        report += f"""
🏗️ STRUCTURE DE DONNÉES
{'─' * 80}
Champs principaux par événement:
"""
        for field, description in response_structure['events_structure']['main_fields'].items():
            report += f"• {field:4s}: {description}\n"
        
        report += f"""
🔍 DÉTAILS STRUCTURE DES COTES
{'─' * 80}
Structure d'une cote individuelle:
• T: Type de pari (1-14)
• C: Cote (coefficient décimal)
• CV: Cote sous forme de chaîne
• P: Paramètre (handicap, buts, etc.)
• G: Groupe (pour les cotes additionnelles)

💡 RECOMMANDATIONS POUR ONE-DELUX-FAST
{'─' * 80}
1. MISE EN CACHE: Implémenter un système de cache avec TTL de 30-60 secondes
2. FILTRAGE: Utiliser les paramètres pour réduire la charge (sports, count)
3. ERROR HANDLING: Implémenter retry logic pour les échecs
4. DATA VALIDATION: Vérifier toujours 'Success' avant de traiter les données
5. TYPE DE PARIS PRÉFÉRENTIELS: Focus sur types 1,2,3,4 (1X2) et 9,10 (Over/Under)
6. HANDICAPS: Les groupes 2 (handicaps buts) et 17 (handicaps points) sont disponibles
7. LIVE BETTING: Utiliser le champ 'ICY' pour identifier les événements en direct

🎯 ARCHITECTURE SUGGÉRÉE POUR LA PLATEFORME
{'─' * 80}
• API Module: Gestion des requêtes et parsing des données
• Cache Layer: Redis ou mémoire locale pour les données fréquemment accédées
• Prediction Engine: Modèles ML basés sur l'historique des cotes et résultats
• Data Processor: Normalisation et enrichment des données
• Notification System: Alertes sur les opportunités de paris
• Database: Stockage de l'historique pour l'entraînement des modèles

╔══════════════════════════════════════════════════════════════════════════════╗
║                         ANALYSE TERMINÉE - SOLITAIRE HACK                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        return report


def main():
    """Fonction principale pour exécuter l'analyse"""
    analyzer = APIAnalyzer()
    
    # Charger les données depuis le fichier webfetch
    try:
        with open(r'C:\Users\HP\AppData\Local\Temp\devin.exe-overflows\cfea86f4\content.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            # Extraire le JSON du contenu (enlever la première ligne qui est le commentaire)
            json_start = content.find('{')
            json_data = content[json_start:]
            # Nettoyer les caractères de contrôle problématiques
            import re
            json_data = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_data)
            data = json.loads(json_data)
        print(f"✅ Données chargées et nettoyées depuis le fichier webfetch")
    except Exception as e:
        print(f"❌ Erreur lors du chargement des données: {e}")
        return
    
    report = analyzer.generate_full_report(data)
    
    # Sauvegarder le rapport dans un fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"api_analysis_report_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n📄 Rapport sauvegardé dans: {filename}")


if __name__ == "__main__":
    main()