"""Moteur de calcul ThermoScout: paramètres éditables, calcul thermique, import CSV/Excel."""
import csv
import io
import json
import logging
import os
import re
import unicodedata
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

log = logging.getLogger("thermoscout")
BASE = Path(__file__).parent
PARAMS_FILE = BASE / "params.json"

# clé: (défaut, min, max, libellé, unité d'affichage)
SCHEMA = {
    "rho_fumees": (1.29, 0.3, 3, "Masse volumique des fumées", "kg/Nm³"),
    "cp_fumees": (1.10, 0.5, 2, "Chaleur massique des fumées", "kJ/kg.K"),
    "cp_ceramique": (1.00, 0.5, 2, "Chaleur massique du matériau de stockage", "kJ/kg.K"),
    "rendement_recup": (0.75, 0.05, 1, "Rendement de récupération", "fraction"),
    "rendement_stockage": (0.85, 0.05, 1, "Rendement de stockage", "fraction"),
    "rendement_chaudiere": (0.90, 0.3, 1, "Rendement de la chaudière remplacée", "fraction"),
    "facteur_co2": (0.205, 0, 1, "Facteur d'émission du combustible", "tCO₂/MWh"),
    "prix_energie": (50, 1, 1000, "Prix de l'énergie évitée", "€/MWh"),
    "t_rejet": (120, 40, 600, "Température minimale de rejet", "°C"),
    "heures_tampon": (4, 0, 48, "Autonomie du stockage tampon", "h"),
    "taux_mad": (10.8, 1, 50, "Taux de change 1 € en dirhams (à vérifier)", "DH/€"),
    "capex_par_kw": (None, 0, 100000, "Coût d'investissement par kW récupérable (vide = inconnu)", "€/kW"),
    "capex_fixe": (0, 0, 1e8, "Coût d'investissement fixe", "€"),
    "seuil_fort": (65, 1, 100, "Score minimal « fort potentiel »", "pts"),
    "seuil_moyen": (40, 1, 100, "Score minimal « potentiel moyen »", "pts"),
}
DEFAULTS = {k: v[0] for k, v in SCHEMA.items()}


def _check(key, val):
    d, lo, hi = SCHEMA[key][:3]
    if val is None or val == "":
        if d is None:
            return None
        raise ValueError(f"{SCHEMA[key][3]} : valeur requise")
    try:
        v = float(val)
    except (TypeError, ValueError):
        raise ValueError(f"{SCHEMA[key][3]} : nombre attendu")
    if not (lo <= v <= hi):
        raise ValueError(f"{SCHEMA[key][3]} : doit être entre {lo} et {hi}")
    return v


def load_params() -> dict:
    p = dict(DEFAULTS)
    try:
        raw = json.loads(PARAMS_FILE.read_text(encoding="utf-8"))
        for k in DEFAULTS:
            if k in raw:
                try:
                    p[k] = _check(k, raw[k])
                except ValueError as e:
                    log.warning("Paramètre ignoré (%s), défaut conservé", e)
    except FileNotFoundError:
        pass
    except Exception as e:
        log.error("params.json illisible (%s), valeurs par défaut utilisées", e)
    if p["seuil_moyen"] >= p["seuil_fort"]:
        p["seuil_moyen"], p["seuil_fort"] = DEFAULTS["seuil_moyen"], DEFAULTS["seuil_fort"]
    return p


def save_params(new: dict) -> dict:
    p = dict(DEFAULTS)
    errors = []
    for k in DEFAULTS:
        try:
            p[k] = _check(k, new.get(k, DEFAULTS[k]))
        except ValueError as e:
            errors.append(str(e))
    if not errors and p["seuil_moyen"] >= p["seuil_fort"]:
        errors.append("Le seuil « moyen » doit être inférieur au seuil « fort ».")
    if errors:
        raise ValueError(" ; ".join(errors))
    tmp = PARAMS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(p, indent=2, ensure_ascii=False), encoding="utf-8")
    if PARAMS_FILE.exists():
        PARAMS_FILE.replace(BASE / "params.bak.json")
    tmp.replace(PARAMS_FILE)
    return p


def schema_public():
    return {k: {"default": v[0], "min": v[1], "max": v[2], "label": v[3], "unit": v[4]} for k, v in SCHEMA.items()}


class Site(BaseModel):
    client: str = Field("Site industriel", max_length=80)
    secteur: str = Field("Autre", max_length=60)
    debit_nm3h: float = Field(..., gt=0, le=2_000_000)
    t_source: float = Field(..., ge=100, le=1500)
    heures_an: float = Field(..., gt=0, le=8760)
    t_rejet: float | None = Field(None, ge=40, le=600)
    heures_tampon: float | None = Field(None, ge=0, le=48)
    prix_energie: float | None = Field(None, gt=0, le=1000)
    rendement_recup: float | None = Field(None, gt=0, le=1)
    rendement_stockage: float | None = Field(None, gt=0, le=1)
    rendement_chaudiere: float | None = Field(None, gt=0, le=1)
    facteur_co2: float | None = Field(None, ge=0, le=1)
    capex: float | None = Field(None, gt=0, le=1e9)
    contact_nom: str = Field("", max_length=80)
    contact_email: str = Field("", max_length=120)


def calcul(s: Site, p: dict | None = None) -> dict:
    p = p or load_params()
    pick = lambda name: getattr(s, name) if getattr(s, name) is not None else p[name]
    t_rejet, tampon, prix = pick("t_rejet"), pick("heures_tampon"), pick("prix_energie")
    r_rec, r_sto, r_ch, co2f = pick("rendement_recup"), pick("rendement_stockage"), pick("rendement_chaudiere"), pick("facteur_co2")
    if s.t_source <= t_rejet:
        raise ValueError("La température des fumées doit être supérieure à la température de rejet.")
    dT = s.t_source - t_rejet
    p_dispo = s.debit_nm3h * p["rho_fumees"] * p["cp_fumees"] * dT / 3600
    p_recup = p_dispo * r_rec
    e_dispo = p_dispo * s.heures_an / 1000
    e_recup = p_recup * s.heures_an / 1000
    e_valo = e_recup * r_sto
    e_evitee = e_valo / r_ch
    gain = e_evitee * prix
    co2 = e_evitee * co2f
    stock_kwh = p_recup * tampon
    masse_t = stock_kwh * 3600 / (p["cp_ceramique"] * dT) / 1000

    capex, capex_src = s.capex, "saisi"
    if capex is None and p["capex_par_kw"] is not None:
        capex, capex_src = p["capex_par_kw"] * p_recup + p["capex_fixe"], "estimé (paramètres)"
    payback = capex / gain if capex and gain > 0 else None
    if capex is None:
        capex_src = None

    sc_p = min(p_recup / 2000, 1) * 40
    sc_t = min(max((s.t_source - 150) / 450, 0), 1) * 35
    sc_h = min(s.heures_an / 6000, 1) * 25
    score = round(sc_p + sc_t + sc_h)
    niveau = "Fort potentiel" if score >= p["seuil_fort"] else "Potentiel moyen" if score >= p["seuil_moyen"] else "Potentiel faible"

    alertes = []
    if s.t_source < 200:
        alertes.append("Température basse (<200 °C) : valorisation plus limitée, pompe à chaleur à étudier.")
    if t_rejet < 140:
        alertes.append("Rejet sous ~140 °C : vérifier le risque de condensation acide (point de rosée) selon le combustible.")
    if s.heures_an < 2000:
        alertes.append("Moins de 2000 h/an : le temps de retour sera allongé.")
    if tampon == 0:
        alertes.append("Sans tampon, la chaleur n'est valorisable que si le besoin est simultané.")
    if payback is not None and payback > 8:
        alertes.append("Temps de retour supérieur à 8 ans avec l'investissement retenu.")

    r = lambda x, n=1: round(x, n)
    return {
        "p_dispo_kw": r(p_dispo, 0), "p_recup_kw": r(p_recup, 0),
        "e_dispo_mwh": r(e_dispo, 0), "e_recup_mwh": r(e_recup, 0), "e_valo_mwh": r(e_valo, 0),
        "e_evitee_mwh": r(e_evitee, 0), "gain_eur": r(gain, 0), "co2_t": r(co2, 0),
        "stock_mwh": r(stock_kwh / 1000, 2), "masse_ceramique_t": r(masse_t, 1),
        "capex_eur": r(capex, 0) if capex else None, "capex_source": capex_src,
        "payback_ans": r(payback, 1) if payback else None,
        "score": score, "niveau": niveau, "alertes": alertes,
    }


# ---------------------------------------------------------------- import
ALIASES = {
    "client": "client", "site": "client", "nom": "client", "societe": "client", "entreprise": "client",
    "secteur": "secteur", "activite": "secteur",
    "debit_nm3h": "debit_nm3h", "debit": "debit_nm3h", "debit_fumees": "debit_nm3h", "debit_nm3_h": "debit_nm3h",
    "t_source": "t_source", "temperature": "t_source", "t_fumees": "t_source", "temperature_fumees": "t_source",
    "heures_an": "heures_an", "heures": "heures_an", "heures_par_an": "heures_an",
    "t_rejet": "t_rejet", "heures_tampon": "heures_tampon", "prix_energie": "prix_energie",
    "capex": "capex", "investissement": "capex",
    "contact_nom": "contact_nom", "contact": "contact_nom", "contact_email": "contact_email", "email": "contact_email",
}
MAX_ROWS = 500
TEMPLATE_COLS = ["client", "secteur", "debit_nm3h", "t_source", "heures_an", "t_rejet", "heures_tampon",
                 "prix_energie", "capex", "contact_nom", "contact_email"]
TEMPLATE_EXAMPLE = [
    ["Verrerie Exemple", "Verre", 30000, 450, 6500, "", "", "", "", "Mme Martin", "contact@exemple.fr"],
    ["Cimenterie Exemple", "Ciment / chaux", 80000, 320, 7800, 130, 6, "", "", "", ""],
]


def _norm(h) -> str:
    s = unicodedata.normalize("NFKD", str(h or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _num(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = re.sub(r"[\s €]", "", str(v)).replace(",", ".")
    return float(t)


def read_table(data: bytes, filename: str) -> list[list]:
    name = filename.lower()
    if name.endswith((".xlsx", ".xlsm")):
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        return [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
    if name.endswith((".csv", ".txt")):
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
        try:
            dialect = csv.Sniffer().sniff(text[:2000], delimiters=";,\t")
        except csv.Error:
            dialect = csv.excel
        return list(csv.reader(io.StringIO(text), dialect))
    raise ValueError("Format non pris en charge : utilise un fichier .xlsx ou .csv")


def parse_sites(rows: list[list]):
    """Retourne (sites[(ligne, Site)], erreurs[(ligne, client, message)])."""
    rows = [r for r in rows if r and any(c not in (None, "") for c in r)]
    if len(rows) < 2:
        raise ValueError("Le fichier doit contenir une ligne d'en-têtes et au moins un site.")
    if len(rows) - 1 > MAX_ROWS:
        raise ValueError(f"Trop de lignes ({len(rows) - 1}) : maximum {MAX_ROWS}.")
    cols = {i: ALIASES[_norm(h)] for i, h in enumerate(rows[0]) if _norm(h) in ALIASES}
    missing = {"debit_nm3h", "t_source", "heures_an"} - set(cols.values())
    if missing:
        raise ValueError("Colonnes obligatoires manquantes : " + ", ".join(sorted(missing)) + ". Télécharge le modèle pour voir le format.")
    sites, errors = [], []
    for n, row in enumerate(rows[1:], start=2):
        d, client = {}, ""
        try:
            for i, key in cols.items():
                v = row[i] if i < len(row) else None
                if key in ("client", "secteur", "contact_nom", "contact_email"):
                    if v not in (None, ""):
                        d[key] = str(v).strip()
                else:
                    num = _num(v)
                    if num is not None:
                        d[key] = num
            client = d.get("client", f"Ligne {n}")
            sites.append((n, Site(**d)))
        except ValidationError as e:
            msg = "; ".join(f"{'.'.join(map(str, x['loc']))} : {x['msg']}" for x in e.errors()[:3])
            errors.append({"ligne": n, "client": client or f"Ligne {n}", "erreur": msg})
        except Exception as e:  # nombre illisible, etc.
            errors.append({"ligne": n, "client": client or f"Ligne {n}", "erreur": f"valeur illisible ({str(e)[:80]})"})
    return sites, errors
