"""Synthetic multi-brand/font/compression OCR checks using isolated stores."""
import argparse
import io
import json
import logging
import math
import os
import platform
import runpy
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont,ImageFilter

platform._wmi=None
logging.disable(logging.CRITICAL)
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
parser=argparse.ArgumentParser()
parser.add_argument('--font',action='append',required=True)
parser.add_argument('--chinese-font',required=True)
parser.add_argument('--isolated',action='store_true')
parser.add_argument('--output',type=Path)
parser.add_argument('--variant',action='append',choices=['clear','jpeg75','smaller_blurred'])
args=parser.parse_args()
cases=[('贴片电容','Samsung','CL05A475KP5NRNC','0402 X5R 4.7uF ±10% 10V'),
       ('贴片电阻','YAGEO','RC0402FR-07174KL','0402 174KΩ ±1% 1/16W'),
       ('贴片电容','Murata','GRM155R71C104KA88D','0402 X7R 100nF ±10% 16V'),
       ('贴片电容','TDK','C1608X7R1H104K080AA','0603 X7R 100nF ±10% 50V'),
       ('贴片电容','WALSIN','0402N221J250CT','0402 NPO 220pF ±5% 25V'),
       ('贴片电阻','FOJAN','FRC0603J221TS','0603 220Ω ±5% 1/10W'),
       ('贴片电阻','UNIOHM','HP06W2J047KT5E','1206 470mΩ ±5% 1/2W'),
       ('贴片电阻','FH','RS-03L4R7JT','0603 4.7Ω ±5% 1/10W')]
report=[]
with tempfile.TemporaryDirectory(prefix='bom-image-matrix-') as folder:
    for env,name in [('MEMBER_AUTH_DB_PATH','member'),('COST_PRICE_DB_PATH','cost'),('NO_MATCH_REPORT_DB_PATH','report'),('BOM_JOB_DB_PATH','job')]:
        os.environ[env]=str(Path(folder)/(name+'.sqlite'))
    os.environ['COMPONENT_MATCHER_BUILD_MODE']='1'
    os.environ['COMPONENT_MATCHER_STARTUP_MAINTENANCE']='0'
    app=runpy.run_path(str(ROOT/'component_matcher.py'),run_name='ocr_matrix')
    app=app['clean_text'].__globals__
    if args.isolated:
        from bom_image_ocr_runtime import IsolatedRecognizer
        engine=IsolatedRecognizer()
        app['get_bom_image_text_recognizer']=lambda:engine
    chinese=ImageFont.truetype(args.chinese_font,26)
    for font_path in args.font:
        font=ImageFont.truetype(font_path,26)
        image=Image.new('RGB',(1800,520),'white')
        draw=ImageDraw.Draw(image)
        x=[0,170,370,930,1799]
        y=[0]+[57*idx for idx in range(1,10)]
        for pos in x:draw.line((pos,0,pos,513),fill='#c8c8c8')
        for pos in y:draw.line((0,pos,1799,pos),fill='#c8c8c8')
        for idx,row in enumerate([('物料名称','品牌','型号','规格'),*cases]):
            for col,text in enumerate(row):
                draw.text((x[col]+12,y[idx]+17),text,font=chinese if idx==0 or col==0 else font,fill='#172b4d')
        for variant in (args.variant or ['clear','jpeg75','smaller_blurred']):
            transformed=image if variant!='smaller_blurred' else image.resize((1440,416),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(.25))
            data=io.BytesIO()
            transformed.save(data,format='JPEG' if variant=='jpeg75' else 'PNG',**({'quality':75} if variant=='jpeg75' else {}))
            started=time.monotonic()
            frame=app['ocr_bom_image_to_dataframe'](data.getvalue())
            exact=flagged=unflagged=spec_exact=spec_unflagged=0
            differences=[]
            for idx,case in enumerate(cases):
                if idx>=len(frame):
                    flagged+=int(bool(frame.attrs.get('ocr_audit',{}).get('missing')))
                    unflagged+=int(not frame.attrs.get('ocr_audit',{}).get('missing'))
                    continue
                record=frame.iloc[idx].to_dict()
                content=' '.join(str(value) for column,value in record.items() if column not in ('OCR原文','OCR行号','识别提示'))
                if app['clean_model'](case[2]) in app['clean_model'](content):exact+=1
                elif any(word in str(record.get('识别提示','')) for word in ('不清楚','需核对','不一致','需确认','截断')):flagged+=1
                else:unflagged+=1
                parse=app['parse_resistor_spec_query'] if case[0]=='贴片电阻' else app['parse_spec_query']
                wanted=parse(case[3]+' '+case[0]) or {}
                actual=parse(content) or {}
                agrees=True
                mismatches={}
                for key in ('_resistance_ohm','容值_pf','尺寸（inch）','容值误差','耐压（V）','材质（介质）','_power'):
                    left,right=wanted.get(key),actual.get(key)
                    if left in (None,''):continue
                    if key in ('_resistance_ohm','容值_pf'):
                        agrees &= right is not None and math.isclose(float(left),float(right),rel_tol=1e-8,abs_tol=1e-10)
                    else:agrees &= str(left)==str(right)
                    if key in ('_resistance_ohm','容值_pf'):
                        equal=right is not None and math.isclose(float(left),float(right),rel_tol=1e-8,abs_tol=1e-10)
                    else:equal=str(left)==str(right)
                    if not equal:mismatches[key]={'wanted':left,'actual':right}
                if agrees:spec_exact+=1
                elif not any(word in str(record.get('识别提示','')) for word in ('不清楚','需核对','不一致','需确认','截断')):spec_unflagged+=1
                if mismatches:differences.append({'brand':case[1],'fields':mismatches,'recognized':content,'note':record.get('识别提示','')})
            result={'font':Path(font_path).name,'variant':variant,'rows':len(frame),'expected':len(cases),
                    'models_exact':exact,'other_models_flagged':flagged,'unflagged_model_errors':unflagged,
                    'specifications_exact':spec_exact,'unflagged_specification_errors':spec_unflagged,
                    'differences':differences,
                    'audit':frame.attrs.get('ocr_audit',{}),'seconds':round(time.monotonic()-started,2)}
            report.append(result)
            print(json.dumps(result,ensure_ascii=False),flush=True)
if args.output:
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(row['rows']==row['expected'] and row['unflagged_model_errors']==0 and row['unflagged_specification_errors']==0 for row in report), 'Some synthetic cases need further investigation'
