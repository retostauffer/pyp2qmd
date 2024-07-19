
class ManPage:
    """Quarto Manual Page

    Class handling the creation of the quarto markdown (`.qmd`) manual pages.

    Args:
        name (str): Name of the function, class, or method.
        obj (function or class): The function or class to be documented.
        config (Config): Object of class :py:class:`Config <pyp2qmd.Config.Config>`.
        parent (None, str): `None` (default) if a class or function is documented.
            Used to document methods, in this case `parent` contains the name of
            the parent class as str.
          
    Returns:
        Initializes an object of this class.
    """

    def __init__(self, name, obj, config, parent = None):

        from inspect import isfunction, isclass
        from .Config import Config

        # parent (None, str): If str, this will be removed from full name.
        if not isinstance(name, str):
            raise TypeError("argument `name` must be str")
        if not isfunction(obj) and not isclass(obj):
            raise TypeError("argument `obj` must be function or class")
        if not isinstance(parent, type(None)) and not isinstance(parent, str):
            raise TypeError("argument `parent` must be None or str")
        if not isinstance(config, Config):
            raise TypeError("argument `config` must be of class `Config`")

        self._name    = name
        self._obj     = obj
        self._parent  = parent
        self._config  = config

        self._doc, self._signature, self._module = self._extract_docstring()


    def _extract_docstring(self):
        """Extract Docstring

        Helper function to extract the docstring.

        Returns:
            list: Returns a list with three elements containing
                the docstring itself, the signature, and the module name.
                If no docstring is present, a list witht three `None`s is returned.
        """
        import inspect
        from docstring_parser import DocstringStyle, parse
        dstyle = getattr(DocstringStyle, self.config_get("docstringstyle").upper())

        # If parent is None, extract docstring of main function or class.
        docstring = parse(inspect.getdoc(self._obj), dstyle)
        if docstring:
            res = [docstring, inspect.signature(self._obj), self._obj.__module__]
        else:
            res = [None, None, None]

        return res

    def config_get(self, what):
        """Get Config Argument

        Interfaces the `.get()` method of the
        :py:class:`Config <pyp2qmd.Config.Config>` object.

        Args:
            what (str): Name of the attribute.

        Returns:
            Whatever is stored on the attribute.
        """
        return self._config.get(what)


    def fullname(self):
        from re import match
        if match(f"^{self._module}", self._name):
            return self._name
        else:
            return f"{self._module}.{self._name}"


    def quartofile(self):
        return f"{self.fullname()}.qmd"


    def isclass(self):
        from inspect import isclass
        return isclass(self._obj)


    def isfunction(self):
        from inspect import isfunction
        return isfunction(self._obj)


    def _format_signature(self, name, max_length = 200, remove_self = False):
        """
        formatting of signature to get some line breaks in output
        """

        from re import compile
        from html import escape

        n = max_length - len(name) - 1
        formatted_params = []
        tmp = []

        # Replacing '<lambda> at [memory pointer]>' with <lambda>
        relambda = compile("<lambda>\s+at\s+\w+>")

        for k,p in self._signature.parameters.items():
            # Removing lambda function mem addr, excaping html chars
            p = escape(relambda.sub(r"<lambda>>", str(p)))
            if remove_self and k == "self": continue
            tmp_len = max(0, sum([len(x) for x in tmp]) + (len(tmp) - 1) * 2)
            if (tmp_len + len(p) + 1) <= n:
                tmp.append(p)
            else:
                formatted_params.append(", ".join(tmp))  
                tmp = [p]

        # First empty? Can happen if max_length very small
        if len(formatted_params) > 0 and formatted_params[0] == "":
            formatted_params = formatted_params[1:]
        # End   
        if len(tmp) > 0: formatted_params.append(", ".join(tmp))
            
        spacers = "".join([" "] * (len(name) + 1))
        return name + "(" + f",<br/>{spacers}".join(formatted_params) + ")"   


    def signature(self, remove_self = None, max_length = 200):
        from re import sub

        assert isinstance(remove_self, type(None)) or isinstance(remove_self, bool)
        assert isinstance(max_length, int)
        assert max_length >= 0
        name = self._name
        # Remove ^parent. if self._parent is set
        if isinstance(self._parent, str):
            name = sub(f"^{self._parent}\.", "", self._name)
        else:
            name = self._name

        if remove_self is None:
            remove_self = self._parent is not None
        
        return self._format_signature(name, max_length, remove_self)


    def getmembers(self):
        import inspect
        members = []
        for rec in inspect.getmembers(self._obj):
            # requires three independent ifs here
            if rec[0].startswith("__"): continue
            if not inspect.isfunction(rec[1]) and not inspect.isclass(rec[1]): continue
            if not self.config_get("include_hidden") and rec[1].__name__.startswith("_"): continue
            members.append((f"{self.fullname()}.{rec[0]}", rec[1]))
        return members


    def get(self, attr):
        assert isinstance(attr, str), "argument `attr` must be of type str"
        if not hasattr(self._doc, attr):    return None
        else:                               return getattr(self._doc, attr)


    def write_qmd(self):

        from os.path import isfile
        import tempfile
        import filecmp

        qmd   = f"{self.config_get('man_dir')}/{self.quartofile()}"
        ofile = f"{self.config_get('quarto_dir')}/{qmd}"

        if not isfile(ofile):
            with open(ofile, "w+") as fid: print(self, file = fid)
        else:
            tmpfile = tempfile.NamedTemporaryFile()
            with open(tmpfile.name, "w+") as fid: print(self, file = fid)
            files_equal = filecmp.cmp(tmpfile.name, ofile)
            # New file differs? Overwrite existing qmd. Re-write the file (not
            # move the temporary file) to ensure correct file permissions.
            if not files_equal:
                with open(ofile, "w+") as fid: print(self, file = fid)
            tmpfile.close()
        
        # Return name of the qmd; used for linking
        return qmd

    def write_examples_qmd(self):

        from os.path import isfile, isdir
        from os import makedirs
        import tempfile
        import filecmp

        # No examples? Nothing to do!
        if not self.get("examples"): return None

        # Trying to create examples_dir if needed    
        if not isdir(self.config_get("examples_dir")):
            try:
                makedirs(self.config_get("examples_dir"))
            except Exception as e:
                raise Exception(f"cannot create {self.config_get('examples_dir')}: {e}")

        qmd      = f"{self.config_get('examples_dir')}/{self.quartofile()}"
        examples = self.get_example_qmd()

        with open(qmd, "w+") as fid: print(examples, file = fid)
        
        # Return name of the qmd; used for linking
        return qmd


    def __repr_args(self):

        from re import findall, sub
        from html import escape

        res = ""

        # Given the signature, we should have the following parameters
        expected_args = list(self._signature.parameters.keys())
        # These are the available parameters (from the docstring)
        documented_args = [sub("^\*+", "", x.arg_name.strip()) for x in self.get("params")]
        # If self._parent is set this is the man page for a method.
        # if the first argument in list is 'self', remove.
        if self._parent and len(expected_args) > 0 and expected_args[0] == "self":
            expected_args.remove("self")

        # Check if any of the expected arguments is not documented
        missing_args = []
        for ea in expected_args:
            if not ea in documented_args:
                missing_args.append(ea)

        # Counting number of warnings and/or arguments added
        counter = 0

        if len(missing_args) > 0:
            counter += 1
            res += "<ul>"
            for rec in missing_args:
                res += f"<li>WARNING(missing argument definition \"{rec}\" in docstring)</li>"
            res += "</ul>"

        # Count arguments
        res += "<dl class=\"pyp-list param-list\">\n"
        for arg in self.get("params"):
            counter += 1
            # If we get "argument (class)" we separate them
            mtch = findall(r"^(.*)\((.*?)\)$", arg.args[1])
            if len(mtch) > 0:
                arg_name = mtch[0][0].strip()
                arg_cls  = f"<code class=\"argument-class\">{escape(mtch[0][1])}</code>"
            else:
                arg_name = arg.args[1].strip()
                arg_cls  = ""

            #short_arg = re.search("^([\*\w]+)", arg.args[1]).group(1).replace("*", "")
            # Building html table row
            res += "  <dt style = \"white-space: nowrap; font-family: monospace; vertical-align: top\">\n" + \
                   f"   <code id=\"{self.fullname()}:{arg_name}\">{escape(arg_name)}</code>{arg_cls}\n" + \
                   "  </dt>\n" + \
                   f" <dd>{self._add_references(arg.description)}</dd>\n"
                   ####f" <dd>{escape(self._add_references(arg.description))}</dd>\n"

        res += "</dl>"

        # If no arguments or warnings have been added, return None
        # such that we can skip to add the 'Arguments' section.
        return None if counter == 0 else res


    def __repr_raises(self):
        import xml.etree.ElementTree as et
        from html import escape
        res = "<ul class=\"python-raises\">\n"
        for rec in self.get("raises"):
            res += f"<li><code class=\"text-warning\">{rec.type_name}</code>: " + \
                   f"{escape(self._add_references(rec.description))}\n"
        return res + "</ul>\n"


    def __repr__(self):
        import re

        if self.get("short_description") is None:
            res  = "---\ntitle: \"WARNING(short_description missing)\"\n---\n\n"
        else:
            res  = "---\ntitle: \"" + \
                   self._add_references(self.get("short_description")) + \
                   "\"\n---\n\n"

        if self.get("long_description"):
            res += "### Description\n\n"
            res += self._add_references(self.get("long_description"))
        else:
            res += "WARNING(long_description missing)"

        res += "\n\n### Usage\n\n"
        res += "<pre><code class='language-python'>" + \
               f"{self.signature(max_length = 50)}" + \
               "</code></pre>"

        # Function arguments
        tmp = self.__repr_args()
        if tmp is not None:
            res += "\n\n### Arguments\n\n" + tmp

        # Return value
        if self.get("returns"):
            res += "\n\n### Return\n\n"
            if self.get("returns").type_name:
                res += f"<code>{self.get('returns').type_name}</code>: "
            res += f"{self._add_references(self.get('returns').description)}"

        # If is class, append methods
        if self.isclass():

            res += "\n\n### Methods\n\n"
            # Convert package.module.class into package.module
            parent = re.sub(r"\.[^.]*$", "", self.fullname())

            res += "<dl class=\"pyp-list method-list\">\n"
            for name,meth in self.getmembers():
                m_man = ManPage(name, meth, self._config)
                if m_man.get("short_description") is None:
                    short = "WARNING(short_description missing)"
                else:
                    short = m_man.get("short_description")

                # Adding <dt><dd> for current method
                link = m_man.quartofile()
                text = re.sub(f"^{parent}\.", "", m_man.signature(remove_self = True))
                res += "    <dt style = \"white-space: nowrap; font-family: monospace; vertical-align: top\">\n" + \
                       f"       <code>[{text}]({link})</code>\n    </dt>\n" + \
                       f"    <dd>{short}</dd>\n"
            res += "</dl>\n"

 
        # If we have examples:
        if self.get("examples"):
            examples = []
            for tmp in [ex.description for ex in self.get("examples")]:
                # Prepare example and possibly split it.
                tmp       = self._prepare_example(tmp)
                examples += self._split_example(tmp)

            res += "\n\n### Examples\n\n"
            for tmp in examples:
                res += self.__repr_examples(tmp)
            res += "\n"

        # If has documented raises exception
        if len(self.get("raises")) > 0:
            res += "\n\n### Raises\n\n" + self.__repr_raises()

 
        return res

    def get_example_qmd(self):
        import re

        if self.get("short_description") is None:
            res  = "---\ntitle: \"WARNING(short_description missing)\"\n---\n\n"
        else:
            res  = "---\ntitle: \"" + \
                   self._add_references(self.get("short_description")) + \
                   "\"\n---\n\n"

        # If we have examples:
        if self.get("examples"):
            examples = []
            for tmp in [ex.description for ex in self.get("examples")]:
                # Prepare example and possibly split it.
                tmp       = self._prepare_example(tmp)
                examples += self._split_example(tmp)

            res += "\n\n### Examples\n\n"
            for tmp in examples:
                res += self.__repr_examples(tmp, warning = False, error = False)
            res += "\n"

        return res

    def _add_references(self, x):
        import re
        if x is None: return x

        # Replace sphinx refs with quarto refs
        matches = re.findall(r":py:(?:func|class|method):`.*?`", x)

        # If any matches are found, set quarto references properly
        for m in matches:
            # Find basic match
            tmp = re.search("py:(\w+?):`(.*?)(?=`)", m)
            if tmp:
                # Extact typ (func, class, or method) and the 'reference'
                typ,ref = tmp.groups()
                # If format is "name <ref>" we further decompose the match
                ref2 = re.match("^(.*)\s+?<(.*?)>$", ref)
                # Take `text <link>` from the docstring
                if ref2:
                    x = x.replace(m, f"[{ref2.group(1)}]({ref2.group(2)}.qmd)")
                # IF we only have a `word` we expect that it refers
                # to it's current module OR its class (if typ == "method")
                elif re.match("^\w+$", ref):
                    if typ == "method":
                        cls = re.sub(r"\.\w+?$", "", self.fullname())
                        x   = x.replace(m, f"[{ref}]({cls}.{ref}.qmd)")
                    else:
                        x   = x.replace(m, f"[{ref}]({self._obj.__module__}.{ref}.qmd)")
                # Else take whatever we got
                else:
                    x = x.replace(m, f"[{ref}]({ref}.qmd)")

        return x


    def __repr_examples(self, x, warning = True, error = True):
        from re import sub, MULTILINE
        assert isinstance(x, str)
        assert isinstance(warning, bool)
        assert isinstance(error, bool)
        res = "```{python}\n" + \
              "#| echo: true\n"

        if warning:
            res += "#| warning: true\n"
        if error:
            res += "#| error: true\n"

        res += sub("^#:", "#", x, flags = MULTILINE) + \
               "\n```\n\n"
        return res


    def _prepare_example(self, x):
        """prepapre_example(x)
 
        Args:
            x (str): The example extracted from the docstring.
 
        Return:
        str : Modified example to be ready for quarto.
        """
        from re import sub, MULTILINE
        # Comment 'text' (can be included in the py example section)
        x = sub(r"^(?!(>>>))", "## ", x, flags = MULTILINE)
        # Removing empty lines
        x = sub(r"^##\s+?$", "", x, flags = MULTILINE)
        # Remove >>> code identifiers
        x = sub(r"^>>>\s+?", "", x, flags = MULTILINE)
        return x


    def _split_example(self, x):
        """split_example(x)
 
        Args:
            x: str, the example extracted from the docstring.
 
        Return:
        list: List of strings. If we find `#:` at the start of a line
        we split the example at this position in multiple segments.
        """
        from re import split, sub, MULTILINE
        res = split(r"\n(?=#:)", x, flags = MULTILINE)
        # Remove empty lines if any
        for i in range(len(res)):
            res[i] = sub("#:[\s+]?\n", "", res[i], flags = MULTILINE)
        return res


