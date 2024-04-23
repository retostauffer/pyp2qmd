


venv:
	virtualenv venv
	venv/bin/python -m pip install ../python-colorspace
	venv/bin/pip install pydocstring
	venv/bin/pip install pyyaml


.PHONY: init
init:
	venv/bin/python makedocs.py init -p colorspace --overwrite

install:
	venv/bin/pip uninstall -y colorspace
	venv/bin/python -m pip install ../python-colorspace

.PHONY: document
document:
	make install
	venv/bin/python makedocs.py document -p colorspace

distclean:
	-rm -rf docs

render:
	(cd _quarto; quarto render)
