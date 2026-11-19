"""PCSG00494 source intake; local files only, dry-run unless --apply.

Public dependency sources and pre-existing tools are borrowed read-only from
the sibling project's audited Vita workset. No license values are logged.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess
from tools.common import ROOT, sha256_file, write_json
from tools.pipeline import sfo_values

TITLE = 'PCSG00494'
WORK = ROOT/'work/vita'
PKG = ROOT/'SRW Z3 Tengoku.pkg'
LICENSE = ROOT/'work.bin'
SIBLING = Path('E:/Projects/SRW Z3')
DEPS = SIBLING/'work/vita'
EXTRACTED = WORK/'app'/TITLE
PLAIN = WORK/('decrypted_'+TITLE)
READER = WORK/'offline_pfs.exe'
PKG2ZIP = DEPS/'pkg2zip.exe'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def inspect():
    with PKG.open('rb') as stream:
        header = stream.read(128)
    with LICENSE.open('rb') as stream:
        rif = stream.read(513)
    need(header[:4] == b'\x7fPKG' and len(rif) == 512, 'Invalid package/license size')
    pkg_id = header[0x30:0x60].split(b'\0')[0]
    need(pkg_id == rif[0x10:0x40].split(b'\0')[0] and pkg_id[7:16] == TITLE.encode(),
         'Package/license identity mismatch (values suppressed)')
    need(struct.unpack_from('>Q', header, 0x18)[0] == PKG.stat().st_size, 'Package size mismatch')
    need(struct.unpack_from('>HHH', rif) == (1,1,1) and any(rif[0x50:0x60]),
         'Unsupported or empty supplied license')
    return dict(schema=1, title_id=TITLE, pkg_bytes=PKG.stat().st_size,
                pkg_sha256=sha256_file(PKG), matching_license_identity=True,
                license_values_logged=False, original_files_changed=False)


def reader_command():
    source = DEPS/'offline_parser_source'
    openssl = DEPS/'openssl_source/include'
    exclude = {'PsvPfsParserConfig.cpp','rif2zrif.cpp','zrif2rif.cpp','F00DKeyEncryptorFactory.cpp',
               'F00DFileKeyEncryptor.cpp','CryptoOperationsFactory.cpp'}
    command = ['C:/mingw64/bin/g++.exe', '-std=c++17', '-O2', '-static-libgcc', '-static-libstdc++',
               '-include','algorithm','-include','cstring','-I',str(source),'-I',str(openssl)]
    command += [str(p) for p in sorted(source.glob('*.cpp')) if p.name not in exclude]
    command += [str(ROOT/'tools/vita/offline_pfs_main.cpp'),
                'C:/Program Files/Git/mingw64/bin/libcrypto-3-x64.dll','-o',str(READER)]
    need(len(command) > 20 and Path(command[0]).is_file(), 'Missing local compiler/dependencies')
    return command


def audit():
    original = {p.relative_to(EXTRACTED).as_posix():p for p in EXTRACTED.rglob('*') if p.is_file()
                and not p.relative_to(EXTRACTED).as_posix().startswith(('sce_pfs/','sce_sys/package/'))}
    plain = {p.relative_to(PLAIN).as_posix():p for p in PLAIN.rglob('*') if p.is_file()}
    need(set(original) == set(plain), 'Decrypted inventory differs from package')
    metadata = sfo_values((PLAIN/'sce_sys/param.sfo').read_bytes())
    need(metadata['TITLE_ID'] == TITLE, 'Wrong Vita game')
    from tools.cpk import CPK
    files, cpks = {}, {}
    for name, path in sorted(plain.items()):
        need(path.stat().st_size == original[name].stat().st_size, 'Decryption changed file size')
        files[name] = dict(bytes=path.stat().st_size, sha256=sha256_file(path))
        if path.suffix.lower() == '.cpk':
            with CPK(path) as archive:
                need(bool(archive.files), 'Empty Vita archive')
                cpks[name] = len(archive.files)
                for row in archive.files:
                    need(row['offset'] >= 0 and row['offset']+row['size'] <= path.stat().st_size,
                         'Archive member out of bounds')
    return dict(schema=1,title_id=TITLE, app_version=metadata.get('APP_VER'),
                files=files,cpk_archives=cpks, original_inventory_matches=True,
                license_values_logged=False, runtime_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect','reader','decrypt','audit'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.action == 'inspect':
        result = inspect()
        print(json.dumps(result, indent=2))
        if args.apply:
            write_json(WORK/'source_identity.json', result)
    elif args.action == 'reader':
        command = reader_command()
        print('Compile local offline PFS reader for', TITLE, '; output:', READER)
        if args.apply:
            need(not READER.exists(), 'Preserve existing reader')
            WORK.mkdir(parents=True,exist_ok=True)
            subprocess.run(command, check=True)
            print('Reader SHA-256:', sha256_file(READER))
    elif args.action == 'decrypt':
        inspect()
        need(READER.is_file() and not PLAIN.exists(), 'Missing reader or output already exists')
        command = [str(READER), str(EXTRACTED), str(PLAIN), str(LICENSE)]
        if args.apply:
            command.append('--write')
        subprocess.run(command, check=True)
    else:
        result = audit()
        print('Verified',len(result['files']),'Vita files;',len(result['cpk_archives']),'CPK archives;',result['app_version'])
        if args.apply:
            write_json(WORK/'source_audit.json',result)
    if not args.apply:
        print('DRY RUN: no source data or reports changed.')


if __name__ == '__main__':
    main()
