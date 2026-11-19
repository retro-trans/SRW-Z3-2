"""Record reviewable Vita release evidence and checksums; never publish."""
import argparse,json,shutil
from tools.common import ROOT,sha256_file,write_json
from tools import vita_source as V,vita_build as B,vita_release as R,vita_integration as I

DEST=ROOT/'work/ui/vita/0.1.0/release.json'


def run(apply=False):
    build=json.loads((B.OUTPUT/'build.json').read_text('utf8'))
    validation=json.loads((I.OUTPUT/'integration.json').read_text('utf8'))
    audit=json.loads((R.OUTPUT/'PATCH_AUDIT.json').read_text('utf8'))
    V.need(validation['native_pkg_install_verified'] and validation['verified_files']==141 and
           audit['native_pkg_install_verified'] and B.describe(I.PATCH)==validation['patch_only_zip'],
           'Missing verified native delivery')
    data=dict(schema=1,title_id=V.TITLE,version=B.VERSION,parent_ps3='0.5.51',
        patch_zip=dict(name=I.PATCH.name,**validation['patch_only_zip']),
        private_vita3k_pkg={k:validation[k] for k in ('bytes','sha256')},
        native_installer_files=141,delta_roundtrips=18,archives_independently_verified=11,
        native_execution_cases=build['native_execution']['native_cases'],
        layout=dict(logical_canvas=[1280,720],framebuffer=[960,544],caption_center_x=640,
                    font_atlas=[4096,1120],font_cell=[32,32],allocated_cells=301,
                    edited_widgets=604,edited_elements=4,edited_table_rows=14),
        hardware_ready=False,missing_hardware_input='Original PCSG00494 v01.00 self_auth.bin console dump',
        gameplay_tested=False,vita_dlc_tested=False,trophy_translation_included=False,
        user_emulator_installation_changed=False,github_published=False,
        original_pkg_unchanged=validation['original_pkg_unchanged'],license_unchanged=validation['license_unchanged'])
    print(json.dumps(data,indent=2))
    if not apply:print('DRY RUN: no review metadata written.');return
    V.need(not DEST.exists(),'Preserve existing review seal');write_json(DEST,data)
    guide=R.OUTPUT/'README-VITA.txt';V.need(not guide.exists(),'Preserve release guide')
    shutil.copyfile(ROOT/'docs/VITA_INSTALL.md',guide)
    public=[I.PATCH,R.OUTPUT/'VITA-PKG.json',R.OUTPUT/'PATCH_AUDIT.json',guide]
    checksum=R.OUTPUT/'SHA256SUMS.txt';V.need(not checksum.exists(),'Preserve checksums')
    checksum.write_text(''.join(sha256_file(p)+'  '+p.name+'\n' for p in public),encoding='ascii')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();run(a.apply)


if __name__=='__main__':main()
