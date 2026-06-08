"""
ONE-DELUX-FAST - Analyse simplifiée de l'API 888starz
SOLITAIRE HACK - Analyse professionnelle et rigoureuse
"""

import requests
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
    
    def __init__(self, base_url: str = "https://888starz.bet/service-api/LiveFeed/Get1x2_VZip"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
        
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
                    "SC": "Score Information"
                },
                "score_structure": {
                    "FS": "Final Score {S1: team1, S2: team2}",
                    "TS": "Time Seconds",
                    "SLS": "Status String"
                },
                "odds_structure": {
                    "E": "Main odds array",
                    "AE": "Additional odds with handicaps"
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
📈 ANALYSE DES COTES
{'─' * 80}
• Total des cotes analysées: {odds_patterns['total_odds_count']}
"""
        for type_code in sorted(odds_patterns['odds_by_type'].keys()):
            count = odds_patterns['odds_by_type'][type_code]
            avg = odds_patterns['average_odds'].get(type_code, 0)
            min_max = odds_patterns['min_max_odds'].get(type_code, {})
            report += f"• Type {type_code:2d}: {count:3d} cotes | Moy: {avg:.3f} | Min: {min_max.get('min', 0):.3f} | Max: {min_max.get('max', 0):.3f}\n"
        
        report += f"""
🏆 ÉVÉNEMENTS ACTUELS
{'─' * 80}
"""
        for i, event in enumerate(events[:5], 1):
            status = "🔴 LIVE" if event.is_live else "⏰ À venir"
            score = f"{event.current_score['team1']}-{event.current_score['team2']}" if event.is_live else "N/A"
            report += f"{i}. {status} {event.team1} vs {event.team2}\n"
            report += f"   Ligue: {event.league_name} | Score: {score} | Sport: {event.sport_name}\n"
            report += f"   Cotes disponibles: {len(event.odds)}\n\n"
        
        if len(events) > 5:
            report += f"... et {len(events) - 5} autres événements\n"
        
        report += f"""
🏗️ STRUCTURE DE DONNÉES
{'─' * 80}
Champs principaux par événement:
"""
        for field, description in response_structure['events_structure']['main_fields'].items():
            report += f"• {field:4s}: {description}\n"
        
        report += f"""
💡 RECOMMANDATIONS POUR ONE-DELUX-FAST
{'─' * 80}
1. MISE EN CACHE: Implémenter un système de cache avec TTL de 30-60 secondes
2. FILTRAGE: Utiliser les paramètres pour réduire la charge (sports, count)
3. ERROR HANDLING: Implement retry logic pour les échecs
4. DATA VALIDATION: Vérifier toujours 'Success' avant de traiter les données
5. TYPE DE PARIS PRÉFÉRENTIELS: Focus sur types 1,2,3,4 (1X2) et 9,10 (Over/Under)

╔══════════════════════════════════════════════════════════════════════════════╗
║                         ANALYSE TERMINÉE - SOLITAIRE HACK                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        return report


def main():
    """Fonction principale pour exécuter l'analyse"""
    analyzer = APIAnalyzer()
    
    # Récupérer les données
    params = {
        'sports': '85',
        'count': '40',
        'lng': 'fr',
        'gr': '789',
        'mode': '4',
        'country': '96',
        'partner': '233',
        'getEmpty': 'true',
        'virtualSports': 'true',
        'noFilterBlockEvent': 'true'
    }
    
    print("📡 Récupération des données de l'API...")
    try:
        response = analyzer.session.get(analyzer.base_url, params=params, timeout=10)
        data = response.json()
        print(f"✅ Données récupérées avec succès (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des données: {e}")
        return
    
    report = analyzer.generate_full_report(data)
    
    # Sauvegarder le rapport dans un fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"api_analysis_report_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n📄 Rapport sauvegardé dans: {filename}")
    
    # Sauvegarder les données brutes pour analyse ultérieure
    raw_filename = f"api_raw_data_{timestamp}.json"
    with open(raw_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Données brutes sauvegardées dans: {raw_filename}")


if __name__ == "__main__":
    main()