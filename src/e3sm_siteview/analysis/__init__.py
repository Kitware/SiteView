import importlib.util
from pathlib import Path

REGISTRY = {}


def create_analysis(type, server, reader):
    klass = REGISTRY.get(type)
    if klass:
        return klass(server, reader)
    return None


def register_analysis(type, klass):
    REGISTRY[type] = klass


def create_id_generator():
    count = 0
    while True:
        count += 1
        yield f"analysis_{count}"


def load_all_analysis():
    for module_path in Path(__file__).parent.glob("*.py"):
        if module_path.stem[0] == "_":
            continue
        name = module_path.stem
        spec = importlib.util.spec_from_file_location(name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)


ANALYSIS_ID = create_id_generator()

__all__ = ["ANALYSIS_ID", "create_analysis", "load_all_analysis", "register_analysis"]
