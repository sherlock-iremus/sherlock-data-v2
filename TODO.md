# TODO

## Corpus MG

✔ - Les D1 (les trucs chez Gallica) doivent être rattachés aux F2 des F5 dont ils sont la numérisation via `crm:P130`
✔ - Lier les F2 articles de la TEI à leurs F2 livraison via R5 (je crois que ces liens existent pour l'édition originale).
- Dire à Antoine de faire les index uniquement sur les liens entre F2
✔ - Je crois que des F2 articles TEI sont imbriqués dans des F2 livraisons physique

## Corpora iconographiques

✔ - dcterms:creator (= personne), pas created (= date)

### Fichier Excel 

**à voir ensemble : P14.1 in the role of?**  - Créer une colonne par contribution avec rôle + nom (UUID) (rôle renvoie à un vocabulaire contrôlé des domaines d'expertise/fonctions => sherlock/data)

### Collection 

✔ - Dire que la collection racine contient deux sous-collections (estampes et musique) 
✔ - Tisser les liens P106 entre collections et E36 
✔ - Quand ce n'est pas nécessaire, ne pas créer d'E41 derrière les P1 
✔ - P104 et P105 ne sont définis que sur la collection "mère" (les "filles" en héritent) 
✔ - Comment dire que plusieurs personnes participent à la création d'une entité chacune avec un rôle spécifique ? E7 -> P9 -> E7 spécifique

### Image 

✔ - Supprimer F2 sur les E36. Relier les E36 aux livraisons via P148 (OK car E36=>E73=>E89 et F2=>E73=>E89)
✔ - E36
    P106(E13)
        E36
            P106(E13)
                E36
                    P165(E13) + sherlock:sheP_position_du_texte_par_rapport_à_la_médaille
                        E33
                            P190(E13)
                                "bla bla bla"

    E13
    P140: E36
    P141: E33
    P177: P165
    sherlock:sheP_position_du_texte_par_rapport_à_la_médaille: <357a459f-4f27-4d46-b5ac-709a410bce04> ou <fc229531-0999-4499-ab0b-b45e18e8196f>

### Indexation

**attendre d'avoir transformé le vocabulaire d'indexation de Anne en ttl** 

- les P2 doivent être dans des E13
- tout sous-fragment identifié (médaille, ville, grelot…) donne lieu à ceci : E36 -> P106(E13) -> E36 -> P2(E13) -> E55 
- comment indexer les fragments d'images avec les entités du RAR ? => P138

### Relations

- Comment modéliser le fait qu'un E36 sert de modèle à un autre ? 
    - H1 : aller voir Linked Art ?
    - H2 : biblio sur LRM image + inspiration/modèle
    - On peut vouloir différencier :
        - Le chercheur ou la chercheuse constate une similarité, mais qui ne dit pas forcément que le peintre de B a vu A et s'en est inspiré (P130)
        - Le chercheur ou la chercheuse fait l'hypothèse que le peintre de B a vu A et s'en est inspiré
    - H3 : E7 -> P15 (was influenced by) -> E1 (dans cette hypothèse, on pose la question en dehors de LRM, ce qui est problématique car LRM définit des propriétés d'inspiration entre F1, à comparer avec F2 -> R2 -> F1)

### Titres

✔ - E13 -> P177:E55(-> dcterms:creator -> Anne)
      -> P141 -> "[Le Feu]"
✔ - Regrouper les E55 types de gestes scientifiques en un F34. -> data/icono.ttl
