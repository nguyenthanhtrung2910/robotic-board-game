# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pygments.lexers import PythonLexer
from sphinx.highlighting import lexers
lexers['ipython3'] = PythonLexer()

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
              'sphinx_autodoc_typehints',
              'nbsphinx',
              ]

templates_path = ['_templates']

exclude_patterns = ['build', 'Thumbs.db', '.DS_Store']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'petting_zoo': ('https://pettingzoo.farama.org', None),
    'gymnasium': ('https://gymnasium.farama.org', None),
    'tianshou': ('https://tianshou.org/en/stable', None),
    'numpy': ('https://numpy.org/doc/stable', None),
    'pygame':('https://www.pygame.org/docs', None),
}

html_title = 'Robotic Board Game Documentation'

html_logo = '_static/logo.png'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

nbsphinx_prolog = """
.. raw:: html

    <a href="{{ env.docname.split('/')[-1] }}.ipynb" download="{{ env.docname.split('/')[-1] }}.ipynb">
        <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">
            Download this Notebook
        </button>
    </a>
"""
