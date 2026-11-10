# Atelier de code

Dashboard d'apprentissage : PHP POO, Doctrine, DTO, Architecture, DDD, React, Données & API, Next.js.

## Utiliser le dashboard

`index.html` est une page autonome. Ouvre-la dans un navigateur ou héberge-la où tu veux.

## Héberger le dashboard

Le plus simple :

- **Netlify Drop** : va sur https://app.netlify.com/drop et glisse le fichier `index.html` (ou ce dossier). Tu obtiens une URL publique en quelques secondes.
- **GitHub Pages** : crée un dépôt, mets `index.html` à la racine, puis Settings > Pages > Deploy from branch (`main`, dossier `/`).
- **Vercel** : `npx vercel` dans ce dossier.

### Ce qui change hors de claude.ai

| Fonction | Sur claude.ai | Hébergé ailleurs |
|---|---|---|
| Cours, quiz, TD, révisions | Oui | Oui |
| Progression | Sur ton compte (tous tes appareils) | Dans le navigateur (localStorage), par appareil |
| « Explique-moi autrement », correction des TD, génération de modules | Oui | Oui, avec ta clé API Anthropic (menu « Activer les boutons Claude ») |
| Import JSON de modules | Oui | Oui |

## Modifier le contenu

Le contenu est écrit en Python, un fichier par parcours :

- `c_php.py`, `c_doctrine.py`, `c_dto.py`, `c_arch.py`, `c_ddd.py`
- `c_react.py`, `c_data.py`, `c_next.py`

Chaque module suit la même structure (`M(...)` dans `common.py`) : objectif, problème, mécanisme en 4 étapes, points clés, pièges, exemple commenté, quiz, TD.

Pour régénérer la page après une modification :

```bash
python3 build.py   # produit index.html à partir de template.html + contenu
```

`build.py` vérifie aussi que chaque module est complet (index de bonne réponse valide, TD complet…).

Pour ajouter un parcours : crée `c_monparcours.py`, importe-le dans `build.py`, ajoute le parcours dans `TRACKS`.

## Boutons Claude hors de claude.ai

Sur GitHub Pages (ou tout autre hébergement), ouvre « Activer les boutons Claude » dans le menu et colle une clé API créée sur https://console.anthropic.com/settings/keys.

- La clé est stockée uniquement dans ton navigateur (localStorage), jamais dans le dépôt.
- Les appels partent directement de ton navigateur vers api.anthropic.com.
- L'API est facturée à l'usage, séparément de l'abonnement Claude : fixe une limite de dépense dans la console.
