#!/usr/bin/env python3
"""Patch and boot-smoke every declared supported Minecraft release."""

import argparse
import io
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
COMMON_RUNTIME_CLASSES = {
    "vanillacord/server/VanillaCord.class",
    "vanillacord/server/QuietException.class",
    "vanillacord/server/ForwardingHelper.class",
    "vanillacord/server/BungeeHelper.class",
}
VELOCITY_RUNTIME_CLASSES = {
    "vanillacord/server/VelocityHelper.class",
    "vanillacord/server/VelocityForwardingParser.class",
    "vanillacord/server/VelocityForwardingParser$ForwardedProperty.class",
    "vanillacord/server/VelocityForwardingParser$ForwardedPlayerData.class",
}


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def java_executable(home: str) -> pathlib.Path:
    name = "java.exe" if os.name == "nt" else "java"
    return pathlib.Path(home) / "bin" / name


def require_java(feature: int) -> pathlib.Path:
    key = f"VANILLACORD_JAVA_{feature}_HOME"
    home = os.environ.get(key, "").strip()
    if not home:
        raise RuntimeError(f"{key} is required for the supported-release matrix")
    java = java_executable(home)
    if not java.is_file():
        raise RuntimeError(f"Java {feature} executable not found: {java}")
    return java


def patcher_java() -> pathlib.Path:
    home = os.environ.get("VANILLACORD_PATCHER_JAVA_HOME", "").strip()
    if not home:
        home = os.environ.get("VANILLACORD_JAVA_21_HOME", "").strip()
    if not home:
        raise RuntimeError("VANILLACORD_PATCHER_JAVA_HOME or VANILLACORD_JAVA_21_HOME is required")
    java = java_executable(home)
    if not java.is_file():
        raise RuntimeError(f"Patcher Java executable not found: {java}")
    return java


def fetch_manifest(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "VanillaCord-supported-matrix/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def velocity_supported(version: str) -> bool:
    parts = version.split(".")
    if parts and parts[0] == "1" and len(parts) >= 2 and parts[1].isdigit():
        return int(parts[1]) >= 13
    return True


def collect_runtime_classfiles(server_jar: pathlib.Path):
    """Collect VanillaCord runtime classes from legacy fat jars or modern bundled jars."""
    classes = {}
    with zipfile.ZipFile(server_jar) as outer:
        for info in outer.infolist():
            name = info.filename
            if name.startswith("vanillacord/") and name.endswith(".class"):
                classes[name] = outer.read(info)
            elif name.startswith("META-INF/versions/") and name.endswith(".jar"):
                with zipfile.ZipFile(io.BytesIO(outer.read(info))) as nested:
                    for nested_info in nested.infolist():
                        nested_name = nested_info.filename
                        if nested_name.startswith("vanillacord/") and nested_name.endswith(".class"):
                            classes[nested_name] = nested.read(nested_info)
    return classes


def validate_runtime_contract(server_jar: pathlib.Path, version: str, java_feature: int):
    classes = collect_runtime_classfiles(server_jar)
    required = set(COMMON_RUNTIME_CLASSES)
    if velocity_supported(version):
        required.update(VELOCITY_RUNTIME_CLASSES)

    problems = []
    missing = sorted(required - classes.keys())
    if missing:
        problems.append("missing injected runtime classes: " + ", ".join(missing))

    max_major = java_feature + 44
    incompatible = []
    for name, data in sorted(classes.items()):
        if not name.startswith("vanillacord/server/"):
            continue
        if len(data) < 8 or data[:4] != b"\xca\xfe\xba\xbe":
            incompatible.append(f"{name}=invalid-classfile")
            continue
        major = int.from_bytes(data[6:8], "big")
        if major > max_major:
            incompatible.append(f"{name}=class-{major}>max-{max_major}")
    if incompatible:
        problems.append("runtime bytecode exceeds target Java: " + ", ".join(incompatible))

    return problems


def wait_for_boot(process, log_path: pathlib.Path, timeout_seconds: int):
    deadline = time.monotonic() + timeout_seconds
    last_text = ""
    while time.monotonic() < deadline:
        if log_path.exists():
            last_text = log_path.read_text(encoding="utf-8", errors="replace")
            if "Done (" in last_text:
                return True, last_text
        if process.poll() is not None:
            return False, last_text
        time.sleep(2)
    if log_path.exists():
        last_text = log_path.read_text(encoding="utf-8", errors="replace")
    return False, last_text


def boot_smoke(java: pathlib.Path, server_jar: pathlib.Path, timeout_seconds: int):
    with tempfile.TemporaryDirectory(prefix="vanillacord-boot-") as temp_dir:
        work = pathlib.Path(temp_dir)
        shutil.copy2(server_jar, work / "server.jar")
        (work / "eula.txt").write_text("eula=true\n", encoding="utf-8")
        (work / "server.properties").write_text(
            "online-mode=false\n"
            "enforce-secure-profile=false\n"
            "server-ip=127.0.0.1\n"
            "server-port=25565\n"
            "motd=VanillaCord supported-release smoke test\n"
            "level-name=world\n"
            "view-distance=2\n"
            "simulation-distance=2\n"
            "spawn-protection=0\n",
            encoding="utf-8",
        )
        log_path = work / "server.log"
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [str(java), "-Xms256M", "-Xmx1536M", "-jar", "server.jar", "nogui"],
                cwd=work,
                stdin=subprocess.PIPE,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            ok, text = wait_for_boot(process, log_path, timeout_seconds)
            returncode = process.poll()
            if ok and process.stdin:
                try:
                    process.stdin.write("stop\n")
                    process.stdin.flush()
                except (BrokenPipeError, OSError):
                    pass
            try:
                process.wait(timeout=30 if ok else 2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        tail = "\n".join(text.splitlines()[-80:])
        return ok, tail, returncode


def emit_failure_details(result):
    """Make stable-gate failures diagnosable directly from the Actions log."""
    print(
        f"FAIL {result['version']} ({result['generation']}, Java {result['java']}): "
        f"{result.get('error', 'unknown failure')}",
        flush=True,
    )
    if "patch_returncode" in result:
        print(f"patch return code: {result['patch_returncode']}", flush=True)
    if "boot_returncode" in result:
        print(f"boot return code: {result['boot_returncode']}", flush=True)
    log_tail = str(result.get("log_tail", "")).strip()
    if log_tail:
        print("--- diagnostic tail ---", flush=True)
        print(log_tail, flush=True)
        print("--- end diagnostic tail ---", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jar")
    parser.add_argument("--matrix", default=str(ROOT / "SUPPORTED_MINECRAFT.json"))
    parser.add_argument("--report", default=str(ROOT / "docs/minecraft-supported-releases.md"))
    parser.add_argument("--json", dest="json_path", default=str(ROOT / "build/minecraft-supported-releases.json"))
    parser.add_argument("--manifest-url", default=os.environ.get("MINECRAFT_MANIFEST_URL", DEFAULT_MANIFEST))
    parser.add_argument("--boot-timeout", type=int, default=int(os.environ.get("VANILLACORD_BOOT_TIMEOUT_SECONDS", "120")))
    args = parser.parse_args()

    patcher = pathlib.Path(args.jar).resolve()
    if not patcher.is_file():
        raise SystemExit(f"VanillaCord jar not found: {patcher}")

    matrix = load_json(pathlib.Path(args.matrix))
    targets = matrix.get("targets", [])
    if not targets:
        raise SystemExit("SUPPORTED_MINECRAFT.json contains no targets")

    manifest = fetch_manifest(args.manifest_url)
    latest_release = manifest["latest"]["release"]
    known_versions = {item["id"] for item in manifest["versions"]}
    current_targets = [item["version"] for item in targets if item.get("current")]
    if current_targets != [latest_release]:
        raise SystemExit(
            f"Supported matrix current target is {current_targets!r}, but Mojang latest release is {latest_release!r}. "
            "Refresh SUPPORTED_MINECRAFT.json before publishing a stable VanillaCord release."
        )

    patch_java = patcher_java()
    results = []
    failures = 0
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)

    for target in targets:
        version = str(target["version"])
        java_feature = int(target["java"])
        generation = str(target["generation"])
        result = {
            "version": version,
            "generation": generation,
            "java": java_feature,
            "policy": "blocking",
            "patch": "pending",
            "jar": "pending",
            "boot": "pending",
            "status": "fail",
        }
        print(f"==> {version} ({generation}, Java {java_feature})", flush=True)

        if version not in known_versions:
            result["patch"] = "not-run"
            result["jar"] = "not-run"
            result["boot"] = "not-run"
            result["error"] = "missing from Mojang version manifest"
            failures += 1
            results.append(result)
            emit_failure_details(result)
            continue

        output = out_dir / f"{version}.jar"
        output.unlink(missing_ok=True)
        patch = subprocess.run(
            [str(patch_java), "-jar", str(patcher), version],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300,
        )
        if patch.returncode != 0:
            result["patch"] = "fail"
            result["jar"] = "not-run"
            result["boot"] = "not-run"
            result["error"] = "patch failed"
            result["patch_returncode"] = patch.returncode
            result["log_tail"] = "\n".join(patch.stdout.splitlines()[-80:])
            failures += 1
            results.append(result)
            emit_failure_details(result)
            continue
        result["patch"] = "pass"

        if not output.is_file() or output.stat().st_size == 0 or not zipfile.is_zipfile(output):
            result["jar"] = "fail"
            result["boot"] = "not-run"
            result["error"] = "patched output is missing, empty, or not a readable JAR"
            failures += 1
            results.append(result)
            emit_failure_details(result)
            continue

        runtime_problems = validate_runtime_contract(output, version, java_feature)
        if runtime_problems:
            result["jar"] = "fail"
            result["boot"] = "not-run"
            result["error"] = "; ".join(runtime_problems)
            failures += 1
            results.append(result)
            emit_failure_details(result)
            continue
        result["jar"] = "pass"

        java = require_java(java_feature)
        ok, log_tail, boot_returncode = boot_smoke(java, output, args.boot_timeout)
        if not ok:
            result["boot"] = "fail"
            result["error"] = f"server did not reach startup marker on Java {java_feature}"
            result["boot_returncode"] = boot_returncode
            result["log_tail"] = log_tail
            failures += 1
            results.append(result)
            emit_failure_details(result)
            continue

        result["boot"] = "pass"
        result["status"] = "pass"
        results.append(result)

    evidence = {
        "schema": "vanillacord-supported-minecraft-results/1",
        "status": "pass" if failures == 0 else "fail",
        "latest_mojang_release": latest_release,
        "manifest": args.manifest_url,
        "matrix_schema": matrix.get("schema"),
        "policy": matrix.get("policy"),
        "results": results,
    }

    json_path = pathlib.Path(args.json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    report_path = pathlib.Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "# VanillaCord supported Minecraft releases",
        "",
        f"Stable-release gate: **{'PASS' if failures == 0 else 'FAIL'}**",
        "",
        "Every listed release is blocking. A green result means VanillaCord patched the Mojang server, produced a readable JAR with a complete runtime helper closure compatible with the declared Java generation, and booted that patched server on the declared Java runtime.",
        "",
        "| State | Minecraft | Generation | Java | Patch | JAR | Boot |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for result in results:
        icon = "🟢" if result["status"] == "pass" else "🔴"
        rows.append(
            f"| {icon} | `{result['version']}` | {result['generation']} | {result['java']} | "
            f"{result['patch']} | {result['jar']} | {result['boot']} |"
        )
    rows.extend(["", f"Mojang latest release at test time: `{latest_release}`.", ""])
    report_path.write_text("\n".join(rows), encoding="utf-8")

    print(report_path.read_text(encoding="utf-8"))
    if failures:
        raise SystemExit(f"{failures} supported Minecraft release(s) failed the stable-release gate")


if __name__ == "__main__":
    main()
