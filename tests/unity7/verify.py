#!/usr/bin/env python3
"""Compile port probes using real IL2CPP headers; optionally diagnose native TUs.

Run from a Visual Studio x64 developer environment. The prepared source tree
must be disposable and must contain generated/UnityVersion.inc. This tool never
edits an installed Unity editor or the input source tree.
"""
# Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
import argparse
import json
import locale
from pathlib import Path
import re
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-root", type=Path, required=True)
    parser.add_argument("--unity-il2cpp", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnose", action="store_true")
    args = parser.parse_args()
    compiler = shutil.which("cl.exe")
    if not compiler:
        parser.error("cl.exe is missing; use a Visual Studio x64 developer environment")
    runtime = args.prepared_root.resolve() / "libil2cpp"
    native = runtime / "hybridclr"
    if not (native / "generated/UnityVersion.inc").is_file():
        parser.error("prepared root has no generated Unity version")
    version_text = (native / "generated/UnityVersion.inc").read_text(encoding="utf-8-sig")
    version = int(re.search(r"#define HYBRIDCLR_UNITY_VERSION (\d+)", version_text).group(1))
    output = args.output.resolve()
    if output.exists():
        parser.error("output must not exist; retain previous logs and use a new path")
    if output.is_relative_to(runtime):
        parser.error("output must be outside the input source tree")
    output.mkdir(parents=True)
    external = args.unity_il2cpp.resolve() / "external"
    flags = ["/nologo", "/EHsc", "/std:c++17", "/Zc:__cplusplus", "/utf-8", "/bigobj",
             "/MT", "/DWIN32", "/D_WINDOWS", "/DUNICODE", "/D_UNICODE",
             "/DRUNTIME_IL2CPP=1", "/DMONO_NET_BCL=0", "/DIL2CPP_DEBUG=0",
             "/DBASELIB_INLINE_NAMESPACE=il2cpp_baselib", f"/I{runtime}",
             f"/I{external / 'baselib/Include'}",
             f"/I{external / 'baselib/Platforms/Windows/Include'}",
             f"/I{external / 'google/sparsehash'}",
             f"/FI{native / 'Il2CppVersionCompatibleDefs.h'}"]
    experimental = ["/DHYBRIDCLR_UNITY7_EXPERIMENTAL=1"]
    tests = Path(__file__).resolve().parent
    report = {"scope": "Win64 C++ source probes; no IL2CPP Player or mobile execution",
              "unity_version_macro": version,
              "checks": [], "translation_units": [], "excluded": []}

    def compile_to_log(name, tail, opt_in=True):
        command = [compiler, *flags, *(experimental if opt_in else []), *map(str, tail)]
        result = subprocess.run(command, cwd=output, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output / (name + ".log")).write_bytes(result.stdout)
        return result.returncode, result.stdout.decode(locale.getencoding(), errors="replace")

    code, text = compile_to_log("default-version-guard", ["/Zs", tests / "generic_context.cpp"], False)
    guard_passed = (code != 0 and "Unity 7 native support is incomplete" in text) if version >= 70000000 else code == 0
    report["checks"].append({"name": "default-version-guard", "passed": guard_passed,
                             "compiler_exit": code})
    exe = output / "generic_context.exe"
    code, _ = compile_to_log("generic-context", [tests / "generic_context.cpp", f"/Fe{exe}"])
    run_code = subprocess.run([str(exe)], cwd=output).returncode if code == 0 else None
    report["checks"].append({"name": "generic-context", "passed": code == 0 and run_code == 0,
                             "compiler_exit": code, "execution_exit": run_code})
    code, _ = compile_to_log("abi-probe", ["/c", tests / "abi_probe.cpp"])
    report["checks"].append({"name": "abi-probe", "passed": code == 0, "compiler_exit": code})
    if version >= 70000000:
        code, _ = compile_to_log("runtime-exceptions", ["/c", runtime / "vm/Exception.cpp"])
        report["checks"].append({"name": "runtime-exceptions", "passed": code == 0, "compiler_exit": code})
    if args.diagnose:
        for source in sorted(native.rglob("*.cpp")):
            relative = source.relative_to(native).as_posix()
            if relative == "metadata/MethodBridgeSub.cpp":
                report["excluded"].append({"source": relative,
                    "reason": "Requires project-generated MethodBridge.inc; no production bridge is fabricated"})
                continue
            name = relative.replace("/", "-")
            code, text = compile_to_log(name, ["/Zs", source])
            errors = [line for line in text.splitlines() if re.search(r"(?:fatal )?error C\d+:", line)]
            report["translation_units"].append({"source": relative, "compiler_exit": code,
                                                "errors": errors})
            print(f"{relative}: {'PASS' if code == 0 else 'FAIL'} ({len(errors)} diagnostics)", flush=True)
    (output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    all_passed = all(check["passed"] for check in report["checks"])
    native_passed = all(unit["compiler_exit"] == 0 for unit in report["translation_units"]) if args.diagnose else None
    print(json.dumps({"checks": report["checks"], "native_passed": native_passed,
                      "native_units": len(report["translation_units"]),
                      "excluded": report["excluded"]}, indent=2))
    return 0 if all_passed and native_passed is not False else 1


if __name__ == "__main__":
    sys.exit(main())
