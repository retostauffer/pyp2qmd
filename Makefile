


venv:
	virtualenv venv
	venv/bin/python -m pip install ../python-colorspace
	venv/bin/pip install pydocstring
	venv/bin/pip install pyyaml


.PHONY: init
init:
	venv/bin/python makedocs.py init -p colorspace

.PHONY: document
document:
	venv/bin/python makedocs.py document -p colorspace

distclean:
	-rm -rf docs
