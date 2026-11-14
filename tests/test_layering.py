"""Layer rules from the architecture (AD-2, layers), checked by reading the imports."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
ANTHROPIC_ADAPTER = APP / "adapters" / "anthropic_llm.py"


def _imports(path: Path) -> set[str]:
    package = list(path.relative_to(ROOT).parent.parts) if path.is_relative_to(ROOT) else []
    return _imports_in(path.read_text(encoding="utf-8"), package)


def _imports_in(source: str, package: list[str]) -> set[str]:
    """Full names of the modules imported; `from a import b` counts as `a` and `a.b`.

    Relative imports are resolved against `package` (e.g. `["app", "pipeline"]`).
    """
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - node.level + 1]
                module = ".".join([*base, *([node.module] if node.module else [])])
            else:
                module = node.module or ""
            names.add(module)
            names.update(f"{module}.{alias.name}" for alias in node.names)
    return names


def _top_level_imports(path: Path) -> set[str]:
    return {name.split(".")[0] for name in _imports(path)}


def _python_files(folder: Path) -> list[Path]:
    return sorted(folder.rglob("*.py"))


def test_only_the_anthropic_adapter_imports_the_sdk() -> None:
    importers = [p for p in _python_files(APP) if "anthropic" in _top_level_imports(p)]
    assert importers == [ANTHROPIC_ADAPTER]


@pytest.mark.parametrize("layer", ["pipeline", "ports"])
def test_pipeline_and_ports_import_no_web_framework_or_sdk(layer: str) -> None:
    forbidden = {"fastapi", "starlette", "anthropic"}
    files = _python_files(APP / layer)
    assert files, f"no Python files in app/{layer}"
    offenders = {str(p.relative_to(ROOT)): sorted(_top_level_imports(p) & forbidden) for p in files}
    assert {path: names for path, names in offenders.items() if names} == {}


@pytest.mark.parametrize("layer", ["pipeline", "ports"])
def test_pipeline_and_ports_import_no_adapters_or_web(layer: str) -> None:
    forbidden = ("app.adapters", "app.web")
    offenders = {
        str(p.relative_to(ROOT)): sorted(
            name for name in _imports(p) if any(name == f or name.startswith(f + ".") for f in forbidden)
        )
        for p in _python_files(APP / layer)
    }
    assert {path: names for path, names in offenders.items() if names} == {}


def test_import_scan_resolves_full_and_relative_names() -> None:
    source = "from app import adapters\nfrom ..web import health\nimport app.web.texts\n"
    names = _imports_in(source, ["app", "pipeline"])
    assert {"app.adapters", "app.web.health", "app.web.texts"} <= names


def test_import_scan_sees_imports_inside_functions(tmp_path: Path) -> None:
    path = tmp_path / "m.py"
    path.write_text("def f():\n    import anthropic.types\n    from fastapi import X\n", encoding="utf-8")
    assert _top_level_imports(path) == {"anthropic", "fastapi"}
