SHELL := bash

PORT ?= 8000

info: menu select

menu:
	echo "1 make update               - fetch latest model data into docs/models.json"
	echo "2 make serve                - preview the page at http://localhost:$(PORT)"
	echo "3 make stats                - show model counts per provider"
	echo "4 make pages                - enable GitHub Pages (main branch, /docs) for this repo"
	echo "5 make update_phony         - update .PHONY in Makefile"

select:
	read -p ">>> " P ; make menu | grep "^$$P " | cut -d ' ' -f2-3 | bash

.SILENT:

.PHONY: info menu select update serve stats pages update_phony

update:
	python3 scripts/update_models.py

serve:
	python3 -m http.server $(PORT) --directory docs

stats:
	jq -r '"updated \(.updated_at)", (.providers[] | "\(.model_count)\t\(.id)")' docs/models.json

pages:
	gh api -X POST "repos/{owner}/{repo}/pages" -f "source[branch]=main" -f "source[path]=/docs" --jq .html_url

update_phony:
	echo "##### Updating .PHONY targets #####"
	targets=$$(grep -E '^[a-zA-Z_][a-zA-Z0-9_-]*:' Makefile | grep -v '=' | cut -d: -f1 | tr '\n' ' '); \
	sed -i.bak "s/^\.PHONY:.*/.PHONY: $$targets/" Makefile && \
	echo "Updated .PHONY: $$targets" && \
	rm -f Makefile.bak
