# Root Makefile: delegates to the two projects. `make setup && make run` gets you a working desk.

.PHONY: setup db test lint web run serve dev eval validate clean

setup:            ## backend venv + deps, frontend node_modules
	$(MAKE) -C backend setup
	cd frontend && npm install --no-audit --no-fund

db:               ## build the backend SQLite database
	$(MAKE) -C backend db

test:             ## backend tests
	$(MAKE) -C backend test

lint:             ## backend lint
	$(MAKE) -C backend lint

web:              ## build the frontend into frontend/dist
	cd frontend && npm run build

run: db web       ## build everything and serve API + UI on http://127.0.0.1:8000
	$(MAKE) -C backend serve

serve:            ## serve the API (and frontend/dist if built) without rebuilding
	$(MAKE) -C backend serve

dev:              ## frontend dev server on :5173 (run `make serve` in another terminal)
	cd frontend && npm run dev

eval:             ## grade all tiers with the configured provider
	$(MAKE) -C backend eval

validate:         ## organiser's dataset validator
	$(MAKE) -C backend validate

clean:
	$(MAKE) -C backend clean
	rm -rf frontend/dist
