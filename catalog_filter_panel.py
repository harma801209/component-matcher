"""Manufacturer-style catalogue panel: metadata only, validated explicit actions."""
import hashlib
import json
from pathlib import Path

PREFIX = 'catalog_filter_'


def build_payload(categories, kind, baseline, result, selected, ranges, keyword, state):
    from component_filters import family_of_kind, option_label, MISSING
    groups = []
    for field in (baseline or {}).get('fields', []):
        base = baseline['facets'].get(field.key, [])
        live = result['facets'].get(field.key, [])
        group = dict(key=field.key, label=field.label.removesuffix('范围'), units=list(field.units))
        if field.units:
            if not base or base[0] is None:
                continue
            group.update(bounds=live, available=base,
                low=state.get(PREFIX+field.key+'_low', ''), high=state.get(PREFIX+field.key+'_high', ''),
                unit=state.get(PREFIX+field.key+'_unit', field.units[0][0]))
        else:
            if not any(value != MISSING for value, _ in base) and not selected.get(field.key):
                continue
            counts = dict(live)
            group['options'] = [dict(value=value, label=option_label(field,value), count=counts.get(value,0),
                checked=value in selected.get(field.key,[])) for value,_ in base]
        groups.append(group)
    payload = dict(kind=kind, categories=[dict(kind=k,count=n,family=family_of_kind(k)) for k,n in categories],
        groups=groups, keyword=keyword, keyword_mode=state.get(PREFIX+'keyword_mode','contains'), total=result['total'] if result else None)
    payload['view'] = hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    # A valid no-op (Search with the same text, or Clear on an empty filter)
    # must still acknowledge the click so the iframe leaves its busy state.
    payload['ack'] = state.get(PREFIX+'panel_event','')
    return payload


def handle_request(state, payload, request):
    from component_filters import reset_filters, parse_range
    if not isinstance(request,dict) or request.get('view') != payload['view']:
        return False
    event = request.get('event')
    if not isinstance(event,str) or not 1 <= len(event) <= 120 or state.get(PREFIX+'panel_event') == event:
        return False
    action = request.get('action')
    group = next((g for g in payload['groups'] if g['key'] == request.get('field')),None)
    if action == 'batch':
        actions = request.get('actions')
        if not isinstance(actions,list) or not 1 <= len(actions) <= 100:
            return False
        keys = {PREFIX+'keyword',PREFIX+'keyword_mode',PREFIX+'page',PREFIX+'picked',PREFIX+'panel_event'}
        for g in payload['groups']:
            keys.update(PREFIX+g['key']+suffix for suffix in (('_low','_high','_unit') if g['units'] else ('',)))
        draft = {key:state[key] for key in keys if key in state}
        for index,item in enumerate(actions):
            if not isinstance(item,dict) or item.get('action') not in ('choice','range','clear_group','keyword'):
                return False
            groups = []
            for g in payload['groups']:
                current = dict(g)
                if not g['units']:
                    current['options'] = [dict(o,checked=o['value'] in draft.get(PREFIX+g['key'],[])) for o in g['options']]
                groups.append(current)
            progress = dict(payload,groups=groups)
            child = dict(item,view=payload['view'],event=hashlib.sha256((event+':'+str(index)).encode()).hexdigest())
            if not handle_request(draft,progress,child):
                return False
        for key in keys:
            if key in draft:
                state[key] = draft[key]
            else:
                state.pop(key,None)
    elif action == 'kind':
        kind = request.get('kind')
        category = next((c for c in payload['categories'] if c['kind']==kind),None)
        if category is None or kind == payload['kind']:
            return False
        reset_filters(state)
        state[PREFIX+'category'] = kind
        state[PREFIX+'family'] = category['family']
    elif action == 'clear_all':
        kind = state.get(PREFIX+'category')
        family = state.get(PREFIX+'family')
        reset_filters(state)
        state[PREFIX+'category'], state[PREFIX+'family'] = kind, family
    elif action == 'choice':
        if group is None or group['units'] or type(request.get('checked')) is not bool:
            return False
        option = next((o for o in group['options'] if o['value'] == request.get('value')),None)
        if option is None or (request['checked'] and not option['checked'] and option['count']==0):
            return False
        current = [o['value'] for o in group['options'] if o['checked']]
        if request['checked'] and option['value'] not in current:
            if len(current) >= 100:
                return False
            current.append(option['value'])
        elif not request['checked'] and option['value'] in current:
            current.remove(option['value'])
        state[PREFIX+group['key']] = current
    elif action == 'range':
        if group is None or not group['units']:
            return False
        unit = request.get('unit')
        units = dict(group['units'])
        if not isinstance(unit,str) or unit not in units:
            return False
        low, high = request.get('low'), request.get('high')
        if not all(isinstance(x,str) and len(x)<=60 for x in (low,high)):
            return False
        try:
            parse_range(low,high,units[unit])
        except ValueError:
            return False
        for suffix,value in (('_low',low),('_high',high),('_unit',unit)):
            state[PREFIX+group['key']+suffix] = value
    elif action == 'clear_group':
        if group is None:
            return False
        for suffix in ('','_low','_high','_unit'):
            state.pop(PREFIX+group['key']+suffix,None)
    elif action == 'keyword':
        value = request.get('keyword')
        mode = request.get('mode',payload.get('keyword_mode','contains'))
        if not isinstance(value,str) or len(value)>120 or not isinstance(mode,str) or mode not in {'contains','prefix','exact'}:
            return False
        state[PREFIX+'keyword'] = value.strip()
        state[PREFIX+'keyword_mode'] = mode
    else:
        return False
    state[PREFIX+'page'] = 1
    state.pop(PREFIX+'picked',None)
    state[PREFIX+'panel_event'] = event
    return True


def render_panel(payload,key):
    import streamlit.components.v1 as components
    folder = Path(__file__).with_name('catalog_facets')
    # A changed component must get a new iframe URL, even when an existing
    # Streamlit frontend/session retains the old custom-component instance.
    revision = hashlib.sha256((folder/'index.html').read_bytes()).hexdigest()[:12]
    component = components.declare_component('catalog_parametric_filters_'+revision,path=str(folder))
    return component(payload=payload,key=key,default=None)
