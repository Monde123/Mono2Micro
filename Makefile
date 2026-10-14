# Mono2Micro Makefile
.PHONY: test bench lint install

test:
	PYTHONPATH=agent_cli pytest agent_cli/tests -v

bench:
	PYTHONPATH=agent_cli:agent_cli/benchmarks python3 -m mono2micro.cli bench --output benchmarks/results

doctor:
	PYTHONPATH=agent_cli python3 -m mono2micro.cli doctor

lint:
	npm run lint
	PYTHONPATH=agent_cli python3 -m mono2micro.cli --help > /dev/null

install:
	npm install
	pip install -e agent_cli
