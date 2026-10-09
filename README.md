# SECOP Live Proxy

Live search over Colombia's public procurement (SECOP) via the official
`datos.gov.co` Socrata API. **No database** — a thin proxy with cache, API-key
auth, Scalar docs and MCP servers for agents.

Sibling project with local Postgres snapshot + embeddings:
`chibchombiano26/volute-secop`.

## Endpoints

- `GET /licitaciones` — filters: `estado`, `entidad`, `modalidad`,
  `departamento`, `q`, `desde`, `hasta`, `limit` (≤100), `offset`, `fresh`
- `GET /licitaciones/{id}` — full detail (CO1.REQ.xxx)
- `GET /documentos/search?q=...` — filename/description (+ `entidad`)
- `GET /health` (open), docs at `/scalar` (open)

Every list response carries `next_offset`/`prev_offset` plus absolute `next`/
`prev` URLs and `"cached": true/false`.

## Quickstart

```bash
cp .env.example .env   # set API_KEYS (+ optional SOCRATA_APP_TOKEN)
docker compose up -d --build api mcp
curl "localhost:8100/licitaciones?estado=Publicado&limit=2" -H "X-API-Key: KEY"
```

## MCP (agents)

- Remote: `http://host:8101/sse` (tools below, API key enforced)
- Local STDIO (Claude Desktop/Cursor):
  `docker compose run --rm api python -m api.mcp_server`

Tools: `buscar_licitaciones`, `detalle_licitacion`, `buscar_documentos`.

## Cache & auth

- In-memory TTL (`CACHE_TTL`, default 600s; `CACHE_DISABLE=1` off).
  `?fresh=1` bypasses (also per-tool `fresh` param). Protects Socrata throttle.
- `API_KEYS` in `.env` (`X-API-Key` header or `?api_key=`). Empty = open dev mode.

## Layout

```
api/socrata.py   SoQL client (p6dx-8zbt, dmgg-8hin)
api/main.py      FastAPI + Scalar
api/mcp_server.py MCP tools (STDIO + SSE)
api/cache.py     TTL cache | api/auth.py  API-key middleware
```
