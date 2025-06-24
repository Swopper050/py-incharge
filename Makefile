LINT_FILES=src/

##@ Utility
help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


pip: ## Update pip
	pip install --upgrade pip

deps_dev: pip ## Install development dependencies 
	pip install -r requirements_dev.txt

deps_prod: pip ## Install production dependencies
	pip install -r requirements.txt
	pip install -e .

deps: deps_prod deps_dev ## Install all dependencies

format: ## Format code ruff 
	ruff format  $(LINT_FILES)

format_check: ## Check code format with ruff 
	ruff format --check $(LINT_FILES)

ruff_fix: ## Run ruff lint check with auto fix
	ruff check --fix $(LINT_FILES)

ruff: ## Run ruff lint check
	ruff check $(LINT_FILES)

lint: format_check ruff  ## Run ruff format and ruff lint 

formatlint: ruff_fix format lint $(LINT_FILES) ## Format code first, then run linters
