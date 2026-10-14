import importlib
import pkgutil

REGISTRY = {}


def create_analysis(type, server, reader, surface_reader=None):
    klass = REGISTRY.get(type)
    if klass:
        return klass(server, reader, surface_reader)
    return None


def register_analysis(type, klass):
    REGISTRY[type] = klass


def create_id_generator():
    count = 0
    while True:
        count += 1
        yield f"analysis_{count}"


def load_all_analysis():
    """Import the analysis modules and packages so they register themselves"""
    for module in pkgutil.iter_modules(__path__):
        if not module.name.startswith("_"):
            importlib.import_module(f"{__name__}.{module.name}")


ANALYSIS_ID = create_id_generator()

__all__ = ["ANALYSIS_ID", "create_analysis", "load_all_analysis", "register_analysis"]
