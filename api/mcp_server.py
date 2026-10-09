"""SECOP live MCP: tools over datos.gov.co, no database.

- STDIO (Claude Desktop/Cursor):  python -m api.mcp_server
- SSE (remote agents):            port 8001 (/sse)
"""
import sys

from mcp.server.fastmcp import FastMCP

from . import socrata

mcp = FastMCP("secop-live", host="0.0.0.0", port=8001)


@mcp.tool()
def buscar_licitaciones(q: str = "", estado: str = "", entidad: str = "",
                        modalidad: str = "", departamento: str = "",
                        limit: int = 20, offset: int = 0,
                        fresh: bool = False) -> dict:
    """Search Colombia SECOP tenders live (full history + just published).
    Filter by estado (e.g. Publicado), entidad, modalidad, departamento, text.
    Use offset/next_offset to paginate."""
    from .main import _procesos
    return _procesos(estado=estado or None, entidad=entidad or None,
                     modalidad=modalidad or None, departamento=departamento or None,
                     q=q or None, desde=None, hasta=None,
                     limit=limit, offset=offset, fresh=fresh)


@mcp.tool()
def detalle_licitacion(id_del_proceso: str) -> dict:
    """Full detail of one tender by ID (CO1.REQ.xxx). May return several
    rows (one per awardee)."""
    from .main import _detalle
    return _detalle(id_del_proceso)


@mcp.tool()
def buscar_documentos(q: str, entidad: str = "", limit: int = 10,
                      offset: int = 0, fresh: bool = False) -> dict:
    """Search SECOP documents live by filename/description, optionally by entity."""
    from .main import _docs
    res = _docs(q=q, entidad=entidad or None, limit=limit, offset=offset,
                fresh=fresh)
    res = dict(res)
    res["q"] = q
    return res


if __name__ == "__main__":
    if "--sse" in sys.argv:
        import uvicorn
        from starlette.applications import Starlette

        from .auth import ApiKeyMiddleware

        wrapped = Starlette()
        wrapped.add_middleware(ApiKeyMiddleware)
        wrapped.mount("/", mcp.sse_app())
        uvicorn.run(wrapped, host="0.0.0.0", port=8001)
    else:
        mcp.run()
