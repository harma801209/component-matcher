"""One-shot, session-local BOM start intents, independent of widget rerenders."""
import secrets
from copy import deepcopy

START_KEY = '_bom_match_start_intent'


def queue_start(state, workbook_signature, export_mode):
    state[START_KEY] = {'workbook': str(workbook_signature), 'mode': str(export_mode),
                        'nonce': secrets.token_urlsafe(18)}


def consume_start(state, workbook_signature, export_mode):
    intent = state.pop(START_KEY, None)
    return bool(isinstance(intent, dict) and intent.get('nonce')
                and intent.get('workbook') == str(workbook_signature)
                and intent.get('mode') == str(export_mode))


def completed_rows(job, run_signature, sheet_lengths, member_key):
    """Recover complete rows, never run a matcher or reuse another price scope."""
    if (not isinstance(job, dict) or job.get('status') != 'complete'
            or not member_key or job.get('member_key') != member_key
            or job.get('run_signature') != run_signature or not sheet_lengths):
        return None
    total = sum(sheet_lengths.values())
    if total <= 0 or job.get('total_rows') != total or job.get('processed_rows') != total:
        return None
    checkpoint = job.get('checkpoint')
    if not isinstance(checkpoint, dict):
        return None
    sheets = checkpoint.get('sheet_rows')
    if not isinstance(sheets, dict) or set(sheets) != set(sheet_lengths):
        return None
    restored = {}
    for name, length in sheet_lengths.items():
        rows = sheets[name]
        if not isinstance(rows, dict) or len(rows) != length:
            return None
        keys = [str(key) for key in rows]
        if len(set(keys)) != length or set(keys) != {str(i) for i in range(length)}:
            return None
        rows = {str(key): value for key, value in rows.items()}
        ordered = [rows[str(i)] for i in range(length)]
        if any(not isinstance(row, dict) or not row.get('状态')
               or str(row.get('BOM行号', '')) != str(i + 2) for i, row in enumerate(ordered)):
            return None
        restored[name] = deepcopy(ordered)
    return restored
