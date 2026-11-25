"""Safety properties of the hardware constant binding transformation."""
import unittest
from tools.vita_lua_constants import bind


class VitaConstantBinding(unittest.TestCase):
    def test_code_references_only_with_long_and_binary_strings(self):
        raw=(b'-- LOCAL_FLAG must stay in this comment\n'
             b'--[=[ LOCAL_FLAG ]=]\n'
             b'local s=[==[LOCAL_FLAG\x31\0]==]\n'
             b'local t="LOCAL_FLAG\\\""\n'
             b'if flags.LOCAL_FLAG == LOCAL_FLAG then f(BATTLE_FLAG+3) end\n')
        out,report=bind(raw,{b'LOCAL_FLAG':b'0',b'BATTLE_FLAG':b'128'})
        self.assertEqual(out,raw.replace(b'== LOCAL_FLAG then',b'== (0) then').replace(b'f(BATTLE_FLAG+3)',b'f((128)+3)'))
        self.assertEqual(report['references'],2)

    def test_rejects_shadowing_and_writes(self):
        for raw in (b'LOCAL_FLAG=9',b'local LOCAL_FLAG',b'function f(a,LOCAL_FLAG) end',b'for LOCAL_FLAG=1,5 do end'):
            with self.subTest(raw=raw),self.assertRaisesRegex(ValueError,'declared/shadowed'):
                bind(raw,{b'LOCAL_FLAG':b'0'})

    def test_preserves_negative_and_string_constant_types(self):
        out,_=bind(b'f(ScNIL, ScBig)',{b'ScNIL':b'-1',b'ScBig':b'"3000000000"'})
        self.assertEqual(out,b'f((-1), ("3000000000"))')


if __name__=='__main__':unittest.main()
