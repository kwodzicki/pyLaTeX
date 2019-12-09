import setuptools
from distutils.util import convert_path

main_ns  = {};
ver_path = convert_path("pyLaTeX/version.py");
with open(ver_path) as ver_file:
  exec(ver_file.read(), main_ns);

setuptools.setup(
  name             = "pyLaTeX",
  description      = "Package for compiling and converting LaTeX documents", 
  url              = "",
  author           = "Kyle R. Wodzicki",
  author_email     = "wodzicki@tamu.com",
  version          = main_ns['__version__'],
  packages         = setuptools.find_packages(),
  install_requires = [ "pandoc" ],
  scripts          = ['bin/LaTeX2docx',
                      'bin/compileLaTeX'],
  zip_safe         = False,
);
