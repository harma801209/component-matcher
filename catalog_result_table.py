"""Paged specification catalogue; display data only, validated explicit actions."""
import hashlib
import json
from pathlib import Path

PREFIX = 'catalog_filter_'


def numeric_display(field, value):
    number=float(value)
    magnitude=abs(number)
    unit,scale=field.units[0]
    if field.key=='_pf':unit,scale=('µF',1e6) if magnitude>=1e6 else ('nF',1e3) if magnitude>=1e3 else ('pF',1)
    elif field.key=='_res_ohm':unit,scale=('MΩ',1e6) if magnitude>=1e6 else ('kΩ',1e3) if magnitude>=1e3 else ('Ω',1)
    elif field.key=='frequency_hz':unit,scale=('MHz',1e6) if magnitude>=1e6 else ('kHz',1e3) if magnitude>=1e3 else ('Hz',1)
    elif field.key=='inductance_uh':unit,scale=('mH',1e3) if magnitude>=1e3 else ('nH',0.001) if 0<magnitude<1 else ('µH',1)
    elif field.key in {'_current_amps','_saturation_amps'}:unit,scale=('µA',1e-6) if 0<magnitude<0.001 else ('mA',0.001) if 0<magnitude<1 else ('A',1)
    return f'{number/scale:.12g} {unit}'


def build_payload(result, kind, condition, selected, ranges, keyword, sort_key='', sort_desc=False):
    from component_filters import option_label
    from amotech_catalog import SPECIAL_KINDS, SPECIAL_DETAIL_ONLY
    columns = [dict(key='型号',label='型号',visible=True), dict(key='品牌',label='品牌',visible=True)]
    rows = []
    for source in result['rows']:
        row = {'型号':source['型号'], '品牌':source.get('品牌') or '未提供'}
        row['id'] = hashlib.sha256(json.dumps([source.get('品牌'),source['型号']],ensure_ascii=False).encode()).hexdigest()[:24]
        if source.get('_lifecycle_source'):
            row['_lifecycle_source'] = source['_lifecycle_source']
            row['_lifecycle_checked'] = source.get('_lifecycle_checked','')
        for field in result['fields']:
            if field.key=='品牌':continue
            value=source.get(field.key)
            if field.units and value is not None:
                row[field.key]=numeric_display(field,value)
            else:row[field.key]=option_label(field,value)
        rows.append(row)
    primary=['_res_ohm','_pf','inductance_uh','impedance_ohm','frequency_hz','极性','_tol','频差（ppm）','_volt_num','_current_amps','_saturation_amps','_power_watt','_mat','封装代码','_size','输出类型','电源电压']
    fields=sorted(result['fields'],key=lambda f:primary.index(f.key) if f.key in primary else len(primary))
    labels={'_res_ohm':'阻值','_pf':'容量','inductance_uh':'电感量','impedance_ohm':'主值阻抗','frequency_hz':'频率','_saturation_amps':'饱和电流','_life_hours_num':'寿命'}
    for field in fields:
        if field.key=='品牌':continue
        # Empty-only columns remain available in Display Columns, not a sea
        # of unknown values crowding out actual specifications by default.
        facet=result['facets'].get(field.key,[])
        populated=(bool(facet) and facet[0] is not None) if field.units else any(value!='__catalog_missing__' for value,_ in facet)
        detail_only = kind in SPECIAL_KINDS and field.key in SPECIAL_DETAIL_ONLY
        columns.append(dict(key=field.key,label=labels.get(field.key,field.label.removesuffix('范围')),visible=populated and not detail_only))
    identity=[kind,selected,ranges,keyword,sort_key,sort_desc,result['total'],result['page'],result['page_size'],rows]
    view=hashlib.sha256(json.dumps(identity,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    return dict(view=view,kind=kind,condition=condition,columns=columns,rows=rows,total=result['total'],page=result['page'],pages=result['pages'],size=result['page_size'],sort=sort_key,desc=sort_desc)


def handle_request(state, payload, request, on_match):
    if not isinstance(request,dict) or request.get('view')!=payload['view']:
        return False
    event=request.get('event')
    if not isinstance(event,str) or not 1<=len(event)<=120 or state.get(PREFIX+'table_event')==event:
        return False
    action=request.get('action')
    if action=='match':
        row=next((r for r in payload['rows'] if r['id']==request.get('id')),None)
        if row is None:return False
        state[PREFIX+'table_event']=event
        on_match(row['型号'])
    elif action=='page':
        value=request.get('page')
        if type(value) is not int or not 1<=value<=payload['pages'] or value==payload['page']:return False
        state[PREFIX+'page']=value
    elif action=='size':
        value=request.get('size')
        if type(value) is not int or value not in (20,50,100) or value==payload['size']:return False
        state[PREFIX+'size']=value
        state[PREFIX+'page']=1
    elif action=='sort':
        key=request.get('column')
        if key not in [c['key'] for c in payload['columns']] or type(request.get('desc')) is not bool:return False
        state[PREFIX+'sort']=key
        state[PREFIX+'desc']=request['desc']
        state[PREFIX+'page']=1
    else:return False
    state[PREFIX+'table_event']=event
    return True


def render_table(payload,key):
    import streamlit.components.v1 as components
    folder=Path(__file__).with_name('catalog_results')
    revision=hashlib.sha256((folder/'index.html').read_bytes()).hexdigest()[:12]
    component=components.declare_component('catalog_specification_results_'+revision,path=str(folder))
    return component(payload=payload,key=key,default=None)
