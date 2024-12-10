# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

project = 'Robotic Board Game'
copyright = '2024, Nguyen Thanh Trung'
author = 'Nguyen Thanh Trung'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.viewcode',
              'sphinx.ext.intersphinx',
              'sphinx.ext.autosectionlabel',
              'sphinx.ext.mathjax',
              'sphinx_autodoc_typehints'
              ]

templates_path = ['_templates']

exclude_patterns = ['build', 'Thumbs.db', '.DS_Store']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pygame_menu': ('https://pygame-menu.readthedocs.io/en/latest', None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']