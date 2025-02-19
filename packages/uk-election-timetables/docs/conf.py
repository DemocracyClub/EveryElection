# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "uk-election-timetables"
copyright = "2020, Alex Wilson"
author = "Alex Wilson"

# The short X.Y version
version = "4.2"
# The full version, including alpha/beta/rc tags
release = "4.2.3"


# -- General configuration ---------------------------------------------------

extensions = ["sphinx.ext.autodoc", "recommonmark", "sphinx_markdown_tables"]

templates_path = ["_templates"]

source_suffix = [".rst", ".md"]

html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}


master_doc = "index"

language = None

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

pygments_style = None


# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "uk-election-timetablesdoc"

# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.

epub_title = project
epub_exclude_files = ["search.html"]


# -- Extension configuration -------------------------------------------------
