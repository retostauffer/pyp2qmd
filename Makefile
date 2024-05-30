

test:
	-rm -rf _quarto
	make install
	pyp2qmd init -p pyp2qmd
	tree _quarto/
	cat _quarto/_quarto.yml


venv: requirements.txt
	virtualenv venv
	venv/bin/pip install -r requirements.txt

clean:
	-rm -rf _quarto/man
	-rm _quarto/index.qmd
	-rm _quarto/_quarto.yml

distclean:
	-rm -rf docs


.PHONY: init
init:
	make clean
	venv/bin/python makedocs.py init -p colorspace --overwrite

install:
	@echo "********* REMOVE AND REINSTALL PYTHON PACKAGE *********"
	python setup.py clean --all && pip install -e .


# Makes use of the token/config stored in $HOME/.pypirc
sdist:
	python setup.py sdist

testpypi:
	make sdist
	twine upload --verbose --repository testpypi dist/*

pypirelease:
	make sdist
	twine upload --verbose --repository pypi dist/*

.PHONY: document
document:
	make install
	python make_docs/main.py # Custom 'make package documentation for this package'
	##pyp2qmd init --package pyp2qmd --output_dir ../docs --overwrite

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
