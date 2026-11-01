#!/usr/bin/env python3
"""Build a real Win64 Unity 7 IL2CPP host, then run two external hot DLLs.

Run in an x64 Visual Studio developer shell, using an isolated, patched IL2CPP
SDK. Output must be new. Nothing is installed into Unity or a game project.
"""
# Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unity-il2cpp', type=Path, required=True)
    parser.add_argument('--prepared-sdk', type=Path, required=True)
    parser.add_argument('--windows-support', type=Path, required=True)
    parser.add_argument('--bridge-generator', type=Path, required=True,
                        help='GenerateBridge.dll compiled from the UPM Tests~/Unity7 host')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    stock, sdk, support = (value.resolve() for value in
                           (args.unity_il2cpp, args.prepared_sdk, args.windows_support))
    output = args.output.resolve()
    if output.exists():
        parser.error('output must not exist')
    if output.is_relative_to(stock) or output.is_relative_to(sdk):
        parser.error('output must be outside both SDKs')
    dotnet = stock.parent / 'DotNetSdk/dotnet.exe'
    csc = next((stock.parent / 'DotNetSdk/sdk').glob('10.*/Roslyn/bincore/csc.dll'), None)
    bcl = support / 'il2cpp/unityaot/x64/lib'
    version = sdk / 'libil2cpp/hybridclr/generated/UnityVersion.inc'
    if not csc or not bcl.is_dir() or not version.is_file() or not shutil.which('cl.exe'):
        parser.error('requires Unity 7 .NET 10 SDK, Windows IL2CPP module, patched SDK and cl.exe')
    if '70000000' not in version.read_text(encoding='utf-8-sig'):
        parser.error('prepared SDK is not Unity 7000.0.0')
    tests = Path(__file__).resolve().parent
    output.mkdir(parents=True)
    for name in ('managed', 'managed-v2', 'trimmed', 'generated', 'data', 'native'):
        (output / name).mkdir()
    report = {'scope': 'Unity 7000.0.0a12, Win64, .NET BCL, Debug standalone IL2CPP',
              'hot_assembly_in_aot': False, 'runs': []}

    def run(name, command):
        (output / (name + '.command.json')).write_text(json.dumps(list(map(str, command)), indent=2), encoding='utf-8')
        with (output / (name + '.log')).open('wb') as log:
            result = subprocess.run(list(map(str, command)), stdout=log, stderr=subprocess.STDOUT, cwd=output)
        print(f'{name}: exit {result.returncode}', flush=True)
        if result.returncode:
            raise RuntimeError(f'{name} failed; see {output / (name + ".log")}')

    references = ['-r:' + str(path) for path in sorted(bcl.glob('*.dll'))]
    for source, destination, extra in (
        ('AotHost.cs', 'managed/AotHost.exe', []),
        ('HotPayload.cs', 'managed/HotPayload.dll', []),
        ('HotPayload.cs', 'managed-v2/HotPayload.dll', ['-define:PAYLOAD_V2']),
    ):
        target = output / destination
        options = ['-noconfig', '-nostdlib+', '-nologo', '-langversion:latest',
                   '-target:' + ('exe' if target.suffix == '.exe' else 'library'),
                   '-out:' + str(target), *references, *extra, str(tests / source)]
        rsp = output / (target.parent.name + '-' + target.stem + '.rsp')
        rsp.write_text('\n'.join('"' + option + '"' for option in options), encoding='utf-8')
        run(target.parent.name + '-' + target.stem, [dotnet, csc, '@' + str(rsp)])

    generated = version.parent
    run('bridge', [dotnet, args.bridge_generator.resolve(), generated / 'MethodBridge.inc',
                   output / 'managed/HotPayload.dll', bcl])
    shutil.copy2(tests / 'link.xml', output / 'link.xml')
    run('link', [stock / 'build/deploy/UnityLinker.exe',
                 '--search-directory=' + str(bcl), '--include-assembly=' + str(output / 'managed/AotHost.exe'),
                 '--include-link-xml=' + str(output / 'link.xml'),
                 '--include-link-xml=' + str(generated / 'MethodBridge.link.xml'),
                 '--out=' + str(output / 'trimmed'), '--dotnetprofile=unityaot2-win-x64',
                 '--dotnetruntime=il2cpp', '--architecture=x64', '--platform=WindowsDesktop',
                 '--core-action=link', '--user-action=link'])
    if (output / 'trimmed/HotPayload.dll').exists():
        raise RuntimeError('hot DLL was incorrectly included in AOT input')
    run('convert', [stock / 'build/deploy/il2cpp.exe', '--convert-to-cpp',
                    '--directory=' + str(output / 'trimmed'), '--generatedcppdir=' + str(output / 'generated'),
                    '--data-folder=' + str(output / 'data'), '--dotnetprofile=unityaot2-win-x64',
                    '--platform=WindowsDesktop', '--architecture=x64', '--emit-null-checks',
                    '--enable-array-bounds-check', '--enable-stacktrace', '--jobs=4'])
    for path in (output / 'generated').glob('*.cpp'):
        if 'Unity7HotUpdateFixture' in path.read_text(encoding='utf-8-sig'):
            raise RuntimeError(f'hot code was statically compiled into {path.name}')

    # Explicit opt-in belongs only to this disposable build fixture.
    version.write_text('#define HYBRIDCLR_UNITY_VERSION 70000000\n#define HYBRIDCLR_UNITY7_EXPERIMENTAL 1\n', encoding='utf-8')
    lackey = sdk / 'Libil2cppLackey/DllMain.cpp'
    lackey.parent.mkdir(exist_ok=True)
    shutil.copy2(tests / 'Libil2cppLackey/DllMain.cpp', lackey)
    baselib = support / 'Variations/win64_player_development_il2cpp'
    baselib_build = sdk / 'build/baselib/debug_win64'
    baselib_build.mkdir(parents=True, exist_ok=True)
    for file in ('baselib.dll', 'baselib.dll.lib'):
        shutil.copy2(baselib / file, baselib_build / file)
    run('compile', [sdk / 'build/deploy/il2cpp.exe', '--compile-cpp',
                    '--generatedcppdir=' + str(output / 'generated'), '--outputpath=' + str(output / 'native/AotHost.exe'),
                    '--cachedirectory=' + str(output / 'cache'), '--dotnetprofile=unityaot2-win-x64',
                    '--platform=WindowsDesktop', '--architecture=x64', '--configuration=Debug',
                    '--libil2cpp-static', '--dont-deploy-baselib', '--additional-libraries=' + str(baselib / 'baselib.dll.lib'),
                    '--additional-defines=HYBRIDCLR_UNITY7_EXPERIMENTAL=1,BASELIB_INLINE_NAMESPACE=il2cpp_baselib,BASELIB_USE_DYNAMICLIBRARY=1,MONO_NET_BCL=1',
                    '--jobs=4', '--verbose'])
    shutil.copytree(output / 'data', output / 'native/Data')
    shutil.copy2(baselib / 'baselib.dll', output / 'native/baselib.dll')
    lackey_dll = sdk / 'build/Libil2cppLackey/debug_win64/Libil2cppLackey.dll'
    if not lackey_dll.is_file():
        matches = list(sdk.glob('build/**/Libil2cppLackey.dll')) + list((output / 'cache').rglob('Libil2cppLackey.dll'))
        if not matches:
            raise RuntimeError('build did not produce Libil2cppLackey.dll')
        lackey_dll = matches[0]
    shutil.copy2(lackey_dll, output / 'native/Libil2cppLackey.dll')
    host = output / 'native/AotHost.exe'
    report['host_sha256'] = sha256(host)
    for number, directory in ((1, 'managed'), (2, 'managed-v2')):
        payload = output / directory / 'HotPayload.dll'
        run('run-v' + str(number), [host, payload, str(number)])
        log = (output / ('run-v' + str(number) + '.log')).read_text(encoding='utf-8-sig')
        if 'HYBRIDCLR_UNITY7_HOT_UPDATE_OK' not in log:
            raise RuntimeError('test process exited without the success marker')
        report['runs'].append({'payload_version': number, 'sha256': sha256(payload),
                                'passed': [line[5:] for line in log.splitlines() if line.startswith('PASS ')]})
    report['host_unchanged'] = sha256(host) == report['host_sha256']
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return 0 if report['host_unchanged'] else 1


if __name__ == '__main__':
    sys.exit(main())
