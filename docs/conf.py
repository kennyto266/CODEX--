# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from datetime import datetime

# Add the source directory to the Python path
sys.path.insert(0, os.path.abspath('../src'))
sys.path.insert(0, os.path.abspath('../'))

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, as shown here.
#

# -- Project information -----------------------------------------------------

project = '港股量化交易系统'
copyright = f'{datetime.now().year}, 港股量化交易团队'
author = '港股量化交易团队'

# The full version, including alpha/beta/rc tags
release = '1.0.0'
version = '1.0.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    # Core Sphinx extensions
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.ifconfig',
    'sphinx.ext.graphviz',

    # Third-party extensions
    'myst_parser',  # Markdown support
    'sphinx_copybutton',  # Copy button for code blocks
    'sphinx.ext.extlinks',  # External links
    'sphinx_rtd_theme',  # Read the Docs theme
    'sphinxext.opengraph',  # Open Graph meta tags
    'sphinxcontrib.bibtex',  # BibTeX citations
    'sphinxcontrib.mermaid',  # Mermaid diagrams
    'sphinx_autodoc_typehints',  # Type hints
    'sphinx_design',  # Modern UI components
    'sphinx_togglebutton',  # Collapsible sections
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    '.pytest_cache',
    '**/__pycache__',
    '**/*.pyc',
    'venv',
    'env',
    '.env',
]

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    # Toc options
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom static files
html_css_files = [
    'css/custom.css',
    'css/code-highlighting.css',
]

html_js_files = [
    'js/custom.js',
    'js/theme-switcher.js',
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Extension configuration -------------------------------------------------

# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
    'sklearn': ('https://scikit-learn.org/stable/', None),
    'fastapi': ('https://fastapi.tiangolo.com/', None),
    'uvicorn': ('https://www.uvicorn.org/', None),
    'pydantic': ('https://docs.pydantic.dev/', None),
}

# -- Options for todo extension ----------------------------------------------

# If this is True, todo and todolist produce output, else they produce nothing.
todo_include_todos = True

# -- Options for napoleon extension ------------------------------------------

# Enable parsing of Google style docstrings
napoleon_google_docstring = True

# Enable parsing of NumPy style docstrings
napoleon_numpy_docstring = True

# Include init docstrings
napoleon_include_init_with_doc = True

# Include private members
napoleon_include_private_with_doc = False

# Use napoleon to parse both docstring formats
napoleon_use_ivar = False

# Use param in Google style docstrings
napoleon_use_param = True

# Use rtype for return type in Google style docstrings
napoleon_use_rtype = True

# -- Autodoc configuration ---------------------------------------------------

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
    'inherited-members': True,
}

# Autodoc typehints
autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'

# -- Autosummary configuration -----------------------------------------------

# Generate autosummary even if no references
autosummary_generate = True

# Use a custom template directory
autosummary_generate_overwrite = True

# -- Graphviz configuration ---------------------------------------------------

graphviz_output_format = 'svg'
graphviz_dot_args = [
    '-Gfontname=SimHei',
    '-Efontname=SimHei',
    '-Nfontname=SimHei',
]

# -- MyST parser configuration -----------------------------------------------

myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

# -- Copy button configuration -----------------------------------------------

copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# -- External links configuration --------------------------------------------

extlinks = {
    'pypi': ('https://pypi.org/project/%s/', '%s'),
    'github': ('https://github.com/%s', '%s'),
    'doi': ('https://doi.org/%s', 'doi:%s'),
}

# -- OpenGraph configuration -------------------------------------------------

ogp_site_url = "https://docs.quant-system.com"
ogp_description_length = 200

# -- BibTeX configuration ----------------------------------------------------

bibtex_bibfiles = ['references.bib']
bibtex_default_style = 'plain'

# -- Mermaid configuration ---------------------------------------------------

mermaid_init_js = """
function MermaidInitPre() {
    // Mermaid initialization code
}
"""

# -- Custom configuration ----------------------------------------------------

# Add custom CSS
def setup(app):
    app.add_css_file('css/custom.css')
    app.add_css_file('css/code-highlighting.css')
    app.add_js_file('js/custom.js')
    app.add_js_file('js/theme-switcher.js')

# -- API documentation configuration -----------------------------------------

# Auto-generate API documentation
apidoc_modules = [
    'src.agents',
    'src.api',
    'src.backtest',
    'src.data_adapters',
    'src.dashboard',
    'src.database',
    'src.strategies',
    'src.trading',
    'src.utils',
]

apidoc_output_dir = 'api/generated'
apidoc_exclude_patterns = [
    '**/tests/**',
    '**/test_*.py',
    '**/*_test.py',
    '**/conftest.py',
    '**/venv/**',
    '**/.venv/**',
    '**/__pycache__/**',
]

# -- Module specific configurations -----------------------------------------

# Suppress warnings for missing references in generated API docs
suppress_warnings = ['ref.citation', 'ref.footnote']

# Allow epic shortcuts like :class:`~pytorch.LSTM` to work correctly
nitpicky = False

# -- Build configuration ----------------------------------------------------

# Number of lines per file to show before and after the matched line.
# Only used if the "include" member of close_matches is also specified
show_authors = True

# Add 'versionadded' and 'versionchanged' directives to the end of the
# description of the documented function, after the description.
add_module_names = True

# -- Performance optimization -----------------------------------------------

# Parallel processing
parallel_read_safe = True
parallel_write_safe = True

# -- Error handling ---------------------------------------------------------

# Fail on warnings (uncomment to ensure documentation quality)
# nitpicky = True  # Warns on missing references
# suppress_warnings = []  # Don't suppress any warnings
