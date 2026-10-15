"""Read-only PINE audit of the popup's loaded keyword archive.

No write, pause, reset or controller commands are implemented. Addresses are
observed from the current process and supplied explicitly; no guest scans.
"""
import argparse,json,socket,struct
from tools.common import ROOT,sha256,write_json
from tools import keyword_popup as K

class Reader:
    def __enter__(self):
        self.socket=socket.create_connection(('127.0.0.1',28012),timeout=5);return self
    def __exit__(self,*args):self.socket.close()
    def receive(self,n):
        out=b''
        while len(out)<n:
            block=self.socket.recv(n-len(out))
            if not block:raise ValueError('Diagnostic connection closed')
            out+=block
        return out
    def request(self,command):
        memory_read=bool(command)and len(command)%5==0 and all(x==0 for x in command[::5])
        if not memory_read and command not in(b'\x0c',b'\x0d'):
            raise ValueError('Read-only command required')
        self.socket.sendall(struct.pack('<I',len(command)+4)+command)
        size=struct.unpack('<I',self.receive(4))[0]
        if not 5<=size<=450000:raise ValueError('Diagnostic reply size differs')
        reply=self.receive(size-4)
        if reply[0]:raise ValueError('Diagnostic read failed')
        return reply[1:]
    def read(self,address,n):
        out=b''
        for start in range(0,n,50000):
            count=min(50000,n-start)
            command=b''.join(b'\0'+struct.pack('<I',address+start+i)for i in range(count))
            part=self.request(command)
            if len(part)!=count:raise ValueError('Diagnostic byte count differs')
            out+=part
        return out
    def info(self,opcode):return self.request(bytes([opcode]))[4:].rstrip(b'\0').decode('utf8')

def audit(table,pool):
    original=K.source();parsed=K.parse(original)
    with Reader() as client:
        title=client.info(0xc);uuid=client.info(0xd)
        if title!='BLJS10299':raise ValueError('Wrong game in diagnostic connection')
        native=client.read(table,K.COUNT*24)
        loaded=client.read(pool,len(parsed['pool']))
    if loaded!=parsed['pool']:raise ValueError('Live popup is not using this source string pool')
    for i,row in enumerate(parsed['rows']):
        want=tuple(pool+row['fields'][tag]['offset']for tag in K.TAGS)+(row['flags'],row['id'])
        if struct.unpack_from('>6I',native,i*24)!=want:
            raise ValueError('Live popup record differs: '+str(row['id']))
    return dict(schema=1,version='0.5.40',game_id=title,executable_uuid=uuid,
        diagnostic_mode='read_only',source_archive=K.DISC,source_archive_sha256=K.SOURCE_SHA,
        source_member_sha256=sha256(original),native_table_va=table,native_pool_va=pool,
        loaded_pool_sha256=sha256(loaded),keyword_records_matched=K.COUNT,
        loaded_fields_matched=K.COUNT*4,description_variants_still_original=K.COUNT*2,
        confirms_separate_popup_archive=True,does_not_verify_corrected_build=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--table',type=lambda x:int(x,0),required=True)
    p.add_argument('--pool',type=lambda x:int(x,0),required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    result=audit(a.table,a.pool);print(json.dumps(result,indent=2))
    if a.apply:write_json(ROOT/'work/ui/keyword_popup_live_0.5.40.json',result)
    else:print('DRY RUN: no evidence written; guest memory is read-only in both modes.')

if __name__=='__main__':main()
