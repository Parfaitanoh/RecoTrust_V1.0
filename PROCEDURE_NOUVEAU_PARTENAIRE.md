# Procédure — Ajouter un nouveau partenaire RecoTrust

Cette procédure évite l’erreur `No module named 'partenaires.xxx'`.

## Règle d’or

Le nom affiché dans la liste déroulante **doit** correspondre **exactement** :
1. à la clé dans `partenaires/__init__.py` → `PROCESSORS`
2. à la clé dans `utils/match_config.py` → `DEFAULT_MATCH_KEYS`
3. aux fichiers modules réellement présents dans `partenaires/`

---

## Étapes obligatoires

### 1. Créer le(s) fichier(s) processeur

| Type | Fichier | Classe (exemple) |
|------|---------|------------------|
| Payment (payin) | `partenaires/monpartenaire_payin.py` | `MonpartenairePayinProcessor` |
| Transfer (payout) | `partenaires/monpartenaire_payout.py` | `MonpartenairePayoutProcessor` |

**Convention de nommage**
- Module : minuscules, sans espace ni tiret → `orangesn_payin.py`
- Classe : PascalCase + suffixe → `OrangesnPayinProcessor`

**Contenu minimal du constructeur**
```python
class OrangesnPayinProcessor:
    def __init__(self, data_file, partner_file, reco_start=None, reco_end=None,
                 match_col_pmt=None, match_col_partner=None):
        self.data_file = data_file
        self.partner_file = partner_file
        self.reco_start = reco_start
        self.reco_end = reco_end
        self.match_col_pmt = match_col_pmt
        self.match_col_partner = match_col_partner

    def process(self):
        ...
```

Astuce : **copier un partenaire proche** (ex. Orange CI → `omci_payin.py`) puis adapter
les colonnes de matching et le nettoyage du fichier partenaire.

### 2. Enregistrer dans le registre lazy

Fichier : `partenaires/__init__.py`

```python
PROCESSORS = {
    "Payment": {
        ...
        "Orange SN": "orangesn_payin.OrangesnPayinProcessor",
    },
    "Transfer": {
        ...
        "Orange SN": "orangesn_payout.OrangesnPayoutProcessor",
    },
}
```

- Clé = libellé exact de la selectbox
- Valeur = `"nom_module.NomClasse"` (**sans** le préfixe `partenaires.`)

### 3. Colonnes de matching par défaut

Fichier : `utils/match_config.py`

```python
DEFAULT_MATCH_KEYS = {
    ("Payment", "Orange SN"): ("Transaction ID", "Référence Partenaire"),
    ("Transfer", "Orange SN"): ("Transaction ID", "Référence Partenaire"),
}
```

⚠️ Le libellé partenaire doit être **identique** à celui de `PROCESSORS`  
(`"Orange SN"` ≠ `"ORANGE SN"`).

### 4. Vérifications avant lancement

```bash
# Les fichiers existent
ls partenaires/orangesn_payin.py partenaires/orangesn_payout.py

# Syntaxe Python
python -m py_compile partenaires/orangesn_payin.py
python -m py_compile partenaires/orangesn_payout.py

# Import du registre
python -c "from partenaires import get_available_partners; print(get_available_partners('Payment'))"
```

### 5. Redémarrer Streamlit

Après ajout de fichiers, **redémarrer** l’application (les modules sont mis en cache).

---

## Checklist anti-erreur

- [ ] Fichier `partenaires/<module>_payin.py` et/ou `_payout.py` créé
- [ ] Classe `*Processor` avec `__init__(data_file, partner_file, ...)` et `process()`
- [ ] Entrée dans `PROCESSORS["Payment"]` et/ou `PROCESSORS["Transfer"]`
- [ ] Chaîne `"module.Classe"` correcte (nom fichier sans `.py`)
- [ ] Entrée dans `DEFAULT_MATCH_KEYS` avec le **même** libellé
- [ ] Colonnes de matching réellement présentes dans les fichiers PMT / partenaire
- [ ] `python -m py_compile` sans erreur
- [ ] Streamlit redémarré

---

## Erreurs fréquentes

| Erreur | Cause | Correctif |
|--------|--------|-----------|
| `No module named 'partenaires.orangesn_payin'` | Fichier manquant ou mauvais nom | Créer `partenaires/orangesn_payin.py` |
| `module '…' has no attribute 'XxxProcessor'` | Nom de classe incorrect dans PROCESSORS | Aligner `PROCESSORS` et `class` |
| Partenaire absent de la liste | Pas d’entrée PROCESSORS | Ajouter la clé |
| Mauvaises colonnes de matching | match_config ou libellé différent | Harmoniser le libellé |
| `KeyError` sur une colonne | Export partenaire différent | Adapter le nettoyage / rename |

---

## Orange SN (livré en V5.1.8)

| Élément | Valeur |
|---------|--------|
| Libellé UI | `Orange SN` |
| Payin | `orangesn_payin.OrangesnPayinProcessor` |
| Payout | `orangesn_payout.OrangesnPayoutProcessor` |
| Matching défaut | PMT `Transaction ID` ↔ Partenaire `Référence Partenaire` |

Le nettoyage des exports Orange SN est **défensif** (plusieurs alias de colonnes).  
Si votre fichier utilise d’autres libellés, ajustez le bloc de rename en tête de `process()`.
