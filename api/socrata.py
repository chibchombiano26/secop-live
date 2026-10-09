"""Live SoQL client for datos.gov.co (SECOP I + II). No database.

Datasets:
  p6dx-8zbt  SECOP II procesos (tenders)
  jbjy-vk9h  SECOP II contratos
  f789-7hwg  SECOP I procesos
  dmgg-8hin  SECOP II docs (download ref, 2025+)
"""
import os
import urllib.parse

import requests

DOMAIN = os.getenv("SOCRATA_DOMAIN", "www.datos.gov.co")
TOKEN = os.getenv("SOCRATA_APP_TOKEN", "")
TIMEOUT = int(os.getenv("SOCRATA_TIMEOUT", "40"))
MAX_LIMIT = 100

PROCESOS = "p6dx-8zbt"
CONTRATOS = "jbjy-vk9h"
SECOP1 = "f789-7hwg"
DOCS = "dmgg-8hin"


def _fetch(dataset, soql):
    url = "https://%s/resource/%s.json?%s" % (
        DOMAIN, dataset, urllib.parse.urlencode({"$query": soql}))
    headers = {"User-Agent": "secop-live/1.0"}
    if TOKEN:
        headers["X-App-Token"] = TOKEN
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []


def _esc(v):
    return v.replace("'", "''")


def _like(col, v):
    return "upper(%s) like '%%%s%%'" % (col, _esc(v.upper()))


def _words_any(cols, q):
    """Cada palabra debe aparecer en alguna de las columnas (AND de ORs).

    Asi un agente puede preguntar en lenguaje natural ("suministro alimentos
    colegios") en vez de keywords exactas.
    """
    conds = []
    for w in q.split():
        w = _esc(w.upper())
        conds.append("(%s)" % " OR ".join(
            "upper(%s) like '%%%s%%'" % (c, w) for c in cols))
    return "(%s)" % " AND ".join(conds) if conds else "1 = 1"


def _page(data, limit, offset):
    return {"limit": limit, "offset": offset,
            "next_offset": offset + limit if len(data) == limit else None,
            "prev_offset": offset - limit if offset - limit >= 0 else None,
            "data": data}


def search_procesos(estado=None, entidad=None, modalidad=None,
                    departamento=None, q=None, desde=None, hasta=None,
                    limit=20, offset=0):
    limit = max(1, min(int(limit or 20), MAX_LIMIT))
    offset = max(0, int(offset or 0))
    w = []
    if estado:
        w.append("estado_del_procedimiento = '%s'" % _esc(estado))
    if entidad:
        w.append(_like("entidad", entidad))
    if modalidad:
        w.append(_like("modalidad_de_contratacion", modalidad))
    if departamento:
        w.append(_like("departamento_entidad", departamento))
    if desde:
        w.append("fecha_de_publicacion_del >= '%s'" % _esc(desde))
    if hasta:
        w.append("fecha_de_publicacion_del <= '%s'" % _esc(hasta))
    if q:
        w.append(_words_any(["nombre_del_procedimiento",
                             "descripci_n_del_procedimiento"], q))
    where = ("WHERE " + " AND ".join(w)) if w else ""
    soql = ("SELECT *, :id %s ORDER BY fecha_de_publicacion_del DESC, :id"
            " LIMIT %d OFFSET %d" % (where, limit, offset))
    return _page(_fetch(PROCESOS, soql), limit, offset)


def detail_proceso(id_del_proceso):
    soql = ("SELECT *, :id WHERE id_del_proceso = '%s' LIMIT 100"
            % _esc(id_del_proceso))
    rows = _fetch(PROCESOS, soql)
    return {"id_del_proceso": id_del_proceso, "filas": rows}


def search_documentos(q, entidad=None, limit=20, offset=0):
    limit = max(1, min(int(limit or 20), MAX_LIMIT))
    offset = max(0, int(offset or 0))
    w = [_words_any(["nombre_archivo", "descripci_n"], q)]
    if entidad:
        w.append(_like("entidad", entidad))
    soql = ("SELECT *, :id WHERE %s ORDER BY fecha_carga DESC, :id"
            " LIMIT %d OFFSET %d" % (" AND ".join(w), limit, offset))
    return _page(_fetch(DOCS, soql), limit, offset)
