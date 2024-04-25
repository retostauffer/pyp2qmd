


venv:
	virtualenv venv
	venv/bin/python -m pip install ../python-colorspace
	venv/bin/pip install pydocstring
	venv/bin/pip install pyyaml

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

all:
	make install
	make init
	make render
