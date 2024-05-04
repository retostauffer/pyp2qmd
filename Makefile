

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


installcolorspace:
	venv/bin/pip uninstall -y colorspace
	venv/bin/python -m pip install ../python-colorspace

.PHONY: document
document:
	venv/bin/python makedocs.py document -p colorspace

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
