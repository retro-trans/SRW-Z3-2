"""Native-format safety checks independent of game screenshots."""
import struct
import unittest
from tools.vita import gxt
from tools import vita_ui as U
from tools.vita.repatch_auth import sanitize
from tools.vita_auth import optional_auth
import numpy as np


def widget_source(endian):
    raw=bytearray(0x180)
    raw[:4]=b'FSSA' if endian=='>' else b'ASSF'
    for at,value in ((32,0x80),(36,0xa0),(72,0xc0),(76,0xe0),(80,0xe0),(84,0xec)):
        struct.pack_into(endian+'I',raw,at,value)
    raw[0x80:0x86]=b'Label\0'
    struct.pack_into(endian+'Iff',raw,0xc0,0,0.25,-0.5)
    raw[0xd0:0xd5]=bytes((32,32,30,32,32))
    struct.pack_into(endian+'ff',raw,0xe0,0.2,-0.3)
    return raw


class VitaWidgets(unittest.TestCase):
    def test_native_offsets_and_pixel_center_delta(self):
        old=widget_source('>');native=widget_source('<');english=bytearray(old)
        struct.pack_into('<f',native,0xc4,0.251)
        struct.pack_into('>f',english,0xc4,0.4)
        english[0xd0]=24
        out,info=U.assf(old,english,native)
        self.assertAlmostEqual(struct.unpack_from('<f',out,0xc4)[0],0.401,places=6)
        self.assertEqual(out[0xd0],24);self.assertEqual(info['widgets'],1)
        self.assertEqual(out[0x80:0xa0],native[0x80:0xa0])

    def test_foreign_widget_rejected(self):
        old=widget_source('>');native=widget_source('<');english=bytearray(old)
        english[0xd0]=24;native[0xd0]=28
        with self.assertRaisesRegex(ValueError,'identity'):U.assf(old,english,native)

    def test_large_native_geometry_difference_rejected(self):
        old=widget_source('>');native=widget_source('<');english=bytearray(old)
        english[0xd0]=24;struct.pack_into('<f',native,0xc4,0.9)
        with self.assertRaisesRegex(ValueError,'geometry'):U.assf(old,english,native)


def p8_source():
    raw=bytearray(64+4+1024)
    raw[:8]=b'GXT\0\x03\0\0\x10'
    struct.pack_into('<5I',raw,8,1,64,1028,0,1)
    struct.pack_into('<6IHHI',raw,32,64,4,0,0,0x60000000,0x95000000,2,2,1)
    raw[64:68]=bytes((0,1,1,0));raw[68+4:68+8]=bytes((255,255,255,255))
    return raw


class VitaGraphics(unittest.TestCase):
    def test_only_masked_index_changes(self):
        source=p8_source();page=gxt.Page(source,0,0);out=bytearray(source)
        mask=np.array([[True,False],[False,False]])
        image=page.pixels();image[0,0]=(255,255,255,255)
        page.paint(out,image,mask)
        self.assertEqual(out[64],1);self.assertEqual(out[:64],source[:64]);self.assertEqual(out[65:],source[65:])
        self.assertEqual(gxt.pages(source),[(0,0)])

    def test_invisible_rgb_does_not_create_visible_fringe(self):
        source=p8_source();page=gxt.Page(source,0,0);out=bytearray(source)
        image=page.pixels();image[0,0]=(255,255,255,0)
        page.paint(out,image,np.array([[True,False],[False,False]]))
        self.assertEqual(out[64],0)

    def test_swizzle_is_bijection_on_rectangular_pages(self):
        for width,height in ((8,8),(16,8),(8,16)):
            self.assertEqual(sorted(gxt.order(width,height)),list(range(width*height)))

    def test_unsupported_format_fails_closed(self):
        source=p8_source();struct.pack_into('<I',source,52,0x98001000)
        with self.assertRaisesRegex(ValueError,'format'):gxt.Page(source,0,0)


class VitaAuth(unittest.TestCase):
    def test_secrets_and_padding_are_removed(self):
        source=bytearray(range(144));struct.pack_into('<Q',source,0,0x11223344)
        out=sanitize(source,0x11223344)
        self.assertEqual(out[:8],source[:8]);self.assertEqual(out[16:80],source[16:80])
        self.assertEqual(out[8:16],bytes(8));self.assertEqual(out[80:],bytes(64))

    def test_wrong_game_authority_rejected(self):
        with self.assertRaisesRegex(ValueError,'matching'):sanitize(bytes(range(144)),123)

    def metadata(self,order=(1,2,3)):
        raw=bytearray(32+48+32)
        for i,typ in enumerate(order):
            size={1:48,2:272,3:48}[typ]
            raw+=struct.pack('<IIQ',typ,size,int(i<len(order)-1))
            raw+=bytes([{1:0x11,2:0xe7,3:0x33}[typ]])*(size-16)
        return bytes(raw),(0xf00,5,1,2,0x170,0,0)

    def test_only_documented_optional_fields_are_exported(self):
        data,header=self.metadata();out,types=optional_auth(data,header,123,0x100,0x1000)
        self.assertEqual(types,[1,2,3]);self.assertEqual(out[16:48],bytes([0x11])*32)
        self.assertEqual(out[48:80],bytes([0x33])*32);self.assertEqual(out[80:],bytes(64))
        self.assertNotIn(bytes([0xe7])*16,out)

    def test_metadata_order_does_not_change_permissions(self):
        a,h=self.metadata();b,k=self.metadata((3,1,2))
        self.assertEqual(optional_auth(a,h,123,0x100,0x1000)[0],optional_auth(b,k,123,0x100,0x1000)[0])

    def test_bad_optional_chain_is_rejected(self):
        data,header=self.metadata();data=bytearray(data);struct.pack_into('<Q',data,112+8,0)
        with self.assertRaisesRegex(ValueError,'header'):optional_auth(data,header,123,0x100,0x1000)

    def test_optional_records_cannot_overlap_signature(self):
        data,header=self.metadata();header=(0x110,*header[1:])
        with self.assertRaisesRegex(ValueError,'bounds'):optional_auth(data,header,123,0x100,0x1000)


if __name__=='__main__':unittest.main()
