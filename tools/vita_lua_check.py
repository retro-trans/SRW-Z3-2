"""Lua 5.1 regression: native constant values and event-check equivalence.

Host interpreter checks source semantics; C game calls are deterministic test
doubles. This is not a console gameplay test or an explanation of why the
tester loses its shared globals.
"""
import json
from pathlib import Path
import subprocess
from tools import vita_lua_constants as L
from tools.common import ROOT,write_json,sha256_file,sha256
from tools.cpk import CPK

LUA=ROOT/'work/output/tool-deps/lua-5.1.5/lua51.exe'
SOURCE=ROOT/'work/output/tool-deps/lua-5.1.5.tar.gz'
SOURCE_SHA='2640fc56a795f29d28ef15e13c34a47e223960b0240e8cb0a82d9b0738695333'


def verify(stage_members,assets,report,folder):
    folder=Path(folder);L.V.need(not folder.exists(),'Preserve an existing Lua semantic check')
    L.V.need(LUA.exists() and sha256_file(SOURCE)==SOURCE_SHA,'Missing pinned Lua 5.1.5 source/interpreter')
    folder.mkdir(parents=True)
    with CPK(L.V.PLAIN/L.SHARED) as a:
        shared={r['id']:a.read(r) for r in a.files}
    with CPK(L.V.PLAIN/L.STAGE) as a:
        stage={r['id']:stage_members.get(r['id'],a.read(r)) for r in a.files}
    constants=L.declarations(shared[1]);(folder/'native-definitions.lua').write_bytes(shared[1])
    rows=[]
    for rel,base in ((L.STAGE,stage),(L.SHARED,shared)):
        for mid,new in assets[rel].items():
            old=base[mid]
            if old==new:continue
            stem=('stage' if rel==L.STAGE else 'shared')+f'-{mid:05d}'
            (folder/(stem+'-before.lua')).write_bytes(old)
            (folder/(stem+'-after.lua')).write_bytes(new)
            rows.append((stem,b'function\tEventCheck_' in old or b'function EventCheck_' in old))
    def q(s):return json.dumps(str(s),ensure_ascii=True)
    script=r'''
local root=arg[1]
local base={}; for k,v in pairs(_G) do base[k]=v end
local definitions=setmetatable({}, {__index=base})
local definitions_chunk=assert(loadfile(root..'/native-definitions.lua'))
setfenv(definitions_chunk,definitions); definitions_chunk()
local constants=0
'''
    for name,value in sorted(constants.items()):
        n=q(name.decode());expr=value.decode()
        script+=f'do local expected=({expr}); local actual=definitions[{n}]; assert(type(actual)==type(expected) and actual==expected,"Native constant differs: "..{n}); constants=constants+1 end\n'
    script+=r'''
local function serialize(x,seen)
  if type(x)~='table' then return type(x)..':'..tostring(x) end
  seen=seen or {}; if seen[x] then return '<cycle>' end; seen[x]=true
  local entries={}
  for k,v in pairs(x) do entries[#entries+1]=serialize(k)..'='..serialize(v,seen) end
  table.sort(entries); seen[x]=nil; return '{'..table.concat(entries,',')..'}'
end
local function environment(source,with_constants,mode)
  local calls={}; local env={}; env._G=env; env.print=function() end
  if with_constants then for k,v in pairs(definitions) do env[k]=v end end
  setmetatable(env,{__index=function(t,k)
    if base[k]~=nil then return base[k] end
    if type(k)=='string' and k:match('^SC_') then
      local f=function(...)
        calls[#calls+1]=k..serialize({...})
        return mode,mode,mode
      end
      rawset(t,k,f); return f
    end
  end})
  local chunk=assert(loadstring(source,'stage')); setfenv(chunk,env); chunk()
  return env,calls
end
local function read(path) local f=assert(io.open(path,'rb')); local s=f:read('*a');f:close();return s end
local original=read(root..'/stage-00002-before.lua')
local corrected=read(root..'/stage-00002-after.lua')
local function setup(source,with_constants)
  local env,calls=environment(source,with_constants,0)
  env.SC_GAME_OVER_CHK=function() return 0 end
  env.SC_STABLE_GET_TAG_NUM=function(a,b) assert(a==5 and b==-1); return 0 end
  env.SC_EVENT_IS_OK_START=function(n) assert(n==1);return 1 end
  env.SC_EVENT_START=function(n) assert(n==1);return 'event_001' end
  env.SC_LFLAG_SET=function(n,v) assert(n==0 and v==1);env.flag_written=true end
  return env,calls
end
local broken=setup(original,true); broken.LOCAL_FLAG=nil
local ok,err=pcall(broken.EventCheck_ActionEnd)
assert(not ok and err:find(':174:') and err:find("global 'LOCAL_FLAG'"), 'Did not reproduce physical error')
local reference=setup(original,true)
assert(reference.EventCheck_ActionEnd()=='event_001' and reference.flag_written)
local fixed=setup(corrected,false)
assert(rawget(fixed,'LOCAL_FLAG')==nil and fixed.EventCheck_ActionEnd()=='event_001' and fixed.flag_written,
       'Missing-global action-end flow did not match the intact original')
local compiled,equivalent,unmodeled=0,0,0
local function check(stem,events)
  local a=read(root..'/'..stem..'-before.lua');local b=read(root..'/'..stem..'-after.lua')
  assert(loadstring(a,stem..'-before'));assert(loadstring(b,stem..'-after'));compiled=compiled+1
  if not events then return end
  for mode=0,2 do
    local left,lcalls=environment(a,true,mode);local right,rcalls=environment(b,false,mode)
    for name,fn in pairs(left) do
      if type(fn)=='function' and name:match('^EventCheck_') then
        for i=#lcalls,1,-1 do lcalls[i]=nil end;for i=#rcalls,1,-1 do rcalls[i]=nil end
        debug.sethook(function() error('test instruction budget exceeded') end,'',10000)
        local lok,lv=pcall(fn);local rok,rv=pcall(right[name]);debug.sethook()
        if lok then
          assert(rok,stem..'/'..name..' introduced an error: '..tostring(rv))
          assert(serialize(lv)==serialize(rv) and serialize(lcalls)==serialize(rcalls),stem..'/'..name..' changed event behavior')
          equivalent=equivalent+1
        else unmodeled=unmodeled+1 end
      end
    end
  end
end
'''
    for stem,events in rows:script+=f'check({q(stem)},{str(events).lower()})\n'
    script+='print(string.format("constants=%d compiled=%d equivalent=%d unmodeled=%d",constants,compiled,equivalent,unmodeled))\n'
    path=folder/'check.lua';path.write_text(script,encoding='ascii')
    output=subprocess.run([str(LUA),str(path),str(folder)],capture_output=True,check=False)
    L.V.need(output.returncode==0,'Lua semantic regression failed: '+output.stderr.decode('utf8','replace'))
    text=output.stdout.decode('ascii').strip();print(text,flush=True)
    result=dict(schema=1,lua_version='5.1.5',source_sha256=SOURCE_SHA,
        binding_plan_sha256=sha256(json.dumps(report,sort_keys=True,separators=(',',':')).encode()),
        native_constants_verified=6481,physical_error_reproduced=True,
        first_stage_missing_globals_corrected=True,engine_calls_are_test_doubles=True,
        console_gameplay_tested=False,summary=text,changed_script_pairs=len(rows))
    write_json(folder/'proof.json',result)
    return result
