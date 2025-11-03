

test:
	-rm -rf _quarto
	make install
	pyp2qmd init -p pyp2qmd
	tree _quarto/
	cat _quarto/_quarto.yml


venv: requirements.txt
	python3 -m virtualenv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r requirements_devel.txt

clean:
	-rm -rf _quarto/man
	-rm _quarto/index.qmd
	-rm _quarto/_quarto.yml

distclean:
	-rm -rf docs


.PHONY: init
init:
	make clean
	.venv/bin/python makedocs.py init -p colorspace --overwrite

install:
	@echo "********* REMOVE AND REINSTALL PYTHON PACKAGE *********"
	python setup.py clean --all && pip install -e .


# Prepare package for PyPI submission
.PHONY: build
build: clean
	-rm -rf build dist *.egg-info
	python -m build

# Rules to push releases to PyPI test and PyPI.
# Makes use of the token/config stored in $HOME/.pypirc

testpypi: build
	twine check dist/*
	twine upload --verbose --repository testpypi dist/*

pypirelease: build
	twine check dist/*
	twine upload --verbose --repository pypi dist/*

.PHONY: document
document:
	make install
	python make_docs/main.py # Custom 'make package documentation for this package'

.PHONY: docx
docx:
	-rm -rf _quarto
	pyp2qmd init --package pyp2qmd --output_dir _quarto --overwrite

render:
	(cd _quarto; quarto render)

preview:
	(cd _quarto; quarto preview)


all:
	make install
	make init
	make render

sync:
	rsync -va _quarto/_site retostauffer:~/html/trash/ --delete
