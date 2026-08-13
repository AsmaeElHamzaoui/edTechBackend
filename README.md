# EdTech Backend Platform

Backend complet pour une plateforme EdTech innovante, basée sur Django, Django REST Framework, et une architecture multi-agents IA (Gemini).

## 🚀 Fonctionnalités Principales

- **Authentification & Gestion des Utilisateurs** : Inscription, JWT, rôles (APPRENANT, ADMINISTRATEUR).
- **Gestion Documentaire** : Upload PDF, traitement asynchrone (Celery + Redis), extraction de texte, OCR fallback (Tesseract), chunking par page.
- **RAG & Vector Storage** : Création d'embeddings et stockage local via ChromaDB.
- **Système Multi-Agents IA** :
  - *OrchestratorAgent* : Classification d'intentions et routage.
  - *RagAgent* : Recherche documentaire avec citations (numéros de page).
  - *PedagogicalAgent* : Vulgarisation de concepts selon 3 niveaux de difficulté.
  - *QuizAgent* : Génération automatique de quiz (QCM, Vrai/Faux, Ouvert).
  - *EvaluationAgent* : Évaluation sémantique des réponses ouvertes.
  - *SummaryAgent* : Génération de résumés et fiches de synthèse.
  - *NotificationAgent* : Centralisation des alertes et emails.
- **Chat avec Streaming (SSE)** : Interface conversationnelle avec l'IA, réponse token par token (Server-Sent Events).
- **Analytics & Progression** : Dashboard de progression, concepts les plus faibles, recommandations de révisions, export CSV/PDF.
- **Stockage Hybride** : Support du stockage local ou Object Storage (MinIO/S3).
- **Quotas & Sécurité** : Limite du nombre de documents et d'espace de stockage par apprenant, isolation des données, log d'audit admin.
- **Documentation API** : Auto-générée via Swagger (drf-spectacular).

## 🛠 Pré-requis

- **Python** 3.11+
- **Redis** (Broker Celery)
- **PostgreSQL** (Optionnel, par défaut SQLite)
- **Tesseract OCR** & **Poppler** (Pour l'extraction PDF avancée)
- **Docker & Docker Compose** (Pour le déploiement)

### Installation locale (Développement)

1. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   .\venv\Scripts\activate   # Sur Windows
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer les variables d'environnement**
   Copiez `.env.example` vers `.env` et remplissez les valeurs (notamment `GEMINI_API_KEY`).

4. **Migrations & Exécution**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. **Lancer le worker Celery (Dans un nouveau terminal)**
   ```bash
   celery -A core worker -l info
   ```

### 🐳 Lancement via Docker (Recommandé)

Le projet inclut un fichier `docker-compose.yml` qui provisionne automatiquement :
- La base de données PostgreSQL
- Le serveur Redis
- Le serveur MinIO (S3)
- L'application Django (gunicorn)
- Le worker Celery

```bash
docker-compose up --build -d
```

L'API sera accessible sur `http://localhost:8000`.

## 📚 Documentation de l'API

Une fois le serveur lancé, accédez à la documentation interactive :
- **Swagger UI** : `http://localhost:8000/api/docs/`
- **ReDoc** : `http://localhost:8000/api/redoc/`

## ⚙️ Configuration S3 / MinIO

Si vous souhaitez stocker les documents sur S3 ou MinIO, modifiez le `.env` :
```env
USE_S3=True
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=edtech-bucket
AWS_S3_ENDPOINT_URL=http://localhost:9000
```
Pensez à créer le bucket manuellement dans l'interface MinIO (http://localhost:9001) avant le premier upload.
