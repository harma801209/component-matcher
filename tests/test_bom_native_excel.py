import ast
import hashlib
import io
import json
from pathlib import Path
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bom_native_excel as native

ROOT = Path(__file__).resolve().parents[1]
URL = native.PUBLIC_ORIGIN + '/x/' + 'A' * 43 + '/BOM.xlsx'


class NativeExcelTests(unittest.TestCase):
    def test_transport_identifies_service_and_hot_reload_refreshes_helper(self):
        with patch.object(native.urllib.request, 'urlopen', return_value=io.BytesIO(b'{}')) as opened:
            self.assertEqual(native._request('test-service-secret','DELETE',{'owner':'a'*64}),{})
            request=opened.call_args.args[0]
            self.assertEqual(request.get_header('User-agent'),'fruition-component-matcher/bom-native-excel')
            self.assertEqual(request.get_header('Accept'),'application/json')
        entry=(ROOT/'streamlit_app.py').read_text(encoding='utf-8')
        self.assertIn('importlib.reload(importlib.import_module("bom_native_excel"))',entry)
        self.assertIn('native_excel_stat.st_mtime_ns',entry)

    def test_owner_is_secret_derived_and_uri_is_short_read_only_https(self):
        owner = native.owner_key('session-token', 'server-secret')
        self.assertEqual(len(owner), 64)
        self.assertNotEqual(owner, native.owner_key('different-session', 'server-secret'))
        self.assertNotEqual(owner, native.owner_key('session-token', 'different-secret'))
        self.assertEqual(native.excel_uri(URL), 'ms-excel:ofv|u|' + URL)
        self.assertLess(len(native.excel_uri(URL)), 216)
        for url in ['blob:fake', 'file:///tmp/a', URL + '?token=login', URL.replace('https:', 'http:'), 'https://evil.example/BOM.xlsx']:
            self.assertEqual(native.excel_uri(url), '')

    def test_issue_validates_server_response_and_never_sends_login_token(self):
        owner = native.owner_key('private-login-token', 'secret')
        with patch.object(native, '_request', return_value={'url':URL, 'expiresAt':time.time()+300}) as req:
            link = native.issue('secret', owner, b'PK\x03\x04xlsx', '匹配.xlsx')
        self.assertEqual(link['digest'], hashlib.sha256(b'PK\x03\x04xlsx').hexdigest())
        self.assertNotIn('private-login-token', json.dumps(req.call_args.args))
        for result in [{'url':'https://evil.example/a','expiresAt':time.time()+30},
                       {'url':URL,'expiresAt':time.time()-1}, {'url':URL,'expiresAt':time.time()+3600}]:
            with patch.object(native, '_request', return_value=result), self.assertRaises(ValueError):
                native.issue('secret', owner, b'PK\x03\x04xlsx','a.xlsx')

    def test_issue_rejects_unauthenticated_or_oversize_without_network(self):
        with patch.object(native, '_request') as req:
            for owner, secret, raw in [('', 'secret', b'PK\x03\x04xlsx'), ('a'*64,'',b'PK\x03\x04xlsx'),
                                       ('a'*64,'secret',b'fake'),('a'*64,'secret',b'PK\x03\x04'+b'x'*native.MAX_BYTES)]:
                with self.assertRaises(ValueError): native.issue(secret,owner,raw,'a.xlsx')
            req.assert_not_called()

    def test_revoke_retries_and_reports_failure_without_secret(self):
        with patch.object(native, '_request', side_effect=[OSError('network'), {'revoked':True}]) as req:
            native.revoke('secret','a'*64)
            self.assertEqual(req.call_count,2)
        with patch.object(native, '_request', side_effect=OSError('secret-leaking-original-error')):
            with self.assertRaisesRegex(RuntimeError,'revocation unavailable') as ctx:
                native.revoke('secret','a'*64)
            self.assertNotIn('secret-leaking',str(ctx.exception))

    def test_cached_link_reuses_exact_workbook_but_changes_owner_or_bytes(self):
        source = (ROOT/'component_matcher.py').read_text(encoding='utf-8')
        names = {'prepare_bom_native_excel_link','revoke_bom_native_excel_link'}
        nodes = [n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in names]
        warnings=[]; state={'_member_auth_token':'login'}
        ns={'st':SimpleNamespace(session_state=state,warning=warnings.append),
            'current_member':lambda:{'id':1}, 'clean_text':lambda v:str(v or '').strip(),
            'hashlib':hashlib,'time':time,'get_member_auth_remote_config':lambda:('unused','secret',True)}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'native-session-tests','exec'),ns)
        def issued(secret,owner,raw,filename):
            return {'owner':owner,'digest':hashlib.sha256(raw).hexdigest(),'expires':time.time()+300,'url':URL}
        with patch.object(native,'issue',side_effect=issued) as issue, patch.object(native,'revoke') as revoke:
            first,_=ns['prepare_bom_native_excel_link'](b'one','a.xlsx')
            same,_=ns['prepare_bom_native_excel_link'](b'one','a.xlsx')
            self.assertEqual(first,same); self.assertEqual(issue.call_count,1)
            ns['prepare_bom_native_excel_link'](b'two','b.xlsx')
            self.assertEqual(issue.call_count,2)
            ns['revoke_bom_native_excel_link']()
            revoke.assert_called_once_with('secret',first['owner'])
            self.assertNotIn('_bom_native_excel_link',state)
            ns['current_member']=lambda:None
            empty,reason=ns['prepare_bom_native_excel_link'](b'one','a.xlsx')
            self.assertEqual(empty,{}); self.assertTrue(reason)

    def test_all_clear_paths_revoke_before_discarding_session(self):
        tree=ast.parse((ROOT/'component_matcher.py').read_text(encoding='utf-8'))
        for name in ['logout_member','clear_customer_dependent_session_state','on_bom_upload_changed']:
            node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            text=ast.unparse(node)
            self.assertIn('revoke_bom_native_excel_link()',text)
            self.assertLess(text.index('revoke_bom_native_excel_link()'),text.index('st.session_state.pop'))


if __name__ == '__main__': unittest.main()
