# Convertepub

Application Windows pour convertir un fichier `.acsm` (Adobe Content Server Message) en EPUB sans DRM. Pensée pour les livres achetés chez **Fnac**, **Furet du Nord**, **Cultura**, **Decitre** et autres revendeurs français passant par le backend **TEA Ebook**.

Cas d'usage : tu achètes un livre en EPUB, ton revendeur t'envoie un `.acsm`, et ta liseuse (Kindle par exemple) n'est pas compatible avec le DRM Adobe ADEPT. Convertepub fait le pont — l'EPUB de sortie est lisible partout et envoyable à ta Kindle via Send-to-Kindle.

## Auteur

**Julien Gauthier** — <iam@juliengauthier.org> — <https://juliengauthier.org>

## Fonctionnalités

- Glisser-déposer un ou plusieurs `.acsm` dans la fenêtre
- Activation Adobe **anonyme** automatique (aucun compte à créer)
- Rotation automatique de l'activation si le device est saturé
- Mode CLI pour scripting (`--cli fichier.acsm --output out/`)
- Sortie EPUB standard, lisible dans Calibre, Sigil, Kobo, Kindle (via Send-to-Kindle)…

## Utilisation

### Mode graphique
```
python -m src.main
```

### Mode ligne de commande
```
python -m src.main --cli mon_livre.acsm --output ./out
```

### Première activation Adobe (optionnel, pour tester la connexion)
```
python -m src.main --setup-only
```

## Pipeline

```
livre.acsm  →  [fulfillment Adobe ADEPT]  →  livre.epub (DRM)  →  [retrait DRM]  →  livre.epub propre
```

## Pile technique

- **Python 3.11+** — pas de binaire externe, 100 % Python
- **PySide6** pour la GUI
- **acsm-calibre-plugin** (extrait) pour le fulfillment ACSM
- **DeDRM_tools / ineptepub** (extrait) pour le retrait DRM ADEPT

## Stockage local

- `%LOCALAPPDATA%\Convertepub\activations\` — clés d'activation Adobe (une par slot, rotation transparente)
- `%LOCALAPPDATA%\Convertepub\logs\` — logs applicatifs
- `%LOCALAPPDATA%\Convertepub\settings.json` — préférences (dossier de sortie…)

## Légalité

Cette application est destinée à l'**interopérabilité d'œuvres acquises légalement** avec un matériel non compatible Adobe DRM — un cas d'usage explicitement couvert par l'article L331-5 du Code de la propriété intellectuelle français. Elle ne contourne pas la mesure technique pour un usage frauduleux : tu dois posséder une licence légitime du livre.

## Crédits

Le cœur ADEPT de cette application est tiré de deux projets sans lesquels rien de tout cela ne serait possible :

- **[acsm-calibre-plugin](https://github.com/Leseratte10/acsm-calibre-plugin)** de Leseratte10 — réimplémentation Python du protocole de fulfillment Adobe
- **[DeDRM_tools / noDRM](https://github.com/noDRM/DeDRM_tools)** d'Apprentice Alf, Apprentice Harper et i♥cabbages — module `ineptepub` pour le retrait du DRM ADEPT
- **[libgourou](https://forge.soutade.fr/soutade/libgourou)** de Grégory Soutadé — recherche d'origine sur le protocole ADEPT

Merci à eux.

## Licence

GPL-3.0-or-later. Voir [`LICENSE`](LICENSE).

Cette application incorpore du code GPL-3.0 des projets cités ci-dessus, donc l'application entière est sous la même licence. Toute redistribution doit publier les sources.
