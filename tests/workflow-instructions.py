"""Check workflow entry points, canonical references and bootstrap regressions offline."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def entry_errors() -> list[str]:
    errors = []
    for path in sorted((ROOT / "workflows").glob("*.md")):
        if path.name == "PIPELINE.md":
            continue
        text = path.read_text()
        for label, pattern in (("invocation", r"^Invocation: "), ("guard", r"^## Guard\b")):
            if not re.search(pattern, text, re.M):
                errors.append(f"{path.name}: missing {label}")
    return errors


def reference_errors() -> list[str]:
    errors = []
    for path in sorted((ROOT / "workflows").glob("*.md")):
        for citation in re.findall(r"`([^`\n]+ → #{2,4} [^`\n]+)`", path.read_text()):
            source, sections = citation.split(" → ", 1)
            targets = [ROOT / group / (source.removesuffix(".md") + ".md")
                       for group in ("rules", "workflows")]
            targets = [target for target in targets if target.is_file()]
            if not targets:
                continue  # Project-specific paths are resolved in the consumer repository.
            headings = re.split(r" → (?=#{2,4} )", sections)
            if not any(all(re.search(r"^" + re.escape(heading) + r"\s*$",
                                     target.read_text(), re.M) for heading in headings)
                       for target in targets):
                errors.append(f"{path.name}: missing canonical section in {citation}")
    return errors


def bootstrap_errors() -> list[str]:
    errors = []
    globals_text = (ROOT / "rules/workflow-globals.md").read_text()
    if "except `/phase-pipeline` and `/spec-run`" not in globals_text:
        errors.append("workflow-globals: phase-transition exceptions are not explicit")
    for path in (ROOT / "rules").glob("phase-*.md"):
        if "Always load full context regardless" in path.read_text():
            errors.append(f"{path.name}: unconditional reload contradicts inherited bootstrap")
        if "<AI_DIR>/../.ai/" in path.read_text():
            errors.append(f"{path.name}: umbrella path resolves to local context")
    classifier = (ROOT / "rules/workflow-reference.md").read_text()
    if re.search(r"S2\s*=\s*1\.5", classifier):
        errors.append("workflow-reference: component count is fractional")
    orchestrator = (ROOT / "workflows/spec-run.md").read_text()
    if not re.search(r"(?is)Step 0.*?phase-discovery.*?Step 0 in full", orchestrator):
        errors.append("spec-run: discovery bootstrap is bypassed")
    return errors


if __name__ == "__main__":
    failures = entry_errors() + reference_errors() + bootstrap_errors()
    for failure in failures:
        print("FAIL:", failure)
    raise SystemExit(bool(failures))
