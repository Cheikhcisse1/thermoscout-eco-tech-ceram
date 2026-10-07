"""Tests de ThermoScout:  .venv\\Scripts\\python.exe -m unittest tests -v"""
import io
import unittest

from fastapi.testclient import TestClient

import engine
import server
from engine import Site

C = TestClient(server.app)


class Calcul(unittest.TestCase):
    def test_puissance(self):
        r = engine.calcul(Site(debit_nm3h=30000, t_source=450, heures_an=6500), dict(engine.DEFAULTS))
        self.assertAlmostEqual(r["p_dispo_kw"], 3902, delta=1)
        self.assertEqual(r["niveau"], "Fort potentiel")

    def test_rejet_trop_haut(self):
        with self.assertRaises(ValueError):
            engine.calcul(Site(debit_nm3h=1000, t_source=200, heures_an=100, t_rejet=300), dict(engine.DEFAULTS))

    def test_payback(self):
        r = engine.calcul(Site(debit_nm3h=30000, t_source=450, heures_an=6500, capex=900000), dict(engine.DEFAULTS))
        self.assertAlmostEqual(r["payback_ans"], 1.0, delta=0.1)


class Params(unittest.TestCase):
    def test_refuse_valeur_absurde(self):
        with self.assertRaises(ValueError):
            engine.save_params({**engine.DEFAULTS, "rendement_recup": 5})

    def test_refuse_seuils_inverses(self):
        with self.assertRaises(ValueError):
            engine.save_params({**engine.DEFAULTS, "seuil_moyen": 80, "seuil_fort": 50})


class Import(unittest.TestCase):
    def test_csv_virgule_decimale_et_erreurs(self):
        csv = "Client;Débit;Température;Heures\nA;30 000;450;6500\nB;-1;450;6500\nC;abc;450;6500\n".encode("utf-8")
        sites, errs = engine.parse_sites(engine.read_table(csv, "x.csv"))
        self.assertEqual(len(sites), 1)
        self.assertEqual(len(errs), 2)

    def test_colonnes_manquantes(self):
        with self.assertRaises(ValueError):
            engine.parse_sites(engine.read_table(b"client;debit\nA;100\n", "x.csv"))

    def test_format_inconnu(self):
        with self.assertRaises(ValueError):
            engine.read_table(b"x", "x.exe")


class Api(unittest.TestCase):
    def test_analyze_invalide(self):
        self.assertEqual(C.post("/api/analyze", json={"debit_nm3h": -1, "t_source": 400, "heures_an": 10}).status_code, 422)

    def test_template_puis_batch(self):
        t = C.get("/api/template.xlsx")
        self.assertEqual(t.status_code, 200)
        r = C.post("/api/batch?filename=modele.xlsx", content=t.content)
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertEqual(j["summary"]["sites"], 2)
        e = C.post("/api/batch/export", json={"rows": j["rows"], "devise": "MAD"})
        self.assertEqual(e.status_code, 200)
        self.assertTrue(e.content.startswith(b"PK"))

    def test_batch_fichier_vide_ou_corrompu(self):
        self.assertEqual(C.post("/api/batch?filename=a.xlsx", content=b"").status_code, 400)
        self.assertEqual(C.post("/api/batch?filename=a.xlsx", content=b"pas un xlsx").status_code, 422)

    def test_batch_trop_gros(self):
        self.assertEqual(C.post("/api/batch?filename=a.csv", content=b"x" * (2 * 1024 * 1024 + 1)).status_code, 413)

    def test_params_roundtrip(self):
        p = C.get("/api/params").json()["params"]
        self.assertEqual(C.put("/api/params", json=p).status_code, 200)
        self.assertEqual(C.put("/api/params", json={**p, "prix_energie": -3}).status_code, 422)


class Rag(unittest.TestCase):
    def files(self, q):
        return {h["file"][:2] for h in __import__("rag").INDEX.search(q, k=3)}

    def test_retrouve_le_bon_document(self):
        self.assertIn("01", self.files("Qu'est-ce qu'Eco-Stock ?"))
        self.assertIn("03", self.files("Comment importer plusieurs sites Excel ?"))
        self.assertIn("02", self.files("Qu'est-ce que la chaleur fatale ?"))
        self.assertIn("01", self.files("Qui a financé l'entreprise ?"))

    def test_hors_sujet_sans_resultat(self):
        self.assertEqual(__import__("rag").INDEX.search("recette de la tarte aux pommes"), [])

    def test_chat_hors_sujet_ne_hallucine_pas(self):
        j = C.post("/api/chat", json={"message": "recette de la tarte aux pommes"}).json()
        self.assertFalse(j["grounded"])
        self.assertEqual(j["sources"], [])

    def test_stream_hors_sujet(self):
        r = C.post("/api/chat/stream", json={"message": "recette de la tarte aux pommes"})
        self.assertEqual(r.status_code, 200)
        self.assertIn('"grounded": false', r.text)

    def test_stream_validation(self):
        self.assertEqual(C.post("/api/chat/stream", json={"message": ""}).status_code, 422)

    def test_stemming(self):
        t = __import__("rag").tokens
        self.assertEqual(set(t("financé")) & set(t("financement")), {"financ"})

    def test_chat_validation(self):
        self.assertEqual(C.post("/api/chat", json={"message": "  "}).status_code, 422)
        self.assertEqual(C.post("/api/chat", json={"message": "x" * 1001}).status_code, 422)


class Securite(unittest.TestCase):
    def app(self, **env):
        import os
        from unittest import mock
        from fastapi import FastAPI
        import security
        a = FastAPI()
        with mock.patch.dict(os.environ, env, clear=False):
            security.install(a, ("/api/chat",))

        @a.get("/secret")
        def secret():
            return {"ok": 1}

        @a.post("/api/chat")
        def chat():
            return {"ok": 1}
        return TestClient(a)

    def test_refuse_de_demarrer_sans_mot_de_passe(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"REQUIRE_AUTH": "1", "APP_PASSWORD": ""}):
            with self.assertRaises(RuntimeError):
                self.app(REQUIRE_AUTH="1", APP_PASSWORD="")

    def test_mot_de_passe(self):
        c = self.app(APP_PASSWORD="s3cret", REQUIRE_AUTH="")
        self.assertEqual(c.get("/secret").status_code, 401)
        self.assertEqual(c.get("/secret", auth=("x", "faux")).status_code, 401)
        self.assertEqual(c.get("/secret", auth=("x", "s3cret")).status_code, 200)
        self.assertEqual(c.get("/healthz").status_code, 200)  # sonde publique

    def test_limite_de_requetes_et_en_tetes(self):
        c = self.app(APP_PASSWORD="", REQUIRE_AUTH="", RATE_LIMIT_PER_HOUR="2")
        self.assertEqual(c.post("/api/chat").status_code, 200)
        self.assertEqual(c.post("/api/chat").status_code, 200)
        r = c.post("/api/chat")
        self.assertEqual(r.status_code, 429)
        self.assertEqual(c.get("/secret").headers["x-frame-options"], "DENY")


if __name__ == "__main__":
    unittest.main()
