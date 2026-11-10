# Atelier de code

Un tableau de bord pour apprendre le développement web en comprenant comment les choses fonctionnent.

**En ligne : https://fausatu.github.io/atelier-de-code/**

## Ce qu'il permet

- Suivre des cours courts : chaque module explique le mécanisme, montre un exemple commenté, propose un quiz et un TD pratique.
- Réviser au bon moment grâce à la répétition espacée.
- Suivre sa progression : tableau de bord graphique, roadmap par parcours, calendrier d'activité.
- Ajouter ses propres modules.

## Parcours

- **Back** : PHP orienté objet → Doctrine → DTO → Architecture → DDD
- **Front** : React → Données & API → Next.js
- **Outils** : Git & GitHub

## Architecture

```
atelier-de-code/
├── index.html      # page générée, publiée sur GitHub Pages
├── template.html   # interface (HTML, CSS, JavaScript)
├── build.py        # assemble l'interface et le contenu
├── common.py       # structure d'un module
└── c_*.py          # contenu, un fichier par parcours
```

Le contenu des modules est écrit dans les fichiers `c_*.py`. `build.py` les assemble avec `template.html` pour produire `index.html`, une page autonome, sans serveur ni dépendance à installer.

## Lancer en local

Ouvrir `index.html` dans un navigateur.

Après une modification du contenu :

```bash
python3 build.py
```
