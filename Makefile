.PHONY: init up down logs test live-test mcp-stdio-test

init:
	cp -n .env.example .env || true
	docker compose build

up:
	docker compose up -d api mcp

down:
	docker compose down

logs:
	docker compose logs -f api mcp

test:
	python3 -m unittest discover -s tests -v

live-test:
	curl -s "localhost:8100/licitaciones?estado=Publicado&limit=1" -H "X-API-Key: $$(grep ^API_KEYS .env | cut -d= -f2)" | head -c 300; echo

mcp-stdio-test:
	printf '%s\n%s\n%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | docker compose run --rm api python -m api.mcp_server 2>/dev/null | tail -1 | head -c 400; echo
