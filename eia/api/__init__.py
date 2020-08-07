from .series import Series
from .geoset import Geoset
from .category import Category
from .series_category import SeriesCategory

# FIXME:40 The relation API doesn't appear to work at the moment.
# from .relation import Relation

__all__ = [
    "Series",
    "Geoset",
    # "Relation",
    "Category",
    "SeriesCategory",
]
