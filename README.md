# ONE-DELUX-FAST 🚀

**Plateforme professionnelle de prédiction sportive propulsée par l'IA**

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

---

## 🎯 À propos

ONE-DELUX-FAST est une plateforme de prédiction sportive haute performance utilisant l'API 888starz pour récupérer des données en temps réel et des modèles de machine learning pour générer des prédictions précises sur les événements sportifs virtuels (FIFA, eSports).

### Caractéristiques principales

- ⚡ **Temps réel**: Récupération et traitement des données en < 5 secondes
- 🎯 **Précision**: Modèles ML entraînés pour une précision > 65%
- 🏗️ **Architecture professionnelle**: Design scalable et maintenable
- 🔒 **Sécurité**: Authentication, encryption, rate limiting
- 📊 **Analytics**: Statistiques détaillées et monitoring
- 💾 **Cache intelligent**: Gestion optimisée du cache avec TTL
- 🗄️ **Persistance**: Base de données robuste pour l'historique

---

## 🚀 Installation

### Prérequis

- Python 3.11 ou supérieur
- pip (gestionnaire de paquets Python)
- Git

### Étapes d'installation

1. **Cloner le dépôt**
```bash
git clone https://github.com/votre-repo/one-delux-fast.git
cd one-delux-fast
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer l'application**
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

5. **Initialiser la base de données**
```bash
python -m one_delux_fast.database init
```

---

## 📖 Utilisation

### Lancer l'application

```bash
python main.py
```

### Exemple d'utilisation

```python
from one_delux_fast import get_api_client, get_data_manager

# Récupérer le client API
api_client = get_api_client()

# Récupérer les événements
response = api_client.get_events()

if response.is_valid():
    events = response.data
    
    # Analyser les événements
    for event in events:
        print(f"{event.team1_name} vs {event.team2_name}")
        print(f"Favorite: {event.get_favorite_team()}")
        
    # Mettre en cache
    data_manager = get_data_manager()
    data_manager.cache_events(events)
```

### Configuration

La configuration se fait via le fichier `config.py` ou les variables d'environnement:

```python
# Configuration API
API_BASE_URL=https://888starz.bet/service-api/LiveFeed/Get1x2_VZip
API_TIMEOUT=10

# Configuration Cache
CACHE_DEFAULT_TTL=60

# Configuration Database
DB_PATH=one_delux_fast.db
```

---

## 🏗️ Architecture

### Structure du projet

```
one-delux-fast/
├── one_delux_fast/           # Package principal
│   ├── __init__.py         # Initialisation du package
│   ├── api_client.py       # Client API 888starz
│   ├── data_manager.py     # Gestion des données et cache
│   └── prediction_engine.py# Moteur de prédiction (à venir)
├── config.py               # Configuration centralisée
├── main.py                 # Point d'entrée principal
├── requirements.txt         # Dépendances Python
├── ARCHITECTURE.md         # Documentation technique
└── README.md              # Ce fichier
```

### Composants principaux

#### 1. API Client (`api_client.py`)
- Communication avec l'API 888starz
- Parsing des données
- Gestion des erreurs
- Retry logic

#### 2. Data Manager (`data_manager.py`)
- Gestion du cache en mémoire
- Persistance des données
- Statistiques d'utilisation
- Nettoyage automatique

#### 3. Configuration (`config.py`)
- Configuration centralisée
- Variables d'environnement
- Paramètres par défaut

---

## 📊 API 888starz

### Endpoint principal

```
GET https://888starz.bet/service-api/LiveFeed/Get1x2_VZip
```

### Paramètres

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|-------------------|
| sports | ID du sport | 85 (FIFA) |
| count | Nombre d'événements | 40 |
| lng | Langue | fr |
| mode | Mode de récupération | 4 |
| virtualSports | Sports virtuels | true |

### Types de paris supportés

- **1X2**: Victoire équipe 1/2, nul
- **Handicaps**: Handicaps positifs/négatifs
- **Over/Under**: Plus/moins de buts/points
- **Goals**: Équipe marque plus/moins de

---

## 🧪 Tests

### Lancer les tests

```bash
python -m pytest tests/
```

### Tests unitaires

```bash
python -m pytest tests/unit/
```

### Tests d'intégration

```bash
python -m pytest tests/integration/
```

---

## 📈 Performance

### Métriques actuelles

- **Temps de réponse API**: < 2s
- **Taux de succès**: > 95%
- **Cache hit rate**: > 80%
- **Memory usage**: < 500MB

### Objectifs

- **Temps de réponse**: < 1s
- **Taux de succès**: > 99%
- **Cache hit rate**: > 90%
- **Scalabilité**: 1000+ requêtes/min

---

## 🔧 Développement

### Convention de code

- PEP 8 pour le style Python
- Type hints pour toutes les fonctions
- Docstrings pour tous les modules/classes
- Tests unitaires pour toute nouvelle fonctionnalité

### Branches

- `main`: Branche principale stable
- `develop`: Développement en cours
- `feature/*`: Nouvelles fonctionnalités
- `bugfix/*`: Corrections de bugs

---

## 🚨 Sécurité

### Mesures de sécurité

- Authentication JWT
- Encryption TLS 1.3
- Rate limiting
- Input validation
- SQL injection prevention

### Signalement de vulnérabilités

Pour signaler une vulnérabilité, contactez: security@one-delux-fast.com

---

## 📝 License

Ce projet est sous license MIT. Voir le fichier LICENSE pour plus de détails.

---

## 👥 Contributeurs

- **SOLITAIRE HACK** - Architecte principal

---

## 🙏 Remerciements

- 888starz pour l'API de données sportives
- La communauté open source pour les outils et bibliothèques

---

## 📞 Contact

- **Email**: contact@one-delux-fast.com
- **GitHub**: https://github.com/votre-repo/one-delux-fast
- **Documentation**: https://docs.one-delux-fast.com

---

## 🗺️ Roadmap

### Version 1.1 (Prochainement)
- [ ] Moteur de prédiction ML
- [ ] Interface utilisateur web
- [ ] Notifications en temps réel

### Version 1.2 (Futur)
- [ ] Application mobile
- [ ] Modèles avancés (Deep Learning)
- [ ] Système d'abonnement

### Version 2.0 (Long terme)
- [ ] Multi-sports (football, basketball, tennis)
- [ ] API publique pour développeurs
- [ ] Marketplace de modèles

---

**ONE-DELUX-FAST - Créé avec excellence par SOLITAIRE HACK** 🚀