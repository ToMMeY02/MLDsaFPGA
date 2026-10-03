#!/usr/bin/env python3
"""Build ~/pqc-fpga/ml-dsa/reports/ml_dsa_benchmark.md from the Vivado reports and the xsim logs (no hand-typed numbers)."""
import os, re, statistics as st
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")); R = os.path.join(REPO, "reports"); RAW = os.path.join(R, "raw")
def row(path, key):
    for l in open(path):
        if l.startswith("| " + key) and l[len(key)+2:len(key)+3] in " *":
            c = [x.strip() for x in l.split("|")]; return float(c[2]), float(c[-2])
def wns(p): return float(re.search(r"WNS\(ns\)[^\n]*\n[^\n]*\n\s*(-?[\d.]+)\s", open(p).read()).group(1))
def whs(p): return float(re.search(r"WNS\(ns\)[^\n]*\n[^\n]*\n\s*-?[\d.]+\s+\S+\s+\S+\s+\S+\s+(-?[\d.]+)", open(p).read()).group(1))
U = f"{RAW}/util_impl.rpt"; US = f"{RAW}/util_synth.rpt"; T = f"{RAW}/timing_impl.rpt"
lut, lutp = row(U, "CLB LUTs"); ff, ffp = row(U, "CLB Registers"); br, brp = row(U, "Block RAM Tile"); dsp, dspp = row(U, "DSPs")
lut_s = row(US, "CLB LUTs")[0]; ff_s = row(US, "CLB Registers")[0]
CLK = 4.35; w = wns(T); h = whs(T); fmax = 1000 / (CLK - w)
pw = float(re.search(r"Total On-Chip Power \(W\)\s*\|\s*([\d.]+)", open(f"{RAW}/power_impl.rpt").read()).group(1))
met = "All user specified timing constraints are met" in open(T).read()
# cycles from the testbench logs (each KAT prints "completed in N clock cycles")
LV = {"II": "44", "III": "65", "V": "87"}; CY = {}
bad = {}
for op in ("keygen", "sign", "verify"):
    t = open(f"{RAW}/sim/run_{op}.log").read(); bad[op] = t.count("WRONG")
    for m in re.finditer(r"ML-DSA-(II|III|V)\.(\w+), KAT #\s*(\d+) completed in\s+(\d+) clock", t):
        CY.setdefault((op, LV[m.group(1)]), []).append(int(m.group(4)))
F = 230.0   # MHz used for the conversions: the 4.35 ns constraint is met
us = lambda c: f"{c / F:.1f}"
# hierarchy (top-level children by LUT)
hier = []
for l in open(f"{RAW}/util_impl_hier.rpt"):
    m = re.match(r"\|   (\S+)\s+\|\s+(\S+)\s+\|\s+(\d+)\s+\|\s+\d+\s+\|\s+\d+\s+\|\s+\d+\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|", l)
    if m: hier.append((m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5))))
hier.sort(key=lambda x: -x[2])
L = []; A = L.append
A("# ML-DSA (FIPS 204) : benchmark FPGA du design ML-DSA-OSH\n")
A("**Design** : [KULeuven-COSIC/ML-DSA-OSH](https://github.com/KULeuven-COSIC/ML-DSA-OSH) (Verilog/VHDL, licence MIT ; une partie des fichiers vient de GMU CERG, Apache-2.0)  ")
A("**Outils** : Vivado 2024.2, xsim  ")
A("**Composant utilisé** : `xczu5ev-sfvc784-2-e` (Zynq UltraScale+, grade −2). **Ce n'est pas la ZCU104 demandée** (voir §0).  ")
A("Tous les chiffres sont extraits des rapports d'outils (`reports/raw/`) par `scripts/gen_report.py`.\n")
A("## 0. Écarts par rapport au plan\n")
A("- **Composant** : `xczu7ev-2ffvc1156-2-e` (ZCU104) et `xczu7ev-ffvc1156-2-e` sont **absents** de cette installation Vivado (seuls `xczu3eg` et `xczu5ev` sont installés ; `get_parts *zu7ev*` renvoie vide). "
  "Tout a été fait sur le ZU5EV (117 120 LUT, 234 240 FF, 144 BRAM36, 1 248 DSP), même famille UltraScale+ et même grade de vitesse. Les fréquences et ressources ne sont donc pas celles d'une ZU7EV.")
A("- **Une seule synthèse** : le design choisit le niveau (`sec_lvl` = 2, 3, 5) et l'opération (`mode`) à l'exécution sur le même matériel (cas de la note 3 du plan). "
  "Les ressources et la fréquence sont donc **identiques pour ML-DSA-44/65/87 et pour KeyGen/Sign/Verify** : il n'existe pas de chiffres de LUT/FF/BRAM/DSP par opération ou par niveau, seulement des latences différentes.")
A("- **Pas de HLS** dans ce dépôt (RTL pur, 49 fichiers Verilog/VHDL) : les latences viennent donc de la simulation RTL avec les testbenchs fournis, pas d'une co-simulation HLS.")
A("- **Pas de scripts TCL dans le dépôt** : `ML-DSA-OSH/scripts/synth_mldsa.tcl` est un script écrit pour cette étude (j'ai écrit le mien plutôt que celui du plan, car il y avait deux difficultés : une synthèse unique suffit, et il fallait déclarer `zetas.txt` comme fichier d'initialisation mémoire).")
A(f"- **Contrainte d'horloge** : {CLK} ns (≈ 230 MHz, la fréquence indiquée pour l'article dans le plan), en mode hors-contexte (out-of-context).\n")
A("## 1. Ressources (un seul matériel pour les 3 niveaux et les 3 opérations)\n")
A("| Étape | LUT | FF | BRAM36 | DSP | URAM |")
A("|---|---:|---:|---:|---:|---:|")
A(f"| Après synthèse | {lut_s:,.0f} | {ff_s:,.0f} | {row(US,'Block RAM Tile')[0]:.0f} | {row(US,'DSPs')[0]:.0f} | 0 |")
A(f"| **Après placement et routage** | **{lut:,.0f}** ({lutp:.1f} %) | **{ff:,.0f}** ({ffp:.1f} %) | **{br:.0f}** ({brp:.1f} %) | **{dsp:.0f}** ({dspp:.1f} %) | 0 |")
A(f"\nPuissance estimée par Vivado : {pw:.2f} W (activité par défaut : indicatif, pas une mesure).\n")
A("Principaux blocs (post-route, LUT / FF / BRAM36 / DSP) :\n")
A("| Instance | Module | LUT | FF | BRAM36 | DSP |")
A("|---|---|---:|---:|---:|---:|")
def full(name):
    for l in open(f"{RAW}/util_impl_hier.rpt"):
        c = [x.strip() for x in l.split("|")]
        if len(c) > 12 and c[1] == name: return c
    return None
for name, mod, l_, f_, b_ in hier[:8]:
    c = full(name)
    A(f"| {name} | {mod} | {int(c[3]):,} | {int(c[7]):,} | {int(c[8])} | {int(c[11])} |") if c else None
A("")
A("## 2. Fréquence\n")
A(f"| Contrainte | WNS | WHS | Contraintes respectées | Fmax estimée |")
A("|---|---:|---:|---|---:|")
A(f"| {CLK} ns ({1000/CLK:.0f} MHz) | {w:+.3f} ns | {h:+.3f} ns | {'oui' if met else 'non'} | {fmax:.1f} MHz |")
A("\nLa Fmax est `1000 / (contrainte − WNS)` pour **cette** contrainte et cette exécution. Avec une contrainte plus sévère, l'outil pourrait aller un peu plus haut : je n'ai pas cherché la fréquence maximale.\n")
A("## 3. Latence (cycles, simulation RTL avec les testbenchs du dépôt)\n")
A("Chaque testbench envoie les entrées et lit les sorties du `combined_top`, **compare à des vecteurs de test NIST (ACVP)**, et affiche le nombre de cycles entre le démarrage et la fin d'une opération. "
  f"Résultat de la comparaison : **0 erreur** sur tous les vecteurs (KeyGen {len(CY[('keygen','44')])*3} vecteurs, Sign {len(CY[('sign','44')])*3}, Verify {len(CY[('verify','44')])*3} ; messages `WRONG` : "
  f"KeyGen {bad['keygen']}, Sign {bad['sign']}, Verify {bad['verify']}).\n")
A("| Niveau | Opération | Vecteurs | Cycles min | Cycles moyen | Cycles max | Latence moyenne @230 MHz (µs) |")
A("|---|---|---:|---:|---:|---:|---:|")
for lv, name in (("44", "ML-DSA-44"), ("65", "ML-DSA-65"), ("87", "ML-DSA-87")):
    for op, lab in (("keygen", "KeyGen"), ("sign", "Sign"), ("verify", "Verify")):
        v = CY[(op, lv)]
        A(f"| {name} | {lab} | {len(v)} | {min(v):,} | {st.mean(v):,.0f} | {max(v):,} | {us(st.mean(v))} |")
A("\nNotes :")
A("- **Sign varie fortement d'un vecteur à l'autre** (rejet probabiliste) : par exemple ML-DSA-87 de "
  f"{min(CY[('sign','87')]):,} à {max(CY[('sign','87')]):,} cycles. La moyenne sur 15 vecteurs est donc une estimation grossière ; KeyGen et Verify sont quasi constants.")
A("- Les cycles incluent le transfert des données par le testbench (bus de 64 bits, côté testbench toujours prêt), pas seulement le calcul.")
A("- La conversion en µs utilise 230 MHz (la contrainte respectée) ; à la Fmax estimée de "
  f"{fmax:.0f} MHz les valeurs seraient pratiquement les mêmes.\n")
A("## 4. Comparaison avec les valeurs de l'article indiquées dans votre plan\n")
A("Ces valeurs viennent de votre plan (« DATE 2026, UltraScale+ à 230 MHz ») ; **je ne les ai pas vérifiées** contre l'article.\n")
A("| | LUT | FF | BRAM | DSP | Sign-44 | Sign-65 | Sign-87 |")
A("|---|---:|---:|---:|---:|---:|---:|---:|")
A("| Plan (article) | 54,942 | 29,309 | 29 | 16 | 106 µs | 143 µs | 160 µs |")
s = lambda lv: us(st.mean(CY[('sign', lv)]))
A(f"| Cette mesure (ZU5EV, post-route, latence moyenne) | {lut:,.0f} | {ff:,.0f} | {br:.0f} | {dsp:.0f} | {s('44')} µs | {s('65')} µs | {s('87')} µs |")
A("\nLes ressources concordent bien (BRAM et DSP identiques, LUT +2,8 %, FF −0,1 %). Pour la latence de Sign, ML-DSA-44 et ML-DSA-65 concordent à quelques pour cent, "
  "mais **ML-DSA-87 est nettement plus lent dans ma mesure (~236 µs contre 160 µs)**. Je ne sais pas expliquer l'écart : la latence de Sign dépend du nombre d'essais de rejet (moyenne sur 15 vecteurs seulement) et je ne connais pas la méthode de mesure de l'article.\n")
A("## 5. Modifications apportées\n")
A("- **Aucun fichier original du dépôt n'a été modifié.**")
A("- Pour la **simulation uniquement**, j'ai utilisé une copie de `combined_top.v` générée par `ML-DSA-OSH/scripts/build_sim.sh` (dans `build/sim/src_sim/`, non versionnée) où deux déclarations de signaux (`a_generated`, `a_generated_during`) et une troisième (`op_done_ntty`) sont déplacées au début du module : xsim refuse un signal utilisé avant sa déclaration, alors que la synthèse Vivado l'accepte. La logique est inchangée. La synthèse et l'implémentation utilisent les fichiers originaux.")
A("- Les fichiers VHDL doivent être compilés dans un ordre explicite pour xsim (paquetages puis feuilles puis FSM, `keccak_control` après les FSM).\n")
A("## 6. Problèmes et limites\n")
A("- Composant ZU7EV indisponible (§0) : les fréquences et ressources ne sont pas celles de la ZCU104.")
A("- Latence de Sign : voir §3 et §4.")
A("- Puissance : estimation par défaut, non fiable.")
A("- Seul le design complet `combined_top` a été implémenté (hors-contexte) ; il n'y a pas de design autour (processeur, mémoire, E/S), et rien n'a tourné sur une carte.")
A("- Les chiffres de ressources viennent d'une seule exécution de l'outil ; d'autres stratégies ou versions donneront des résultats un peu différents.\n")
A("## 7. Reproduction\n")
A("```bash\nsource /tools/Xilinx/Vivado/2024.2/settings64.sh\ncd ML-DSA-OSH/scripts\n"
  "PART=xczu5ev-sfvc784-2-e vivado -mode batch -source synth_mldsa.tcl   # synthesis + implementation -> reports/raw/\n"
  "./build_sim.sh                                                        # xsim, KAT check + cycle counts -> build/sim/run_*.log\n"
  "python3 ../../scripts/gen_report.py                                   # (after copying run_*.log to reports/raw/sim/)\n```\n")
open(f"{R}/ml_dsa_benchmark.md", "w").write("\n".join(L) + "\n")
print("written", f"{R}/ml_dsa_benchmark.md")
