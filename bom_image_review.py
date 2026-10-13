"""Read-only source geometry and explicit, source-bound user corrections."""
from __future__ import annotations

import hashlib
import io
import json

import pandas as pd


HELPERS = {'OCR原文', 'OCR行号', '识别提示', '_图片行号', '_已对照原图'}


def source_fingerprint(frame):
    payload = {'columns': list(frame.columns),
               'rows': [[str(value) for value in row] for row in frame.fillna('').itertuples(index=False,name=None)]}
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def editor_frame(source, current, confirmed=()):
    columns = [column for column in source.columns if column not in HELPERS
               and source[column].fillna('').astype(str).str.strip().ne('').any()]
    frame = current[columns].copy().reset_index(drop=True)
    frame.insert(0,'_图片行号',source.get('OCR行号',pd.Series(range(1,len(source)+1))).tolist())
    frame.insert(1,'_已对照原图',[idx in confirmed for idx in range(len(source))])
    return frame


def build_corrections(source, edited):
    expected = editor_frame(source,source)
    if len(edited) != len(source) or list(edited.columns) != list(expected.columns):
        raise ValueError('修正表的行列与原图不一致，请重新打开修正区域。')
    if edited['_图片行号'].tolist() != expected['_图片行号'].tolist():
        raise ValueError('原图行号不能修改。')
    changes, confirmed = {}, []
    for idx, row in edited.reset_index(drop=True).iterrows():
        if row['_已对照原图'] is True or row['_已对照原图'] == True:
            confirmed.append(int(idx))
        updates = {}
        for column in expected.columns:
            if column in HELPERS:
                continue
            value = str(row[column]) if pd.notna(row[column]) else ''
            if len(value) > 2000:
                raise ValueError('单个字段不能超过2000字，请缩短后保存。')
            old = str(source.iloc[idx][column]) if pd.notna(source.iloc[idx][column]) else ''
            if value != old:
                updates[column] = value
        if updates:
            changes[str(idx)] = updates
    return {'source': source_fingerprint(source), 'changes':changes, 'confirmed':confirmed}


def apply_corrections(source, payload, validate):
    result = source.copy(deep=True)
    if not payload:
        return result
    if payload.get('source') != source_fingerprint(source):
        raise ValueError('原图识别内容已变化，旧修正不能直接套用，请重新核对。')
    allowed = set(editor_frame(source,source).columns) - HELPERS
    changes = payload.get('changes',{})
    confirmed = payload.get('confirmed',[])
    if not isinstance(changes,dict) or not isinstance(confirmed,list) or len(changes)>len(source):
        raise ValueError('修正内容格式不正确。')
    for value in confirmed:
        if type(value) is not int or not 0 <= value < len(source):
            raise ValueError('修正行号不正确。')
    for index, updates in changes.items():
        if not isinstance(index,str) or not index.isdigit() or not 0<=int(index)<len(source) or not isinstance(updates,dict):
            raise ValueError('修正行号不正确。')
        idx = int(index)
        for column, value in updates.items():
            if column not in allowed or not isinstance(value,str) or len(value)>2000:
                raise ValueError('修正字段不正确。')
            result.at[result.index[idx],column] = value
    for idx in sorted(set(map(int,changes)) | set(confirmed)):
        notes = []
        if idx not in confirmed:
            notes.append(str(source.iloc[idx].get('识别提示','')))
        if str(idx) in changes:
            notes.append('人工修改：'+'、'.join(f'{column} {source.iloc[idx][column]} → {value}'
                                               for column,value in changes[str(idx)].items()))
        notes.append('已对照原图人工确认' if idx in confirmed else '修改后尚未人工确认，请对照原图')
        # Manual confirmation cannot erase an unresolved model/spec conflict.
        notes.extend(validate(result.iloc[idx].to_dict()))
        result.at[result.index[idx],'识别提示'] = '；'.join(note for note in notes if note)
    return result


def normalized_box(left,top,right,bottom,size):
    width,height = size
    return [max(0,min(1,left/width)),max(0,min(1,top/height)),
            max(0,min(1,right/width)),max(0,min(1,bottom/height))]


def crop_source(raw_bytes, box):
    from PIL import Image, ImageOps
    image=ImageOps.exif_transpose(Image.open(io.BytesIO(raw_bytes))).convert('RGB')
    if not isinstance(box,(list,tuple)) or len(box)!=4:
        raise ValueError('原图位置不可用，请查看完整原图。')
    values=[float(value) for value in box]
    if not all(0<=value<=1 for value in values) or values[2]<=values[0] or values[3]<=values[1]:
        raise ValueError('原图位置不可用，请查看完整原图。')
    bounds=(int(values[0]*image.width),int(values[1]*image.height),
            min(image.width,max(1,int(values[2]*image.width))),min(image.height,max(1,int(values[3]*image.height))))
    crop=image.crop(bounds)
    scale=min(3.0,2000/max(1,crop.width),900/max(1,crop.height))
    if scale>1:
        crop=crop.resize((int(crop.width*scale),int(crop.height*scale)),Image.Resampling.LANCZOS)
    return crop
