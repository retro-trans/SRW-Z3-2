"""Keep native CPK compression choices, including directly loaded textures.

Decoded member equality alone is insufficient: PCSG00494's synchronous file
path rejects compressed effect members 229 and 232, which shipped raw.
"""
from tools.cpk import CPK


def compression_ids(source, replacements):
    with CPK(source) as archive:
        rows={r['id']:r for r in archive.files}
        if set(replacements)-rows.keys():raise ValueError('Unknown native member')
        return {mid for mid in replacements if rows[mid]['size']<rows[mid]['extract']}


def verify(source,target):
    with CPK(source) as before,CPK(target) as after:
        a={r['id']:r for r in before.files};b={r['id']:r for r in after.files}
        if a.keys()!=b.keys():raise ValueError('Native archive member IDs changed')
        changed=[mid for mid in a if (a[mid]['size']<a[mid]['extract'])!=(b[mid]['size']<b[mid]['extract'])]
        if changed:raise ValueError('Native compression mode changed: '+str(changed))
        compressed=sum(r['size']<r['extract'] for r in a.values())
        return dict(members=len(a),compressed=compressed,uncompressed=len(a)-compressed,
                    original_compression_modes_preserved=True)
