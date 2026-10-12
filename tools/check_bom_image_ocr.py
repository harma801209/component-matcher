"""Run actual BOM image import against a supplied local image, with isolated stores."""
import argparse
import json
import logging
import os
import platform
import runpy
import sys
import tempfile
import time
from pathlib import Path

platform._wmi = None
logging.disable(logging.CRITICAL)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
parser = argparse.ArgumentParser()
parser.add_argument('image', type=Path)
parser.add_argument('--tesseract')
parser.add_argument('--expected-rows', type=int)
parser.add_argument('--output', type=Path)
parser.add_argument('--verify-example', action='store_true')
args = parser.parse_args()
if args.tesseract:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = args.tesseract
with tempfile.TemporaryDirectory(prefix='bom-image-check-') as folder:
    for env, name in [('MEMBER_AUTH_DB_PATH','member'), ('COST_PRICE_DB_PATH','cost'),
                      ('NO_MATCH_REPORT_DB_PATH','report'), ('BOM_JOB_DB_PATH','job')]:
        os.environ[env] = str(Path(folder) / (name + '.sqlite'))
    os.environ['COMPONENT_MATCHER_BUILD_MODE'] = '1'
    os.environ['COMPONENT_MATCHER_STARTUP_MAINTENANCE'] = '0'
    app = runpy.run_path(str(ROOT / 'component_matcher.py'), run_name='ocr_diagnostic')
    raw = args.image.read_bytes()
    image = app['preprocess_bom_image_for_ocr'](raw)
    print('grid', app['detect_bom_image_grid_lines'](image), flush=True)
    started = time.monotonic()
    df = app['ocr_bom_image_to_dataframe'](raw)
    result = {'seconds': round(time.monotonic()-started, 2), 'rows': len(df),
              'columns': list(df.columns), 'mapping': app['guess_bom_column_mapping'](df),
              'engine': df.attrs.get('ocr_engine'), 'records': df.to_dict('records')}
    if args.verify_example:
        expected_models = {0:'HP06W2J047KT5E',1:'HP05W3J068JT5E',2:'0402WGF4024TCE',
                           4:'CL31A106MOHNNNE',5:'CL05A475KP5NRNC',6:'AC0603FR-07180RL',
                           7:'AC0603FR-07100RL',12:'RS-03L4R7JT',13:'RC0402FR-07174KL',
                           14:'0402N221J250CT',15:'CL10A106KP8NNNC'}
        expected_resistance = {0:.47,1:6.8,2:4020000,3:200,6:180,7:100,8:3090,
                               9:2400,10:10000,11:.1,12:4.7,13:174000}
        expected_caps = {4:(10000000,'1206','X5R','20','16'),5:(4700000,'0402','X5R','10','10'),
                         14:(220,'0402','COG(NPO)','5','25'),15:(10000000,'0603','X5R','10','10')}
        parsed = []
        for idx, row in df.iterrows():
            query = row['规格型号'] + ' ' + row['物料名称']
            tokens = app['extract_model_like_tokens'](query)
            if idx in expected_models:
                assert expected_models[idx] in tokens, (idx, tokens, expected_models[idx])
            spec = app['parse_resistor_spec_query'](query) if idx in expected_resistance else app['parse_spec_query'](query)
            parsed.append({'index':int(idx),'tokens':tokens,'spec':spec})
            if idx in expected_resistance:
                assert spec is not None and abs(float(spec['_resistance_ohm'])-expected_resistance[idx]) < max(1e-9,expected_resistance[idx]*1e-9), (idx,spec)
            if idx in expected_caps:
                actual = tuple(spec.get(key) for key in ('容值_pf','尺寸（inch）','材质（介质）','容值误差','耐压（V）'))
                assert actual == expected_caps[idx], (idx, actual)
            assert app['format_bom_quantity'](row['申请数量']).isdigit(), (idx,row['申请数量'])
        result['parsed'] = parsed
    print(json.dumps(result, ensure_ascii=False, default=str), flush=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    if args.expected_rows is not None:
        assert len(df) == args.expected_rows, (len(df), args.expected_rows)
