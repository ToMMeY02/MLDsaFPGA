# ML-DSA (FIPS 204) : benchmark FPGA du design ML-DSA-OSH

**Design** : [KULeuven-COSIC/ML-DSA-OSH](https://github.com/KULeuven-COSIC/ML-DSA-OSH) (Verilog/VHDL, licence MIT ; une partie des fichiers vient de GMU CERG, Apache-2.0)  
**Outils** : Vivado 2024.2, xsim  
**Composant utilisé** : `xczu5ev-sfvc784-2-e` (Zynq UltraScale+, grade −2). **Ce n'est pas la ZCU104 demandée** (voir §0).  
Tous les chiffres sont extraits des rapports d'outils (`reports/raw/`) par `scripts/gen_report.py`.

## 0. Écarts par rapport au plan

- **Composant** : `xczu7ev-2ffvc1156-2-e` (ZCU104) et `xczu7ev-ffvc1156-2-e` sont **absents** de cette installation Vivado (seuls `xczu3eg` et `xczu5ev` sont installés ; `get_parts *zu7ev*` renvoie vide). Tout a été fait sur le ZU5EV (117 120 LUT, 234 240 FF, 144 BRAM36, 1 248 DSP), même famille UltraScale+ et même grade de vitesse. Les fréquences et ressources ne sont donc pas celles d'une ZU7EV.
- **Une seule synthèse** : le design choisit le niveau (`sec_lvl` = 2, 3, 5) et l'opération (`mode`) à l'exécution sur le même matériel (cas de la note 3 du plan). Les ressources et la fréquence sont donc **identiques pour ML-DSA-44/65/87 et pour KeyGen/Sign/Verify** : il n'existe pas de chiffres de LUT/FF/BRAM/DSP par opération ou par niveau, seulement des latences différentes.
- **Pas de HLS** dans ce dépôt (RTL pur, 49 fichiers Verilog/VHDL) : les latences viennent donc de la simulation RTL avec les testbenchs fournis, pas d'une co-simulation HLS.
- **Pas de scripts TCL dans le dépôt** : `ML-DSA-OSH/scripts/synth_mldsa.tcl` est un script écrit pour cette étude (j'ai écrit le mien plutôt que celui du plan, car il y avait deux difficultés : une synthèse unique suffit, et il fallait déclarer `zetas.txt` comme fichier d'initialisation mémoire).
- **Contrainte d'horloge** : 4.35 ns (≈ 230 MHz, la fréquence indiquée pour l'article dans le plan), en mode hors-contexte (out-of-context).

## 1. Ressources (un seul matériel pour les 3 niveaux et les 3 opérations)

| Étape | LUT | FF | BRAM36 | DSP | URAM |
|---|---:|---:|---:|---:|---:|
| Après synthèse | 56,979 | 29,248 | 29 | 16 | 0 |
| **Après placement et routage** | **56,475** (48.2 %) | **29,292** (12.5 %) | **29** (20.1 %) | **16** (1.3 %) | 0 |

Puissance estimée par Vivado : 3.19 W (activité par défaut : indicatif, pas une mesure).

Principaux blocs (post-route, LUT / FF / BRAM36 / DSP) :

| Instance | Module | LUT | FF | BRAM36 | DSP |
|---|---|---:|---:|---:|---:|
| genblk1[2].KECCAK | keccak_top_6 | 6,886 | 4,467 | 0 | 0 |
| HINT_APPLIER | usehint | 6,741 | 2,821 | 0 | 0 |
| genblk1[1].KECCAK | keccak_top_5 | 6,034 | 4,460 | 0 | 0 |
| genblk1[0].KECCAK | keccak_top | 5,952 | 4,467 | 0 | 0 |
| genblk2[1].OPERATOR | operation_module_7 | 5,191 | 3,222 | 0 | 8 |
| genblk2[0].OPERATOR | operation_module | 5,095 | 3,222 | 0 | 8 |
| DECODER | decoder | 2,618 | 244 | 0 | 0 |
| ENCODER | encoder | 2,593 | 462 | 0 | 0 |

## 2. Fréquence

| Contrainte | WNS | WHS | Contraintes respectées | Fmax estimée |
|---|---:|---:|---|---:|
| 4.35 ns (230 MHz) | +0.019 ns | +0.021 ns | oui | 230.9 MHz |

La Fmax est `1000 / (contrainte − WNS)` pour **cette** contrainte et cette exécution. Avec une contrainte plus sévère, l'outil pourrait aller un peu plus haut : je n'ai pas cherché la fréquence maximale.

## 3. Latence (cycles, simulation RTL avec les testbenchs du dépôt)

Chaque testbench envoie les entrées et lit les sorties du `combined_top`, **compare à des vecteurs de test NIST (ACVP)**, et affiche le nombre de cycles entre le démarrage et la fin d'une opération. Résultat de la comparaison : **0 erreur** sur tous les vecteurs (KeyGen 75 vecteurs, Sign 45, Verify 45 ; messages `WRONG` : KeyGen 0, Sign 0, Verify 0).

| Niveau | Opération | Vecteurs | Cycles min | Cycles moyen | Cycles max | Latence moyenne @230 MHz (µs) |
|---|---|---:|---:|---:|---:|---:|
| ML-DSA-44 | KeyGen | 25 | 4,865 | 4,872 | 4,878 | 21.2 |
| ML-DSA-44 | Sign | 15 | 10,970 | 25,081 | 53,034 | 109.0 |
| ML-DSA-44 | Verify | 15 | 6,584 | 6,634 | 6,908 | 28.8 |
| ML-DSA-65 | KeyGen | 25 | 8,287 | 8,292 | 8,300 | 36.1 |
| ML-DSA-65 | Sign | 15 | 16,179 | 34,262 | 97,833 | 149.0 |
| ML-DSA-65 | Verify | 15 | 9,730 | 9,730 | 9,730 | 42.3 |
| ML-DSA-87 | KeyGen | 25 | 14,025 | 14,033 | 14,045 | 61.0 |
| ML-DSA-87 | Sign | 15 | 25,672 | 54,222 | 108,916 | 235.7 |
| ML-DSA-87 | Verify | 15 | 14,632 | 14,643 | 14,655 | 63.7 |

Notes :
- **Sign varie fortement d'un vecteur à l'autre** (rejet probabiliste) : par exemple ML-DSA-87 de 25,672 à 108,916 cycles. La moyenne sur 15 vecteurs est donc une estimation grossière ; KeyGen et Verify sont quasi constants.
- Les cycles incluent le transfert des données par le testbench (bus de 64 bits, côté testbench toujours prêt), pas seulement le calcul.
- La conversion en µs utilise 230 MHz (la contrainte respectée) ; à la Fmax estimée de 231 MHz les valeurs seraient pratiquement les mêmes.

## 4. Comparaison avec les valeurs de l'article indiquées dans votre plan

Ces valeurs viennent de votre plan (« DATE 2026, UltraScale+ à 230 MHz ») ; **je ne les ai pas vérifiées** contre l'article.

| | LUT | FF | BRAM | DSP | Sign-44 | Sign-65 | Sign-87 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Plan (article) | 54,942 | 29,309 | 29 | 16 | 106 µs | 143 µs | 160 µs |
| Cette mesure (ZU5EV, post-route, latence moyenne) | 56,475 | 29,292 | 29 | 16 | 109.0 µs | 149.0 µs | 235.7 µs |

Les ressources concordent bien (BRAM et DSP identiques, LUT +2,8 %, FF −0,1 %). Pour la latence de Sign, ML-DSA-44 et ML-DSA-65 concordent à quelques pour cent, mais **ML-DSA-87 est nettement plus lent dans ma mesure (~236 µs contre 160 µs)**. Je ne sais pas expliquer l'écart : la latence de Sign dépend du nombre d'essais de rejet (moyenne sur 15 vecteurs seulement) et je ne connais pas la méthode de mesure de l'article.

## 5. Modifications apportées

- **Aucun fichier original du dépôt n'a été modifié.**
- Pour la **simulation uniquement**, j'ai utilisé une copie de `combined_top.v` générée par `ML-DSA-OSH/scripts/build_sim.sh` (dans `build/sim/src_sim/`, non versionnée) où deux déclarations de signaux (`a_generated`, `a_generated_during`) et une troisième (`op_done_ntty`) sont déplacées au début du module : xsim refuse un signal utilisé avant sa déclaration, alors que la synthèse Vivado l'accepte. La logique est inchangée. La synthèse et l'implémentation utilisent les fichiers originaux.
- Les fichiers VHDL doivent être compilés dans un ordre explicite pour xsim (paquetages puis feuilles puis FSM, `keccak_control` après les FSM).

## 6. Problèmes et limites

- Composant ZU7EV indisponible (§0) : les fréquences et ressources ne sont pas celles de la ZCU104.
- Latence de Sign : voir §3 et §4.
- Puissance : estimation par défaut, non fiable.
- Seul le design complet `combined_top` a été implémenté (hors-contexte) ; il n'y a pas de design autour (processeur, mémoire, E/S), et rien n'a tourné sur une carte.
- Les chiffres de ressources viennent d'une seule exécution de l'outil ; d'autres stratégies ou versions donneront des résultats un peu différents.

## 7. Reproduction

```bash
source /tools/Xilinx/Vivado/2024.2/settings64.sh
cd ML-DSA-OSH/scripts
PART=xczu5ev-sfvc784-2-e vivado -mode batch -source synth_mldsa.tcl   # synthesis + implementation -> reports/raw/
./build_sim.sh                                                        # xsim, KAT check + cycle counts -> build/sim/run_*.log
python3 ../../scripts/gen_report.py                                   # (after copying run_*.log to reports/raw/sim/)
```

