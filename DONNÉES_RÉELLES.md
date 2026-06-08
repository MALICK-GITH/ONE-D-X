# 🎯 ONE-DELUX-FAST - Données Réelles Uniquement

## 📊 Configuration du Système

Ce système utilise **uniquement** les données réelles de l'API 888starz.bet. Aucune donnée de démonstration n'est utilisée.

---

## 🌐 API 888starz.bet

**URL de l'API:**
```
https://888starz.bet/service-api/LiveFeed/Get1x2_VZip?sports=85&count=40&lng=fr&gr=789&mode=4&country=96&partner=233&getEmpty=true&virtualSports=true&noFilterBlockEvent=true
```

**Paramètres:**
- `sports=85` - ID du sport (Football)
- `count=40` - Nombre d'événements à récupérer
- `lng=fr` - Langue (Français)
- `gr=789` - Group ID
- `mode=4` - Mode de l'API
- `country=96` - Code pays
- `partner=233` - ID partenaire

---

## 🔧 Modules du Système

### 1. API Client (`api_client.py`)
- Communique avec l'API 888starz.bet
- Gère les erreurs et les retries
- Parse les données JSON en objets Python
- Cache des réponses pour optimiser les performances

### 2. Data Manager (`data_manager.py`)
- Gestion du cache avec TTL
- Stockage dans une base de données locale
- Métriques de performance (hit rate, miss rate)

### 3. Prediction Engine (`prediction_engine.py`)
- Utilise les données réelles de l'API
- Modèles Machine Learning:
  - Random Forest pour vainqueur
  - Gradient Boosting pour Over/Under
- Feature extraction à partir des cotes réelles
- Gestion du fallback intelligent si modèle indisponible

---

## 🔄 Flux Complet avec Données Réelles

### Étape 1: Chargement des Événements
```
API 888starz → API Client → Flask Route → Frontend
```
- Récupération des événements depuis l'API
- Parsing et validation des données
- Mise en cache pour optimisation
- Affichage des ligues groupées par sport

### Étape 2: Filtrage par Ligue
```
API Events → Filtrage par ligue → Affichage matchs
```
- Sélection des matchs d'une ligue spécifique
- Tri par heure de début
- Affichage avec bouton "Détails"

### Étape 3: Génération des Prédictions
```
Événement → Feature Extraction → Modèle ML → Prédiction
```
- Extraction des caractéristiques (cotes, statistiques)
- Application du modèle ML approprié
- Calcul de la confiance
- Affichage du pronostic avec probabilités

---

## ⚠️ Gestion des Erreurs

### Si l'API échoue:
- **Message d'erreur clair** affiché à l'utilisateur
- **Logging détaillé** dans la console
- **Pas de données de démonstration** - l'utilisateur est informé du problème

### Si le modèle ML échoue:
- **Fallback intelligent** basé sur les cotes réelles
- **Utilisation des cotes favorites** comme indicateur
- **Confiance ajustée** en fonction de la disponibilité

---

## 🎯 Données Affichées

### Ligues:
- Nom de la ligue (ex: "Ligue 1 France", "Premier League")
- Sport (ex: "Football")
- Nombre de matchs disponibles
- Indicateur de matchs en direct

### Matchs:
- Équipes (domicile/extérieur)
- Heure de début
- Status (Live/À venir)
- Score actuel (si en direct)
- Équipe favorite (basée sur les cotes)
- Cotes disponibles

### Prédictions:
- Vainqueur prédit (avec nom de l'équipe)
- Confiance du système (en pourcentage)
- Probabilités détaillées
- Version du modèle utilisé

---

## 🚀 Lancement de l'Application

```bash
python app.py
```

Puis ouvrir: **http://localhost:5000**

---

## 📊 Métriques et Monitoring

### API Client:
- Nombre de requêtes totales
- Taux de succès
- Temps de réponse moyen
- Erreurs par type

### Cache:
- Hit rate
- Miss rate
- Taille du cache
- TTL configuré

### Prédictions:
- Nombre de prédictions générées
- Confiance moyenne
- Distribution des types de prédictions

---

## 🔍 Debugging

### Vérifier l'API:
```bash
curl "https://888starz.bet/service-api/LiveFeed/Get1x2_VZip?sports=85&count=40&lng=fr&gr=789&mode=4&country=96&partner=233&getEmpty=true&virtualSports=true&noFilterBlockEvent=true"
```

### Vérifier les logs:
- Console du navigateur (F12 → Console)
- Logs de l'application Flask
- Logs du module API Client

### Tester les routes:
- `GET /api/events` - Liste des événements
- `GET /api/predictions/<event_id>` - Prédictions pour un événement
- `GET /api/stats` - Statistiques du système

---

**Ce système utilise UNIQUEMENT les données réelles de l'API 888starz.bet.**

---

*SOLITAIRE HACK - Intégrité des Données*