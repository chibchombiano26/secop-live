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

- Remote: `http://host:8001/sse`, or same-port `http://host:8000/mcp/sse`
  (single-port mount, used by the free Render deploy below)
- Local STDIO (Claude Desktop/Cursor):
  `docker compose run --rm api python -m api.mcp_server`

Tools: `buscar_licitaciones`, `detalle_licitacion`, `buscar_documentos`.

## Free hosting (Render)

`render.yaml` included (no credit card). Dashboard → New → Blueprint →
pick this repo → set `API_KEYS` (+ optional `SOCRATA_APP_TOKEN`) → Deploy.
Free limits: sleeps after 15 min idle (~1 min wake), 750h/mo, 5 GB bandwidth.
Good for demos; agents wanting instant answers need a paid always-on instance.

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
