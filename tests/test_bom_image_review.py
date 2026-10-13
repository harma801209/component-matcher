import io
import unittest

import pandas as pd
from PIL import Image

from bom_image_review import editor_frame,build_corrections,apply_corrections,crop_source,normalized_box


class ImageReviewTests(unittest.TestCase):
    def setUp(self):
        self.source=pd.DataFrame([{'型号':'CLO5A475KP5NRNC','规格':'0402 4.7uF ±10% 10V',
                                   'OCR原文':'CLO5A475KP5NRNC original','OCR行号':1,'识别提示':'字符0不清楚'},
                                  {'型号':'RC0402FR-07174KL','规格':'0402 174KΩ ±1%',
                                   'OCR原文':'RC0402FR-07174KL original','OCR行号':3,'识别提示':''}])
        self.source.attrs['ocr_regions']={'0':{'row':[0,0,.5,.5]}}

    def test_save_applies_only_explicit_fields_and_preserves_raw_and_geometry(self):
        edited=editor_frame(self.source,self.source)
        edited.at[0,'型号']='CL05A475KP5NRNC'
        edited.at[0,'_已对照原图']=True
        payload=build_corrections(self.source,edited)
        actual=apply_corrections(self.source,payload,lambda row:[])
        self.assertEqual(actual.iloc[0]['型号'],'CL05A475KP5NRNC')
        self.assertEqual(actual.iloc[0]['OCR原文'],self.source.iloc[0]['OCR原文'])
        self.assertEqual(self.source.iloc[0]['型号'],'CLO5A475KP5NRNC')
        self.assertEqual(actual.attrs,self.source.attrs)
        self.assertIn('已对照原图人工确认',actual.iloc[0]['识别提示'])
        self.assertNotIn('字符0不清楚',actual.iloc[0]['识别提示'])
        self.assertEqual(actual.iloc[1]['型号'],self.source.iloc[1]['型号'])

    def test_confirmation_does_not_erase_conflicts_or_unconfirmed_edits(self):
        edited=editor_frame(self.source,self.source)
        edited.at[0,'_已对照原图']=True
        edited.at[1,'规格']='0402 174mΩ ±1%'
        actual=apply_corrections(self.source,build_corrections(self.source,edited),lambda row:['型号与规格不一致'])
        self.assertIn('型号与规格不一致',actual.iloc[0]['识别提示'])
        self.assertIn('尚未人工确认',actual.iloc[1]['识别提示'])

    def test_other_source_and_protected_helper_changes_are_rejected(self):
        edited=editor_frame(self.source,self.source)
        payload=build_corrections(self.source,edited)
        changed=self.source.copy()
        changed.at[0,'型号']='OTHER123'
        with self.assertRaises(ValueError):apply_corrections(changed,payload,lambda row:[])
        payload['changes']={'0':{'OCR原文':'overwrite'}}
        with self.assertRaises(ValueError):apply_corrections(self.source,payload,lambda row:[])
        edited.at[0,'_图片行号']=99
        with self.assertRaises(ValueError):build_corrections(self.source,edited)
        payload['changes']={'999':{'型号':'OTHER123'}}
        with self.assertRaises(ValueError):apply_corrections(self.source,payload,lambda row:[])

    def test_editor_roundtrip_retains_saved_values_and_confirmation(self):
        edited=editor_frame(self.source,self.source)
        edited.at[0,'型号']='CL05A475KP5NRNC'
        edited.at[0,'_已对照原图']=True
        payload=build_corrections(self.source,edited)
        actual=apply_corrections(self.source,payload,lambda row:[])
        roundtrip=build_corrections(self.source,editor_frame(self.source,actual,payload['confirmed']))
        self.assertEqual(roundtrip,payload)

    def test_crop_uses_normalized_original_coordinates_not_ocr_resized_pixels(self):
        original=Image.new('RGB',(200,100),'white')
        original.paste('red',(100,50,200,100))
        output=io.BytesIO()
        original.save(output,format='PNG')
        box=normalized_box(200,100,400,200,(400,200))
        crop=crop_source(output.getvalue(),box)
        self.assertEqual(crop.getpixel((crop.width//2,crop.height//2)),(255,0,0))
        self.assertEqual(original.getpixel((0,0)),(255,255,255))
        with self.assertRaises(ValueError):crop_source(output.getvalue(),[-1,0,1,1])


if __name__=='__main__':unittest.main()
