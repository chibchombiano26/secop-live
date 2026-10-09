"""SECOP live proxy API: search datos.gov.co directly. No database."""
from fastapi import FastAPI, HTTPException, Query, Request
from scalar_fastapi import add_scalar_reference

from . import socrata
from .auth import ApiKeyMiddleware
from .cache import cached, last_hit

app = FastAPI(title="SECOP Live Proxy",
              description="Live search over Colombia SECOP (datos.gov.co Socrata API). No database.",
              version="1.0.0",
              docs_url=None, redoc_url=None)

app.add_middleware(ApiKeyMiddleware)
add_scalar_reference(app, route="/scalar")


def _with_pages(request: Request, res: dict) -> dict:
    """Absolute next/prev URLs (None when exhausted)."""
    import urllib.parse
    out = dict(res)

    def url(offset):
        qp = dict(request.query_params)
        qp["offset"] = str(offset)
        return str(request.url.replace(query=urllib.parse.urlencode(qp)))

    out["next"] = url(res["next_offset"]) if res.get("next_offset") is not None else None
    out["prev"] = url(res["prev_offset"]) if res.get("prev_offset") is not None else None
    out["cached"] = last_hit.get(False)
    return out


@cached
def _procesos(**kw):
    kw.pop("fresh", None)
    return socrata.search_procesos(**kw)


@cached
def _detalle(pid, **kw):
    return socrata.detail_proceso(pid)


@cached
def _docs(**kw):
    kw.pop("fresh", None)
    return socrata.search_documentos(**kw)


@app.get("/health")
def health():
    return {"ok": True, "mode": "live-proxy"}


@app.get("/licitaciones", tags=["licitaciones"])
def licitaciones(request: Request, estado: str = Query(None, description="E.g. Publicado"),
                 entidad: str = Query(None), modalidad: str = Query(None),
                 departamento: str = Query(None),
                 q: str = Query(None, description="Text in name/description"),
                 desde: str = Query(None, description="YYYY-MM-DD"),
                 hasta: str = Query(None, description="YYYY-MM-DD"),
                 limit: int = Query(20, le=100), offset: int = Query(0, ge=0),
                 fresh: bool = Query(False, description="1 = bypass cache")):
    return _with_pages(request, _procesos(estado=estado, entidad=entidad,
                                          modalidad=modalidad, departamento=departamento,
                                          q=q, desde=desde, hasta=hasta,
                                          limit=limit, offset=offset, fresh=fresh))


@app.get("/licitaciones/{id_del_proceso}", tags=["licitaciones"])
def licitacion(id_del_proceso: str):
    rows = _detalle(id_del_proceso)["filas"]
    if not rows:
        raise HTTPException(404, "not found")
    return {"id_del_proceso": id_del_proceso, "filas": rows}


@app.get("/documentos/search", tags=["documentos"])
def documentos_search(request: Request, q: str, entidad: str = Query(None),
                      limit: int = Query(20, le=100), offset: int = Query(0, ge=0),
                      fresh: bool = Query(False, description="1 = bypass cache")):
    res = _docs(q=q, entidad=entidad, limit=limit, offset=offset, fresh=fresh)
    res = dict(res)
    res["q"] = q
    return _with_pages(request, res)
