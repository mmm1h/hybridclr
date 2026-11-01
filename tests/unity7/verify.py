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
    parser.add_argument("--runtime-source", action="append", default=[],
                        help="Additional runtime .cpp path relative to libil2cpp")
    parser.add_argument("--runtime-manifest", type=Path,
                        help="JSON manifest of patched runtime files to compile")
    parser.add_argument("--compile-objects", action="store_true",
                        help="Emit objects for diagnosed sources instead of syntax-only checks")
    parser.add_argument("--legacy-bcl", action="store_true",
                        help="Probe the legacy Mono BCL profile instead of the modern Unity 7 BCL")
    args = parser.parse_args()
    runtime_manifest = {}
    if args.runtime_manifest:
        runtime_manifest = json.loads(args.runtime_manifest.read_text(encoding="utf-8"))
        args.runtime_source += [path for path in runtime_manifest["files"]
                                if path.endswith(".cpp")]
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
    mono_net_bcl = 1 if version >= 70000000 and not args.legacy_bcl else 0
    flags = ["/nologo", "/EHsc", "/std:c++17", "/Zc:__cplusplus", "/utf-8", "/bigobj",
             "/MT", "/DWIN32", "/D_WINDOWS", "/DUNICODE", "/D_UNICODE",
             "/DRUNTIME_IL2CPP=1", f"/DMONO_NET_BCL={mono_net_bcl}", "/DIL2CPP_DEBUG=0",
             "/DBASELIB_INLINE_NAMESPACE=il2cpp_baselib", f"/I{runtime}",
             f"/I{external / 'baselib/Include'}",
             f"/I{external / 'baselib/Platforms/Windows/Include'}",
             f"/I{external / 'google/sparsehash'}",
             f"/I{external / 'bdwgc/include'}",
             f"/I{args.unity_il2cpp.resolve() / 'libmono'}",
             f"/FI{native / 'Il2CppVersionCompatibleDefs.h'}"]
    experimental = ["/DHYBRIDCLR_UNITY7_EXPERIMENTAL=1"]
    tests = Path(__file__).resolve().parent
    report = {"scope": "Win64 C++ source probes; no IL2CPP Player or mobile execution",
              "unity_version_macro": version,
              "mono_net_bcl": mono_net_bcl,
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
        decoder = output / "metadata_decode.exe"
        code, _ = compile_to_log("metadata-decoder", [tests / "metadata_decode.cpp", runtime / "vm/MetadataDeserialization.cpp", f"/Fe{decoder}"])
        decoder_exit = subprocess.run([str(decoder)], cwd=output).returncode if code == 0 else None
        report["checks"].append({"name": "metadata-decoder", "passed": code == 0 and decoder_exit == 0,
                                 "compiler_exit": code, "execution_exit": decoder_exit})
    if args.diagnose or args.runtime_source:
        sources = sorted(native.rglob("*.cpp")) if args.diagnose else []
        sources += [runtime / path for path in args.runtime_source]
        for source in sources:
            relative = source.relative_to(native).as_posix() if source.is_relative_to(native) else source.relative_to(runtime).as_posix()
            if mono_net_bcl and relative in runtime_manifest.get("legacy_only", []):
                report["excluded"].append({"source": relative,
                    "reason": "Legacy Mono BCL source; Unity's System.Private.CoreLib profile uses icalls_monoaot instead"})
                continue
            if not mono_net_bcl and relative.startswith("icalls_monoaot/"):
                report["excluded"].append({"source": relative, "reason": "Modern BCL source is not compiled in the legacy profile"})
                continue
            if relative == "metadata/MethodBridgeSub.cpp" and not (native / "generated/MethodBridge.inc").is_file():
                report["excluded"].append({"source": relative,
                    "reason": "Requires project-generated MethodBridge.inc; no production bridge is fabricated"})
                continue
            name = relative.replace("/", "-")
            compile_mode = ["/c", "/Od", f"/Fo{output / (name + '.obj')}"] if args.compile_objects else ["/Zs"]
            code, text = compile_to_log(name, [*compile_mode, source])
            errors = [line for line in text.splitlines() if re.search(r"(?:fatal )?error C\d+:", line)]
            report["translation_units"].append({"source": relative, "compiler_exit": code,
                                                "errors": errors})
            print(f"{relative}: {'PASS' if code == 0 else 'FAIL'} ({len(errors)} diagnostics)", flush=True)
    (output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    all_passed = all(check["passed"] for check in report["checks"])
    native_passed = all(unit["compiler_exit"] == 0 for unit in report["translation_units"]) if args.diagnose or args.runtime_source else None
    print(json.dumps({"checks": report["checks"], "native_passed": native_passed,
                      "native_units": len(report["translation_units"]),
                      "excluded": report["excluded"]}, indent=2))
    return 0 if all_passed and native_passed is not False else 1


if __name__ == "__main__":
    sys.exit(main())
