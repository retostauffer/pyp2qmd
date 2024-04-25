#!/usr/bin/env python3
# -------------------------------------------------
# Building quarto manual pages for python package
# -------------------------------------------------

### Tutorial
##extract = mydoc.extract.PyExtract(source)
##add = extract.extract('add')

import sys
import os
import re
import yaml
import re
import argparse
from importlib import import_module # Dynamic module import
import inspect                      # Find functions/classes in package
import mydocstring                  # Parsing functions and classes (extracting docstring)
import docstring_parser             # Parsing docstring

class docParser:
    def __init__(self, file):
        if not isinstance(file, str):
            raise TypeError("argument `file` must be str")
        if not os.path.isfile(file):
            raise FileNotFoundError(f"file \"{file}\" not found")

        try:
            with open(file, "r") as fid:
                self._src = "".join(fid.readlines())
        except Exception as e:
            raise Exception(e)

        # Find functions
        fun = self.find_functions()

    def find_functions(self):
        pattern = re.compile(r"^def\s(.*)(?=(\())", re.M)
        function_names = []
        for rec in pattern.findall(self.source()):
            function_names.append(rec[0])

        print(f"[DEV] {function_names=}")
        return function_names

        
    def source(self):
        return self._src

def parse_input_args():

    # Allowed action options
    allowed_action = ["init", "document"]

    import argparse
    parser = argparse.ArgumentParser("Creating qmd documentation from python package")
    parser.add_argument("action", nargs = 1, type = str,
            help = f"Action to perform, one of: {', '.join(allowed_action)}")
    parser.add_argument("-p", "--package", type = str,
            help = "Name of the python package.")
    parser.add_argument("-o", "--output_dir", type = str, default = "_quarto",
            help = "Name of the output directory to store the qmd file")
    parser.add_argument("--overwrite", default = False, action = "store_true",
            help = "Only used if action = create; will overwrite _quarto.yml if needed.")
    parser.add_argument("--man_dir", type = str, default = "man",
            help = "Folder to store the function/class manuals qmds, " + \
                    "ceated inside the --output_dir folder. Must start with [A-Za-z].")
    parser.add_argument("--docstringstyle", type = str, default = "GOOGLE",
            help = "Docstring type (format).")
    parser.add_argument("--include_hidden", default = False, action = "store_true",
            help = "If set, hidden functions and methods will also be documented " + \
                    "(functions/methods starting with _ or __)")

    # Parsing input args
    args = parser.parse_args()

    args.action = args.action[0]
    if not args.action in allowed_action:
        parser.print_help()
        sys.exit("\nUsage error: invalid \"action\" (see help).")

    if args.package is None:
        parser.print_help()
        sys.exit("\nUsage error: argument -p/--package must be set.")

    ymlfile = f"{args.output_dir}/_quarto.yml"
    if args.action == "create" and isfile(ymlfile):
        parser.print_help()
        sys.exit(f"\nUsage error: action is set to \"{args.action}\" " + \
                 f"but the file \"{ymlfile}\" " + \
                 f"already exists. Remove folder \"{args.output_dir}\" or use " + \
                 f"--overwrite; be aware, will overwrite the existing \"{ymlfile}\".")

    if not re.match("^[A-Za-z]", args.man_dir):
        parser.print_help()
        sys.exit(f"\nUsage error: man_dir must start with [A-Za-z].")

    return args


def create_quarto_yml(args):
    """

    Returns:
    bool: Returns `True` if the yml file is created the first time
    by calling this function, else `False` (file did already exist).
    """
    import os
    ymlfile = f"{args.output_dir}/_quarto.yml"

    if args.action == "init":
        res = True
        # If yml already exists and overwrite = False, error
        if os.path.isfile(ymlfile) and not args.overwrite:
            raise Exception(f"action = {args.action}, overwrite = {args.overwrite} " + \
                    f"but file \"{ymlfile}\" already exists; stop!")

        # If output directory does not yet exist, create.
        if not os.path.isdir(args.output_dir):
            try:
                os.makedirs(args.output_dir)
            except:
                raise Exception(f"Unable to create output folder \"{args.output_dir}\"")

        # Content of the yml file
        content = {"project": {"type": "website"},
                     "website": {"title": args.package,
                        "navbar": {"search": True,
                            "right": [{"icon": "github", "href": "https://github.com/dummy/entry", "aria-label": "gsdata GitHub"}]},
                        "sidebar": {"collapse-level": 1,
                           "contents": [{"text": "Home", "file": "index.qmd"}]
                        }
                     },
                     "format": {"html": {"theme": ["quarto", "pyp.scss"]}},
                     "execute": {"cache": True}
                   }

        # Else create (overwrite) the file
        with open(ymlfile, "w+") as fid: fid.write(yaml.dump(content))

    # Else (not init): Ensure the output folder and the yml file exists, else
    # init must be used.
    else:
        res = False
        if not os.path.isdir(args.output_dir):
            raise Exception(f"Output folder \"{args.output_dir}\" does not exist. " + \
                    "You may first need to call the script with action = init")
        elif not os.path.isfile(ymlfile):
            raise Exception(f"yml file \"{ymlfile}\" does not exist. " + \
                    "You may first need to call the script with action = init")

    # Create references dir if not existing
    refdir = os.path.join(args.output_dir, args.man_dir)
    if not os.path.isdir(refdir):
        try:
            os.makedirs(refdir)
        except Exception as e:
            raise Exception(e)

    return res

def write_index(args):
    """
    Write index

    Returns:
    bool : True if index was newly created, else False.
    """
    import os
    import re
    from datetime import datetime as dt
    qmdfile = f"{args.output_dir}/index.qmd"
    res = False
    if not os.path.isfile(qmdfile):
        res = True
        # Sorry, indent is important
        content = f"""
        # {args.package} Package Documentation

        This page has been automatically generated by
        pyp2qmd (Python package documentation to quarto),
        converting the docstrings of all loaded functions
        and methods available via `{args.package}.*` into
        quarto markdown files (`.qmd).

        ### Function reference

        Contains the documentation/reference of all functions,
        including description, usage, arguments, exceptions,
        as well as evaluated examples.

        ### Class reference

        The documentation/reference of all classes including
        description, usge, arguments, _methods_, exceptions,
        and evaluated examples (if any).

        For each method listed on the class reference page,
        a quarto markdown file is generated as well, altough
        not listed in the navigation. The documentation can
        be accessed by visiting the class reference, and then
        click on the method of interest.
        
        _Generated: {dt.now() : %Y-%m-%d %H:%M}_.
        """

        # There is for sure a single nice regex instead of
        # this approach (currently the regex kills empty lines).
        content = re.sub(r"^(?!\s*$)\s+", "", content, flags = re.MULTILINE)
        with open(qmdfile, "w+") as fid: fid.write(content)

    return res


def write_sass(args):
    """
    Write sass

    Returns:
    bool : True sass file was created/replaced, else False.
    """
    import os
    scssfile = f"{args.output_dir}/pyp.scss"
    res = False
    if not os.path.isfile(scssfile) or args.action == "init":
        res = True
        # Sorry, indent is important
        content = """
/*-- scss:defaults --*/
// Base document colors
$body-bg: white;
$body-color: black;
$primary: #0d6efd;
$link-color: #4287f5;

/*-- scss:custom --*/

// Usage code
pre {
    code {
        &.language-python {
            white-space: pre;
            font-family: monospace;
            vertical-align: top;
            color: $primary;
            font-weight: 500;
        }
    }
}

// Styling of the <dl> lists
dl.pyp-list {
    dd {
        margin-left: 2em;
    }
}
div.cell-output-display {
    margin: 1em 0;
    padding: 0.5em 0.5em;
    pre {
        background-color: #e0e7ff;
    }
}
        """
        with open(scssfile, "w+") as fid: fid.write(content)

    return res

def update_quarto_yml(args, section, mans):

    import yaml

    assert isinstance(section, str)
    assert isinstance(mans, dict)
    assert all([isinstance(x, str) for x in mans])
    ymlfile = f"{args.output_dir}/_quarto.yml"

    # Read existing 
    with open(ymlfile, "r") as fid:
        content = yaml.load("".join(fid.readlines()), yaml.SafeLoader)

    # Dictionary to extend the content
    tmp = []
    for key,val in mans.items():
        tmp.append({"text": key, "file": val})
    tmp = {"section": section, "contents": tmp}

    # Append and overwrite _quarto.yml with new content
    content["website"]["sidebar"]["contents"].append(tmp)
    with open(ymlfile, "w+") as fid: fid.write(yaml.dump(content))

def extract_docstring(obj, style, include_hidden):
    dstyle = getattr(docstring_parser.DocstringStyle, style.upper())

    # If parent is None, extract docstring of main function or class.
    class_docstring = docstring_parser.parse(inspect.getdoc(obj), dstyle)
    if class_docstring:
        res = [class_docstring, inspect.signature(obj), obj.__module__]
    else:
        res = [None, None, None]

    return res

    ## If parent is a class object we extractt he members of that object,
    ## i.e., the methods of a class. Only meaningful for classes, obviously.
    #else:
    #    # Extract method/function docstrings
    #    for name,func in get_members(obj).items():

    #        name = re.search(r"[^.]+$", name).group(0)
    #        if not include_hidden and name.startswith("_"): continue

    #        # Else check if is function
    #        if inspect.isfunction(func):
    #            try:
    #                doc = docstring_parser.parse(inspect.getdoc(func), dstyle)
    #            except Exception as e:
    #                print(f"Problem extracting docstring from:   {func.__name__} ({name})")
    #                raise Exception(e)

    #            # Setting up the displayed name for the manuals; a combination
    #            # of the parent `obj` and the visible name of the function.
    #            fn_name = ".".join([parent.fullname(), func.__name__])

    #            fn_module = re.sub(f"^{package}\.", "", obj.__module__)
    #            docstrings[fn_name] = {"docstring": doc,
    #                                   "signature": inspect.signature(func),
    #                                   "module":    ".".join([func.__module__, obj.__name__])}

    #            # For this function (method) we'll also write 
    #            # a qmd page, tough it will not be added/included
    #            # in the navigation.
    #            fn_man = py2quarto(func, package, args.include_hidden)
    #            print(f"[DEVEL]     - adding man page for method {fn_man.fullname()}")
    #            fn_qmdfile = os.path.join(args.output_dir, args.man_dir,
    #                                      f"{fn_name}.qmd")
    #                                      #f"{fn_fullname()}.qmd")
    #            print(f"              {fn_qmdfile}")
    #            with open(fn_qmdfile, "w+") as fid: print(fn_man, file = fid)

    #return docstrings

class manPage:
    def __init__(self, name, obj, args, parent = None):
        # parent (None, str): If str, this will be removed from full name.
        if not isinstance(name, str):
            raise TypeError("argument `name` must be str")
        if not inspect.isfunction(obj) and not inspect.isclass(obj):
            raise TypeError("argument `obj` must be function or class")
        if not isinstance(parent, type(None)) and not isinstance(parent, str):
            raise TypeError("argument `parent` must be None or str")

        self._name   = name
        self._obj    = obj
        self._parent = parent
        self._include_hidden = args.include_hidden

        self._doc, self._signature, self._module = \
                extract_docstring(obj, args.docstringstyle, args.include_hidden)

    def fullname(self):
        if re.match(f"^{self._module}", self._name):
            return self._name
        else:
            return f"{self._module}.{self._name}"

    def quartofile(self):
        return f"{self.fullname()}.qmd"

    def isclass(self):
        return inspect.isclass(self._obj)

    def isfunction(self):
        return inspect.isfunction(self._obj)

    def _format_signature(self, name, max_length = 50):
        """
        formatting of signature to get some line breaks in output
        """

        n = max_length - len(name) - 1
        formatted_params = []
        tmp = []
        for k,p in self._signature.parameters.items():
            tmp_len = max(0, sum([len(x) for x in tmp]) + (len(tmp) - 1) * 2)
            if (tmp_len + len(str(p)) + 1) <= n:
                tmp.append(str(p))
            else:
                formatted_params.append(", ".join(tmp))  
                tmp = [str(p)]
        # End   
        if len(tmp) > 0: formatted_params.append(", ".join(tmp))
            
        spacers = "".join([" "] * len(name))
        return name + "(" + f",<br/>{spacers}".join(formatted_params) + ")"   

    def signature(self, max_length = None):
        name = self._name
        # Remove ^parent. if self._parent is set
        if isinstance(self._parent, str):
            name = re.sub(f"^{self._parent}\.", "", self._name)
        else:
            name = self._name
        
        if isinstance(max_length, int) and max_length > 20:
            return self._format_signature(name)
        return name + str(self._signature)

    def getmembers(self):
        members = []
        for rec in inspect.getmembers(self._obj):
            # requires three independent ifs here
            if rec[0].startswith("__"): continue
            if not inspect.isfunction(rec[1]) and not inspect.isclass(rec[1]): continue
            if not self._include_hidden and rec[1].__name__.startswith("_"): continue
            members.append((f"{self.fullname()}.{rec[0]}", rec[1]))
        return members

    def get(self, attr):
        assert isinstance(attr, str), "argument `attr` must be of type str"
        if not hasattr(self._doc, attr):    return None
        else:                               return getattr(self._doc, attr)


    def _repr_args(self):

        res = ""

        # Given the signature, we should have the following parameters
        expected_args = list(self._signature.parameters.keys())
        # These are the available parameters (from the docstring)
        documented_args = [x.arg_name for x in self.get("params")]
        missing_args = []
        for ea in expected_args:
            if not ea in documented_args:
                missing_args.append(ea)

        if len(missing_args) > 0:
            res += "<ul>"
            for rec in missing_args:
                res += f"<li>WARNING(missing argument definition \"{rec}\" in docstring)</li>"
            res += "</ul>"


        res += "<dl class=\"pyp-list param-list\">\n"
        for arg in self.get("params"):
            short_arg = re.search("^([\*\w]+)", arg.args[1]).group(1).replace("*", "")
            # Building html table row
            res += "  <dt style = \"white-space: nowrap; font-family: monospace; vertical-align: top\">\n" + \
                   f"   <code id=\"packagename_:_{short_arg}\">{arg.args[1]}</code>\n" + \
                   "  </dt>\n" + \
                   f" <dd>{arg.description}</dd>\n"

        return res + "</dl>"

    def __repr__(self):
        if self.get("short_description") is None:
            res  = "## WARNING(short_description missing) {.unnumbered}\n\n"
        else:
            res  = "## " + self.get("short_description") + " {.unnumbered}\n\n"

        if self.get("long_description"):
            res += "### Description\n\n"
            res += self._adjust_references(self.get("long_description"))
        else:
            res += "WARNING(long_description missing)"

        res += "\n\n### Usage\n\n"
        res += "<pre><code class='language-python'>" + \
               f"{self.signature()}" + \
               "</code></pre>"

        # Function arguments
        res += "\n\n### Arguments\n\n"
        res += self._repr_args()

        # Return value
        if self.get("returns"):
            res += "\n\n### Return\n\n"
            res += f"{self.get('returns').description}"

        # If is class, append methods
        if self.isclass():

            res += "\n\n### Methods\n\n"
            # Convert package.module.class into package.module
            parent = re.sub(r"\.[^.]*$", "", self.fullname())

            res += "<dl class=\"pyp-list method-list\">\n"
            for name,meth in man.getmembers():
                m_man = manPage(name, meth, args)
                if m_man.get("short_description") is None:
                    short = "WARNING(short_description missing)"
                else:
                    short = m_man.get("short_description")

                # Skipping main class (else infinite recursion)
                #if key == self._name: continue
                #link = ".".join([self.fullname(), re.search(r"[^.]+$", key).group(0)]) + ".qmd"
                link = m_man.quartofile()
                text = re.sub(f"^{parent}\.", "", m_man.signature())
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
                res += self._repr_examples(tmp)
            res += "\n"
 
        return res

    def _adjust_references(self, x):
        import re
        if x is None: return x

        # Replace sphinx refs with quarto refs
        matches = re.findall(r":py:(?:func|class):`.*?`", x)
        for m in matches:
            # Find basic match
            tmp = re.search("`(.*?)(?=`)", m).group(1)
            if tmp:
                # If format is "name <ref>" we further decompose the match
                tmp2 = re.match("^(.*)\s+?<(.*?)>$", tmp)
                if tmp2:
                    x = x.replace(m, f"[{tmp2.group(1)}]({tmp2.group(2)}.qmd)")
                else:
                    x = x.replace(m, f"[{tmp}]({tmp}.qmd)")

        return x

    def _repr_examples(self, x):
        assert isinstance(x, str)
        res = "```{python}\n" + \
              "#| echo: true\n" + \
              "#| error: true\n" + \
              "#| warning: true\n" + \
              x + \
              "\n```\n\n"
        return res

    def _prepare_example(self, x):
        """prepapre_example(x)
 
        Args:
            x (str): The example extracted from the docstring.
 
        Return:
        str : Modified example to be ready for quarto.
        """
        # Comment 'text' (can be included in the py example section)
        x = re.sub(r"^(?!(>>>))", "## ", x, flags = re.MULTILINE)
        # Removing empty lines
        x = re.sub(r"^##\s+?$", "", x, flags = re.MULTILINE)
        # Remove >>> code identifiers
        x = re.sub(r"^>>>\s+?", "", x, flags = re.MULTILINE)
        return x
 
    def _split_example(self, x):
        """split_example(x)
 
        Args:
            x: str, the example extracted from the docstring.
 
        Return:
        list: List of strings. If we find `#:` at the start of a line
        we split the example at this position in multiple segments.
        """
        return re.split(r"\n(?=#:)", x, flags = re.MULTILINE)


# Testing a function
def py2quarto(obj, package, include_hidden = False):
    """py2quarto(obj)

    Args:
        obj: function or class.
        package (str): name of the package for which the documentation
            is created.
        include_hidden (bool): Defaults to `False`. If set,
            hidden functions and methods (_*, __*) will also
            be documented.
    """

    if not inspect.isfunction(obj) and not inspect.isclass(obj):
        raise TypeError("argument `obj` must be a function or class")
    if not isinstance(package, str):
        raise TypeError("argument `package` must be str")
    if not isinstance(include_hidden, bool):
        raise TypeError("argument `include_hidden` must be boolean True or False")


    docstrings = extract_docstrings(obj, None, args.docstringstyle, include_hidden)

    # Generate manPage object
    u = manPage(package    = args.package,
                typ        = "function" if inspect.isfunction(obj) else "class",
                name       = obj.__name__,
                docstrings = docstrings)

    if inspect.isclass(obj):
        docstrings = extract_docstrings(obj, u, args.docstringstyle, include_hidden)
        sys.exit(333)

    # Returning object of class manPageFunction or manPageClass
    return u

def get_members(pkg, predicate = None):
    from inspect import getmembers
    result = {}
    # Extract all members (given predicate) which have
    # a __qualname__ (functions, classes), the rest will be ignored
    for rec in getmembers(pkg, predicate):
        try:
            result[".".join([rec[1].__module__, rec[1].__qualname__])] = rec[1]
        except:
            pass
    return result

# -------------------------------------------------
# -------------------------------------------------
if __name__ == "__main__":

    # Parsing user args
    args = parse_input_args()

    # If args.action is init, crate _quarto.yml
    yml_newly_created = create_quarto_yml(args)

    # Wirte sass (if not existing _or_ action = "init")
    write_sass(args)
    # Write index (if not existing)
    write_index(args)

    # Trying to import the module
    try:
        pkg = import_module(args.package)
    except Exception as e:
        raise Exception(e)

    # Extracting functions and classes
    import inspect
    functions = inspect.getmembers(pkg, inspect.isfunction)
    classes   = inspect.getmembers(pkg, inspect.isclass)

    functions = dict(zip([x[0] for x in functions], [x[1] for x in functions]))
    classes   = dict(zip([x[0] for x in classes], [x[1] for x in classes]))

    #print(functions.keys())
    #print(classes.keys())
    #print("\n\n")

    #functions = {"darken": functions["darken"]}
    #classes   = {"sequential_hcl": classes["sequential_hcl"]}
    
    # -------------------------------------------------
    # Create man pages for functions
    # -------------------------------------------------
    man_func_created = {}
    for name,func in functions.items():
        print(f"[DEVEL] Create man page function {name}")
        man = manPage(name, func, args)
        qmd = f"{args.man_dir}/{man.quartofile()}"
        with open(f"{args.output_dir}/{qmd}", "w+") as fid:
            print(man, file = fid)
        man_func_created[name] = qmd

    print(f"Number of function manuals created: {len(man_func_created)}")

    # Adding Function references to _quarto.yml
    if yml_newly_created and len(man_func_created) > 0:
        update_quarto_yml(args, "Function reference", man_func_created)


    # -------------------------------------------------
    # Create man pages for classtions
    # -------------------------------------------------
    man_class_created = {}
    man_meth_created  = {}
    for name,cls in classes.items():
        print(f"[DEVEL] Create man page class {name}")
        man = manPage(name, cls, args)
        qmd = f"{args.man_dir}/{man.quartofile()}"
        with open(f"{args.output_dir}/{qmd}", "w+") as fid:
            print(man, file = fid)
        man_class_created[name] = qmd

        # Now do the same for all methods belonging to the current class (if any)
        for name,meth in man.getmembers():
            if not args.include_hidden and meth.__name__.startswith("_"): continue
            print(f"[DEVEL]   + method page for {name}")
            parent = re.sub(r"\.[^.]*$", "", man.fullname())
            m_man = manPage(name, meth, args, parent = parent)
            m_qmd = f"{args.man_dir}/{m_man.quartofile()}"
            with open(f"{args.output_dir}/{m_qmd}", "w+") as fid:
                print(m_man, file = fid)
            man_meth_created[name] = m_qmd
    

    print(f"Number of class manuals created: {len(man_class_created)}")

    # Adding Function references to _quarto.yml
    if yml_newly_created and len(man_class_created) > 0:
        update_quarto_yml(args, "Class reference", man_class_created)


