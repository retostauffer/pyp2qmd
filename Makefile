


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

