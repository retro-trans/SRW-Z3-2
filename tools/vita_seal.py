"""Record reviewable Vita release evidence and checksums; never publish."""
import argparse,json,shutil
from tools.common import ROOT,sha256_file,write_json
from tools import vita_source as V,vita_build as B,vita_release as R,vita_integration as I
from tools import vita_hardware_check as H

DEST=ROOT/'work/ui/vita'/B.VERSION/'release.json'


def hardware_seal(apply=False):
    """Complete the unpublished review seal with verified physical delivery."""
    prior=json.loads(DEST.read_text('utf8'))
    evidence=json.loads((H.PARENT/'integration.json').read_text('utf8'))
    auth_audit=json.loads((R.OUTPUT/'HARDWARE_AUDIT.json').read_text('utf8'))
    profile=json.loads((R.OUTPUT/'VITA-REPATCH.json').read_text('utf8'))
    components=len(profile['files'])
    V.need(evidence['retro_trans_pkg_work_bin_route_verified'] and evidence['zip_stream_hashes_verified'] and
           evidence['overlay_components']==components and evidence['original_inputs_unchanged'] and
           auth_audit['original_boot_parameters_preserved'],'Incomplete physical delivery proof')
    for path in (H.PATCH,H.ZIP):V.need(B.describe(path)==evidence['artifacts'][path.name],'Hardware artifact changed')
    V.need(B.describe(I.PATCH)=={k:prior['patch_zip'][k] for k in ('bytes','sha256')},'Existing Vita3K patch changed')
    result=dict(prior,schema=2,hardware_ready=True,hardware_ready_means='Prepared for testing; physical gameplay unverified',
        missing_hardware_input=None,hardware_validation_pending=False,console_auth_dump_required=False,physical_gameplay_tested=False,
        hardware_patch=dict(name=H.PATCH.name,**B.describe(H.PATCH)),
        hardware_copy_zip=dict(name=H.ZIP.name,**B.describe(H.ZIP)),
        hardware_components=components,hardware_auth_files=1,retro_trans_pkg_work_bin_route_verified=True,
        original_boot_parameters_preserved=True,auth_source='Original SELF decrypted with supplied work.bin',
        sanitized_auth_sha256=evidence['auth_source_proof']['sanitized_auth_sha256'])
    print(json.dumps(result,indent=2))
    if not apply:print('DRY RUN: no release metadata updated.');return
    write_json(DEST,result)
    audit=json.loads((R.OUTPUT/'PATCH_AUDIT.json').read_text('utf8'))
    audit.update(hardware_auth_available=True,hardware_pkg_work_bin_route_verified=True,
                 hardware_components=components,physical_gameplay_tested=False)
    for path in (H.PATCH,R.OUTPUT/'VITA-REPATCH.json',R.OUTPUT/'HARDWARE_AUDIT.json'):
        audit['artifacts'][path.name]=B.describe(path)
    write_json(R.OUTPUT/'PATCH_AUDIT.json',audit)
    guide=R.OUTPUT/'README-VITA.txt';shutil.copyfile(ROOT/'docs/VITA_INSTALL.md',guide)
    public=[I.PATCH,R.OUTPUT/'VITA-PKG.json',H.PATCH,R.OUTPUT/'VITA-REPATCH.json',
            R.OUTPUT/'PATCH_AUDIT.json',R.OUTPUT/'HARDWARE_AUDIT.json',guide]
    (R.OUTPUT/'SHA256SUMS.txt').write_text(''.join(sha256_file(p)+'  '+p.name+'\n' for p in public),encoding='ascii')


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
        native_installer_files=len(build['source_files']),delta_roundtrips=len(build['files']),archives_independently_verified=len(build['archives']),
        native_execution_cases=build['native_execution']['native_cases'],
        layout=dict(logical_canvas=[1280,720],framebuffer=[960,544],caption_center_x=640,
                    font_atlas=[4096,1120],font_cell=[32,32],allocated_cells=301,
                    edited_widgets=604,edited_elements=4,edited_table_rows=14),
        hardware_ready=False,missing_hardware_input=None,hardware_validation_pending=True,console_auth_dump_required=False,
        gameplay_tested=False,vita_dlc_tested=False,trophy_translation_included=False,
        user_emulator_installation_changed=False,github_published=False,
        original_pkg_unchanged=validation['original_pkg_unchanged'],license_unchanged=validation['license_unchanged'])
    runtime_path=DEST.parent/'runtime.json'
    if runtime_path.is_file():
        runtime=json.loads(runtime_path.read_text('utf8'))
        V.need(runtime['title_id']==V.TITLE and runtime['version']==B.VERSION and
               runtime['verified_game_files']==141 and runtime['build_files']==build['files'],
               'Runtime evidence does not match this build')
        for row in runtime['screenshots']:
            V.need(sha256_file(ROOT/row['path'])==row['sha256'],'Runtime screenshot changed')
        data.update(runtime_smoke_tested=runtime['post_intro_map_observed'],
                    runtime_evidence=dict(path=runtime_path.relative_to(ROOT).as_posix(),sha256=sha256_file(runtime_path)),
                    user_confirmed_working=runtime['user_confirmed_working'],
                    gameplay_test_scope=runtime['scope'],full_playthrough_tested=False)
    print(json.dumps(data,indent=2))
    if not apply:print('DRY RUN: no review metadata written.');return
    V.need(not DEST.exists(),'Preserve existing review seal');write_json(DEST,data)
    guide=R.OUTPUT/'README-VITA.txt';V.need(not guide.exists(),'Preserve release guide')
    shutil.copyfile(ROOT/'docs/VITA_INSTALL.md',guide)
    public=[I.PATCH,R.OUTPUT/'VITA-PKG.json',R.OUTPUT/'PATCH_AUDIT.json',guide]
    checksum=R.OUTPUT/'SHA256SUMS.txt';V.need(not checksum.exists(),'Preserve checksums')
    checksum.write_text(''.join(sha256_file(p)+'  '+p.name+'\n' for p in public),encoding='ascii')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');p.add_argument('--hardware',action='store_true');a=p.parse_args()
    if a.hardware:hardware_seal(a.apply)
    else:run(a.apply)


if __name__=='__main__':main()
