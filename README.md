# TechEvents · Gestionnaire d'Événements et de Formations Tech

Application web Django (frontend et backend) qui centralise, planifie et suit la participation à des activités tech : conférences, ateliers pratiques et certifications.

Mini-projet Django/Python, réalisé par **Mohammed Hamdani** et Ilyass Boukaya.

---

## Fonctionnalités

- **Liste des événements** avec le titre, la date, le lieu, les places et le **statut** : _À venir_, _Terminé_, _Inscrit_ (et _Complet_).
- **Filtres** par statut (Tous, À venir, Terminés, Mes inscriptions) et par **catégorie** (Intelligence Artificielle, DevOps, Cybersécurité…).
- **Inscription / désinscription** aux événements, avec gestion des places disponibles.
- **Création, modification et suppression** d'événements, avec des règles de validation strictes :
  - date dans le passé refusée ;
  - capacité d'accueil nulle ou négative refusée ;
  - capacité inférieure au nombre d'inscrits refusée.
- **Comptes utilisateurs** : création de compte, connexion, déconnexion.
- **Permissions** : seul l'organisateur d'un événement peut le modifier ou le supprimer ; la création de catégories exige une permission Django.
- **Tableau de bord personnel** : inscriptions à venir, historique de participation, événements organisés.
- Interface d'**administration** Django (`/admin/`).

## Technologies

- Python 3.10 ou plus récent
- Django 5.2 (version LTS, support long terme)
- SQLite (base de données par défaut de Django)
- HTML et CSS, sans dépendance externe (le site fonctionne même hors ligne)

---

## Installation et lancement

### 1. Récupérer le projet

```bash
git clone https://github.com/ilyassdev27/eventsProject.git
cd eventsProject
```

### 2. Créer et activer l'environnement virtuel

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Créer la base de données et lancer le serveur

```bash
python manage.py migrate
python manage.py charger_demo      # (facultatif) données de démonstration
python manage.py runserver
```

Le site est alors accessible sur **http://127.0.0.1:8000/**.

### Comptes de démonstration

La commande `charger_demo` crée ces comptes. Ils servent uniquement en développement.

| Utilisateur | Mot de passe | Rôle                                                          |
| ----------- | ------------ | ------------------------------------------------------------- |
| `admin`     | `admin12345` | superutilisateur : accès à `/admin/`, création de catégories  |
| `demo`      | `demo12345`  | utilisateur avec des inscriptions et des événements organisés |
| `sara`      | `demo12345`  | autre utilisateur (pour tester les permissions)               |

Pour créer votre propre administrateur : `python manage.py createsuperuser`.

### Lancer les tests

```bash
python manage.py test
```

---

## Architecture

Le projet `eventsProject` coordonne deux applications indépendantes :

| Application | Rôle                                                                      |
| ----------- | ------------------------------------------------------------------------- |
| `events`    | Logique métier : catégories, événements, inscriptions, tableau de bord    |
| `accounts`  | Authentification et sécurité : connexion, déconnexion, création de compte |

```
eventsProject/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── eventsProject/                # configuration du projet
│   ├── settings.py
│   └── urls.py                   # inclut events.urls et accounts.urls
├── events/                       # application métier
│   ├── models.py                 # Categorie, Evenement, Inscription
│   ├── forms.py                  # EvenementForm, CategorieForm, FiltreEvenementsForm
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   ├── migrations/
│   ├── management/commands/charger_demo.py
│   └── templates/events/
├── accounts/                     # authentification
│   ├── forms.py                  # CreationCompteForm
│   ├── views.py                  # ConnexionView, DeconnexionView, creer_compte
│   ├── urls.py
│   ├── tests.py
│   └── templates/accounts/
├── templates/                    # templates globaux, partagés par les deux applications
│   ├── base.html                 # squelette commun (navigation, messages, pied de page)
│   ├── formulaire.html           # page de formulaire générique
│   ├── 403.html · 404.html
│   └── partials/                 # morceaux réutilisés avec {% include %}
└── static/css/style.css
```

### Modèle de données

```
Categorie 1 ───────── N Evenement N ───────── N User
                          │         (via Inscription)
                          │ N
                          │
                          1 User (organisateur)
```

- **Categorie** : `nom` unique (`unique=True`).
- **Evenement** : `titre`, `type_evenement` (choix), `date`, `lieu`, `capacite`, `description`.
  - `categorie` : `ForeignKey` vers `Categorie` avec `on_delete=CASCADE` (une catégorie supprimée n'a plus de sens, ses événements sont supprimés avec elle).
  - `organisateur` : `ForeignKey` vers `User`.
  - `participants` : `ManyToManyField` vers `User` à travers le modèle `Inscription`.
- **Inscription** : table intermédiaire `utilisateur` ↔ `evenement`, avec la date d'inscription.

### Choix de conception

- **Le statut n'est pas stocké en base, il est calculé.** « À venir » ou « Terminé » dépend de la date (`Evenement.est_termine`) : aucun statut ne peut devenir faux avec le temps. « Inscrit » dépend de l'utilisateur connecté, pas de l'événement : il est calculé à partir de la table `Inscription`.
- **La capacité est stockée, les places restantes sont calculées** (`capacite - nombre d'inscrits`). Un événement plein a 0 place restante sans que la capacité passe à 0.
- **Double protection des données** : les formulaires valident les saisies et affichent des messages clairs, et la base de données garantit les règles avec des contraintes (`CheckConstraint`, `UniqueConstraint`, `unique=True`).

---

## Correspondance avec les exigences du projet

### Points essentiels

| Exigence         | Réalisation                                                                                                                                                                                                                                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Architecture** | Deux applications séparées (`events` pour le métier, `accounts` pour l'authentification) ; la configuration est dans `eventsProject/`.                                                                                                                                               |
| **Modèles**      | `events/models.py` : relations One-to-Many (`ForeignKey`) et Many-to-Many (`through="Inscription"`) ; contraintes `unique=True`, `MinValueValidator(1)`, `CheckConstraint` (capacité ≥ 1), `UniqueConstraint` (une seule inscription par utilisateur et par événement).              |
| **Migrations**   | Migration initiale `events/migrations/0001_initial.py`, appliquée avec `migrate`. Chaque modification de `models.py` passe par `makemigrations` puis `migrate`.                                                                                                                      |
| **URLs**         | `eventsProject/urls.py` utilise `include()` ; chaque application a son `urls.py` avec un `app_name` (ex. : `{% url 'events:detail' evenement.pk %}`).                                                                                                                                |
| **Views**        | `events/views.py` et `accounts/views.py` : des vues courtes. Les requêtes réutilisables sont dans `EvenementQuerySet` (`a_venir()`, `termines()`…) et la validation dans `forms.py`.                                                                                                 |
| **Templates**    | Héritage : `base.html` → `formulaire.html` → `login.html` / `creer_compte.html` (deux niveaux). Réutilisation avec `{% include %}` : `_carte_evenement.html` (liste et tableau de bord), `_badges_statut.html`, `_champ.html`, `_formulaire.html`, `_navbar.html`, `_messages.html`. |

### Bonus

| Exigence          | Réalisation                                                                                                                                                                                                                                                                                                                                                      |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Forms**         | `EvenementForm` (`clean_date` refuse les dates passées, `clean_capacite`, capacité minimale 1), `CategorieForm` (`clean_nom` : doublons sans tenir compte des majuscules), `CreationCompteForm` (e-mail obligatoire et unique), `FiltreEvenementsForm` (valide les paramètres de l'URL).                                                                         |
| **Sécurité**      | `@login_required` sur la création, la modification, la suppression et l'inscription ; seul l'organisateur peut modifier ou supprimer (erreur 403 sinon) ; `@permission_required` pour créer une catégorie ; `@require_POST` pour les actions ; jeton CSRF sur tous les formulaires ; déconnexion en POST ; `SECRET_KEY` lue depuis une variable d'environnement. |
| **Git**           | Dépôt Git avec un `.gitignore` qui exclut `venv/`, `__pycache__/`, `db.sqlite3` et `.env`.                                                                                                                                                                                                                                                                       |
| **Environnement** | `venv` et `requirements.txt`.                                                                                                                                                                                                                                                                                                                                    |
| **Documentation** | Ce fichier `README.md`.                                                                                                                                                                                                                                                                                                                                          |
| **Qualité**       | Noms explicites en français, docstrings et commentaires, tests automatisés (`python manage.py test`).                                                                                                                                                                                                                                                            |

---

## Commandes utiles

| Commande                           | Rôle                                                      |
| ---------------------------------- | --------------------------------------------------------- |
| `python manage.py makemigrations`  | Crée les migrations après une modification de `models.py` |
| `python manage.py migrate`         | Applique les migrations à la base de données              |
| `python manage.py charger_demo`    | Charge les données de démonstration                       |
| `python manage.py createsuperuser` | Crée un compte administrateur                             |
| `python manage.py test`            | Lance les tests                                           |
| `pip freeze > requirements.txt`    | Fige les versions exactes des dépendances installées      |
