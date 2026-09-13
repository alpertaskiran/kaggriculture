import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Kaggriculture submission artifact.")
    parser.add_argument("--output", type=Path, default=Path("artifacts/submission"))
    parser.add_argument("--zip", dest="archive", type=Path, default=Path("artifacts/submission.zip"))
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    shutil.copy2(root / "main.py", output / "main.py")
    shutil.copytree(root / "src" / "agriculture_kaggle", output / "agriculture_kaggle")
    if output.joinpath("main.py").stat().st_size > 100 * 1024 * 1024:
        raise ValueError("submission exceeds 100 MiB")
    with tempfile.TemporaryDirectory() as tmp:
        check_dir = Path(tmp)
        shutil.copytree(output, check_dir / "submission")
        sys.path.insert(0, str(check_dir / "submission"))
        try:
            namespace = {}
            compiled = compile(
                (check_dir / "submission" / "main.py").read_text(),
                "main.py",
                "exec",
            )
            exec(compiled, namespace)  # noqa: S102 - validating the user submission entrypoint
            if not callable(namespace.get("agent")):
                raise TypeError("packaged main.py must expose callable agent")
        finally:
            sys.path.pop(0)
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.archive, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in output.rglob("*"):
            if file.is_file():
                archive.write(file, file.relative_to(output))
    print(f"submission directory: {output}")
    print(f"submission archive: {args.archive.resolve()}")
    if args.submit:
        subprocess.run(["kaggle", "competitions", "submit", "-c", "kaggriculture",
                        "-f", str(args.archive)], check=True)


if __name__ == "__main__":
    main()
