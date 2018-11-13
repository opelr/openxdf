dev-tests:
	pipenv run python -m unittest

dev-format:
	pipenv run black openxdf
	pipenv run flake8 --ignore="E501,E266,W503" src

package-dist:
	pipenv run python setup.py sdist
