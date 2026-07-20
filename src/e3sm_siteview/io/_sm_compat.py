"""ParaView-optional compatibility shim.

QuickView loads these algorithms as ParaView plugins, where ``smproxy`` /
``smproperty`` / ``smdomain`` register server-manager proxies and expose the
``Set*`` methods to the GUI. SiteView runs pure VTK with no ParaView, so here
those decorators degrade to no-ops and the classes are configured directly
(call the ``Set*`` methods, wire with ``SetInputConnection`` / ``Update``).
"""
import sys

try:  # ParaView present (e.g. running inside pvpython)
    from paraview import print_error, print_warning
    from paraview.util.vtkAlgorithm import smdomain, smproperty, smproxy

    HAS_PARAVIEW = True
except ImportError:  # pure VTK (SiteView)
    HAS_PARAVIEW = False

    def print_error(*args):
        print(*args, file=sys.stderr)

    def print_warning(*args):
        print(*args, file=sys.stderr)

    class _NoOp:
        """No-op stand-in for a server-manager decorator namespace.

        Handles every shape the plugins use: ``@smproxy.filter()``,
        ``@smproxy.source(name=...)``, ``@smproperty.xml("...")``,
        ``@smproperty.input(name=..., port_index=1)``,
        ``@smdomain.datatype(dataTypes=[...])`` and method decorators such as
        ``@smproperty.dataarrayselection(name=...)``.
        """

        def __getattr__(self, _name):
            return self

        def __call__(self, *args, **kwargs):
            # @dec applied directly to a class/function
            if len(args) == 1 and not kwargs and callable(args[0]):
                return args[0]

            # @dec(...) -> return a passthrough decorator
            def _passthrough(obj):
                return obj

            return _passthrough

    smproxy = smproperty = smdomain = _NoOp()

__all__ = [
    "HAS_PARAVIEW",
    "print_error",
    "print_warning",
    "smdomain",
    "smproperty",
    "smproxy",
]
