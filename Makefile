dev-tests:
	pipenv run python -m unittest

dev-format:
	pipenv run black src
	pipenv run flake8 --ignore="E501,E266,W503" src