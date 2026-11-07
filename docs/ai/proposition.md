# Format des propositions

En tête : la liste de tous les fichiers concernés. Puis, pour chaque fichier :

    ### Fichier : chemin/vers/le/fichier.ext
    ### Objectif : <changement>
    ### Raison : <pourquoi>

Diff unifié (```diff), 3 lignes de contexte minimum, numéros de ligne si possible, un bloc par fichier.

# Après validation
1. Rappeler ce qui a été modifié (fichiers + résumé).
2. Afficher le diff réellement appliqué (`git diff`).
3. Signaler tout écart avec la proposition validée.
4. Proposer les vérifications (build, tests) sans lancer celles qui ont un effet de bord.
