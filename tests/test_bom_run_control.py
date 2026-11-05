"""UI rerender isolation; synthetic state only, no accounts, quotes or files."""
import ast
import copy
import hashlib
from types import SimpleNamespace
from pathlib import Path
import unittest
import concurrent.futures
import threading
import time
import sqlite3
import tempfile

import pandas as pd

from bom_run_control import START_KEY, completed_rows, consume_start, queue_start
import bom_model_comparison as comparison


class BomStartIntentTests(unittest.TestCase):
    def test_start_is_consumed_once_even_when_a_widget_trigger_is_replayed(self):
        state = {'result_signature': 'completed', 'export': b'KEEP', 'member': 'KEEP'}
        queue_start(state, 'same-bom', 'auto')
        executions = sum(consume_start(state, 'same-bom', 'auto') for stale_button_value in (True, True, True))
        self.assertEqual(executions, 1)
        self.assertNotIn(START_KEY, state)
        self.assertEqual(state, {'result_signature': 'completed', 'export': b'KEEP', 'member': 'KEEP'})

    def test_view_only_rerenders_never_queue_a_start(self):
        for action in ('scroll', 'resize', 'mount', 'compare', 'filter', 'page'):
            with self.subTest(action=action):
                self.assertFalse(consume_start({}, 'same-bom', 'auto'))

    def test_an_intent_cannot_move_to_another_upload_or_output_mode(self):
        for workbook, mode in (('another-bom', 'auto'), ('same-bom', 'custom')):
            state = {}
            queue_start(state, 'same-bom', 'auto')
            self.assertFalse(consume_start(state, workbook, mode))
            self.assertNotIn(START_KEY, state)

    def test_explicit_second_click_is_still_allowed_and_has_a_fresh_intent(self):
        state, nonces = {}, []
        for _ in range(2):
            queue_start(state, 'same-bom', 'auto')
            nonces.append(state[START_KEY]['nonce'])
            self.assertTrue(consume_start(state, 'same-bom', 'auto'))
        self.assertNotEqual(nonces[0], nonces[1])

    def test_actual_start_buttons_use_callbacks_not_replayable_return_values(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'component_matcher.py').read_text(encoding='utf-8'))
        page = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'render_bom_upload_page')
        starts = [n for n in ast.walk(page) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                  and n.func.attr == 'button' and n.args and isinstance(n.args[0], ast.Constant)
                  and n.args[0].value in ('开始主营品牌匹配', '开始指定品牌匹配')]
        self.assertEqual(len(starts), 2)
        for call in starts:
            callback = next(k.value for k in call.keywords if k.arg == 'on_click')
            self.assertEqual(callback.id, 'queue_bom_match_start')
            self.assertTrue(any(k.arg == 'args' for k in call.keywords))
        assigned = [n for n in ast.walk(page) if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'match_start_clicked' for t in n.targets)]
        self.assertFalse(any(isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
                             and n.value.func.attr == 'button' for n in assigned))
        self.assertEqual(sum(isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)
                             and n.value.func.id == 'consume_bom_match_start' for n in assigned), 1)

    def test_actual_upload_card_never_says_wait_for_click_after_start_or_interruption(self):
        source = (Path(__file__).resolve().parents[1] / 'component_matcher.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        cards = [node for node in ast.walk(tree) if isinstance(node, ast.Dict)
                 and any(isinstance(key, ast.Constant) and key.value == 'title'
                         and isinstance(value, ast.IfExp) for key, value in zip(node.keys, node.values))]
        card = next(node for node in cards if 'interrupted_before_result' in ast.unparse(node))
        code = compile(ast.Expression(body=card), '<actual-upload-card>', 'eval')
        for started, interrupted, title in ((True, False, 'BOM 正在准备匹配'),
                                             (False, True, 'BOM 匹配已中断'),
                                             (False, False, 'BOM 文件读取完成')):
            state = eval(code, dict(match_start_clicked=started, interrupted_before_result=interrupted,
                                    bom_sheet_frames=[1], total_workbook_rows=138,
                                    selected_sheet_name='Sheet1', output_selection_ready=True))
            self.assertEqual(state['title'], title)
            self.assertEqual(state['percent'], 0)
            if started or interrupted:
                self.assertNotIn('等待点击', state['subtitle'])

    def test_result_fragment_rechecks_access_before_reading_or_emitting_captured_data(self):
        class UI:
            def __init__(self): self.warnings, self.runs = [], 0
            def warning(self, message): self.warnings.append(message)
            def fragment(self, function):
                def run(*args, **kwargs):
                    self.runs += 1
                    return function(*args, **kwargs)
                return run
        ui, emitted = UI(), []
        result = comparison.render_table(ui, object(), table_html='PRIVATE', original_column_count=0,
                                         visible_columns=[], key='private', authorize_view=lambda: False,
                                         component=lambda **values: emitted.append(values))
        self.assertIsNone(result)
        self.assertEqual(ui.runs, 1)
        self.assertEqual(len(ui.warnings), 1)
        self.assertEqual(emitted, [])

    def test_actual_result_scope_changes_for_principal_permission_customer_and_price_revision(self):
        source = (Path(__file__).resolve().parents[1] / 'component_matcher.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'bom_result_view_authorization_scope')
        state = dict(member={'id': 7}, level='sales', allowed=True, customer=('existing', 'Synthetic A'), revision='A')
        env = dict(current_member=lambda: state['member'], member_cost_access_level=lambda _: state['level'],
                   member_can_view_cost=lambda _: state['allowed'],
                   selected_sales_cost_customer_context=lambda: state['customer'],
                   authorize_cost_customer_context=lambda member, kind, name: (kind, name),
                   selected_admin_cost_as_of=lambda member: '',
                   get_cost_price_lookup_signature=lambda *args, **kwargs: state['revision'])
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual-result-scope>', 'exec'), env)
        scope = env['bom_result_view_authorization_scope']
        original = scope(True)
        for key, value in [('member', {'id': 8}), ('level', 'pm'), ('customer', ('new', '')), ('revision', 'B')]:
            before = state[key]
            state[key] = value
            self.assertNotEqual(scope(True), original, key)
            state[key] = before
        state['allowed'] = False
        self.assertIsNone(scope(True))
        state['member'] = None
        self.assertIsNone(scope(False))


class CompletedResultRestoreTests(unittest.TestCase):
    def job(self):
        return dict(status='complete', member_key='id:7', run_signature='verified-price-scope',
                    total_rows=2, processed_rows=2, file_name='synthetic.csv', file_bytes=b'A\n1\n2',
                    file_sha256='synthetic', file_type='text/csv', mappings={'Sheet1': {'spec': 'spec'}},
                    checkpoint={'sheet_rows': {'Sheet1': {
                        '0': {'BOM行号': 2, '状态': '可推荐', '首选型号': 'DEMO1', '首选成本': 1.25},
                        '1': {'BOM行号': 3, '状态': '无匹配', '首选型号': ''}}}})

    def test_completed_rows_restore_in_source_order_without_mutating_checkpoint(self):
        job = self.job()
        saved = copy.deepcopy(job)
        restored = completed_rows(job, 'verified-price-scope', {'Sheet1': 2}, 'id:7')
        self.assertEqual([r['BOM行号'] for r in restored['Sheet1']], [2, 3])
        restored['Sheet1'][0]['首选成本'] = 999
        self.assertEqual(job, saved)

    def test_restore_rejects_other_owner_changed_price_scope_and_incomplete_jobs(self):
        for field, value in [('member_key', 'id:8'), ('run_signature', 'different-customer-or-price'),
                             ('status', 'running'), ('processed_rows', 1), ('total_rows', 3)]:
            with self.subTest(field=field):
                job = self.job()
                job[field] = value
                self.assertIsNone(completed_rows(job, 'verified-price-scope', {'Sheet1': 2}, 'id:7'))

    def test_restore_rejects_missing_sheets_rows_status_and_wrong_source_row_numbers(self):
        for mutation in ('sheet', 'row', 'status', 'number'):
            job = self.job()
            rows = job['checkpoint']['sheet_rows']['Sheet1']
            if mutation == 'sheet': job['checkpoint']['sheet_rows']['Extra'] = {}
            if mutation == 'row': rows.pop('1')
            if mutation == 'status': rows['0'].pop('状态')
            if mutation == 'number': rows['0']['BOM行号'] = 3
            self.assertIsNone(completed_rows(job, 'verified-price-scope', {'Sheet1': 2}, 'id:7'), mutation)

    def actual_function(self, name, env):
        source = (Path(__file__).resolve().parents[1] / 'component_matcher.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual-completed-job-restore>', 'exec'), env)
        return env[name]

    def test_completed_job_is_not_requeued_but_interrupted_job_still_has_resume_checkpoint(self):
        for status in ('complete', 'running'):
            state = {}
            job = self.job()
            job.update(status=status, job_id='synthetic-job')
            env = dict(st=SimpleNamespace(session_state=state), hashlib=hashlib,
                       current_bom_job_member_key=lambda: 'id:7', get_query_param_value=lambda key: 'synthetic-job',
                       get_bom_job=lambda job_id, member_key: job, update_query_params=lambda **kw: None,
                       clean_text=lambda x: str(x or '').strip(), BOM_JOB_QUERY_PARAM='job',
                       BOM_PENDING_UPLOAD_CACHE_KEY='upload', SessionCachedUploadedFile=lambda cache: cache)
            result = self.actual_function('restore_persisted_bom_job_upload', env)()
            self.assertIsNotNone(result)
            self.assertEqual('_bom_match_checkpoint' in state, status == 'running')

    def test_actual_restore_never_calls_matching_or_pricing_and_reuses_export(self):
        import pandas as pd
        state, exports = {}, []
        def forbidden(*args, **kwargs):
            raise AssertionError('Completed results must not rematch or reprice')
        env = dict(st=SimpleNamespace(session_state=state), pd=pd,
                   current_bom_job_member_key=lambda: 'id:7', normalize_bom_export_settings=lambda settings: settings,
                   move_reference_model_columns_after_rank=lambda frame: frame,
                   bom_to_excel_bytes=lambda *args, **kwargs: exports.append(kwargs) or b'PK-SYNTHETIC',
                   build_bom_workbook_sheet_results=forbidden, bom_dataframe_from_upload=forbidden,
                   load_authorized_cost_price_lookup=forbidden)
        restore = self.actual_function('restore_completed_bom_results', env)
        workbook = {'sheet_frames': [{'sheet_name': 'Sheet1', 'df': pd.DataFrame({'spec': ['A', 'B']})}]}
        args = (self.job(), 'verified-price-scope', workbook, 'Sheet1', {'include_cost': False})
        self.assertTrue(restore(*args))
        self.assertEqual(len(exports), 1)
        self.assertEqual(state['_bom_export_bytes'], b'PK-SYNTHETIC')
        self.assertEqual(state['_bom_result_df']['BOM行号'].tolist(), [2, 3])
        self.assertFalse(restore(*args))
        self.assertEqual(len(exports), 1)


class BomWorkerInterruptionTests(unittest.TestCase):
    """Execute the real row coordinator with synthetic rows, without app startup."""

    @classmethod
    def setUpClass(cls):
        source = (Path(__file__).resolve().parents[1] / 'component_matcher.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'bom_dataframe_from_upload')
        cls.code = compile(ast.Module(body=[node], type_ignores=[]), '<actual-bom-coordinator>', 'exec')

    def coordinator(self, builder, events=None):
        events = events if events is not None else []
        def cost(*args, **kwargs):
            events.append('cost')
            return {}
        def prefetch(*args, **kwargs):
            events.append('prefetch')
            return {}
        env = dict(pd=pd, time=time, threading=threading, BOM_MATCH_DEBUG=False,
                   ThreadPoolExecutor=concurrent.futures.ThreadPoolExecutor,
                   as_completed=concurrent.futures.as_completed, wait=concurrent.futures.wait,
                   FIRST_COMPLETED=concurrent.futures.FIRST_COMPLETED,
                   clean_text=lambda value: str(value or '').strip(),
                   looks_like_compact_part_query=lambda value: True,
                   extract_model_like_tokens=lambda value: [],
                   load_component_rows_by_exact_models_from_database=prefetch,
                   normalize_bom_export_settings=lambda value: value or {},
                   load_authorized_cost_price_lookup=cost, COST_CUSTOMER_TYPE_NEW='new',
                   load_resistor_series_pricing_rules=lambda: {},
                   build_bom_record_match_signature=lambda record, mapping, **kw: record['型号'],
                   clone_bom_result_for_source_row=lambda row, idx, record, mapping:
                       dict(row, BOM型号=record['型号'], BOM行号=idx + 2),
                   _BOM_SEARCH_ROW_CACHE=threading.local(),
                   is_public_mode=lambda: False, is_streamlit_cloud_runtime=lambda: False,
                   build_bom_upload_result_row=builder,
                   move_reference_model_columns_after_rank=lambda frame: frame)
        exec(self.code, env)
        return env['bom_dataframe_from_upload']

    def invoke(self, builder, count=20, **kwargs):
        return self.coordinator(builder)(None, pd.DataFrame({'型号': [f'P{i}' for i in range(count)]}),
                                         {'model': '型号'}, max_workers=1, **kwargs)

    def test_ui_interruption_does_not_drain_all_queued_bom_rows(self):
        class Rerun(BaseException):
            pass
        calls = []
        def builder(_df, idx, record, mapping, **kwargs):
            calls.append(idx)
            return {'状态': '可推荐', '首选推荐等级': '完全匹配'}
        def progress(state):
            if state.get('processed_rows', 0) >= 1:
                raise Rerun()
        with self.assertRaises(Rerun):
            self.invoke(builder, progress_callback=progress)
        self.assertEqual(calls, [0], 'A rerun must not leave the other 19 rows computing invisibly')

    def test_slow_row_keeps_progress_alive_without_false_completed_rows(self):
        release = threading.Event()
        heartbeats = []
        def builder(*args, **kwargs):
            if not release.wait(3):
                raise AssertionError('No heartbeat while waiting for a slow row')
            return {'状态': '可推荐', '首选推荐等级': '完全匹配'}
        def progress(state):
            if state.get('processed_rows') == 0 and state.get('elapsed_seconds', 0) >= 0.2:
                heartbeats.append(state)
                release.set()
        try:
            result = self.invoke(builder, count=1, progress_callback=progress)
        finally:
            release.set()
        self.assertTrue(heartbeats)
        self.assertEqual(heartbeats[0]['percent'], 0)
        self.assertEqual(heartbeats[0]['current_label'], '任务状态')
        self.assertNotIn('正在处理第',heartbeats[0]['current_text'])
        self.assertEqual(len(result), 1)

    def test_preparation_is_acknowledged_before_database_work(self):
        events = []
        run = self.coordinator(lambda *a, **kw: {'状态': '可推荐'}, events)
        run(None, pd.DataFrame({'型号': ['P0']}), {'model': '型号'}, max_workers=1,
            progress_callback=lambda state: events.append('progress'))
        self.assertEqual(events[0], 'progress')
        self.assertIn('prefetch', events)
        self.assertIn('cost', events)

    def test_bounded_dispatch_preserves_source_order_dedupe_and_checkpoints(self):
        calls, checkpoints = [], []
        def builder(_df, idx, record, mapping, **kwargs):
            calls.append(idx)
            return {'状态': '可推荐', '首选推荐等级': '完全匹配'}
        run = self.coordinator(builder)
        source = pd.DataFrame({'型号': ['A', 'B', 'A', 'C']})
        result = run(None, source, {'model': '型号'}, max_workers=2,
                     checkpoint_callback=lambda rows: checkpoints.append(rows))
        self.assertEqual(result['BOM型号'].tolist(), source['型号'].tolist())
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(checkpoints[-1]), 4)
        calls.clear()
        resumed = run(None, source, {'model': '型号'}, max_workers=2, resume_rows=checkpoints[-1])
        self.assertEqual(calls, [])
        self.assertEqual(resumed['BOM型号'].tolist(), source['型号'].tolist())

    def test_parallel_public_cold_preparation_runs_once_before_worker_dispatch(self):
        events = []
        main_thread = threading.get_ident()
        def builder(*args, **kwargs):
            events.append(('worker',threading.get_ident()))
            return {'状态':'可推荐'}
        run = self.coordinator(builder)
        run.__globals__['is_public_mode'] = lambda: True
        def warm(**kwargs):
            events.append(('warm',threading.get_ident()))
            return SimpleNamespace(close=lambda: events.append(('close',threading.get_ident())))
        run.__globals__['open_search_db_connection'] = warm
        run(None,pd.DataFrame({'型号':['A','B','C']}),{'model':'型号'},max_workers=2)
        self.assertEqual([event for event in events if event[0]=='warm'],[('warm',main_thread)])
        self.assertEqual(events[:2],[('warm',main_thread),('close',main_thread)])
        self.assertTrue(all(thread != main_thread for kind,thread in events if kind=='worker'))


class BomPublicConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'component_matcher.py').read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'open_search_db_connection')
        cls.code = compile(ast.Module(body=[node], type_ignores=[]), '<actual-public-search-connection>', 'exec')

    def opener(self, path, state, initialized):
        def overlay(conn):
            initialized.append(conn)
            conn.execute('CREATE TEMP TABLE test_overlay (value TEXT)')
        env = dict(os=__import__('os'), sqlite3=sqlite3, SEARCH_DB_PATH=str(path),
                   is_public_mode=lambda: True, is_streamlit_cloud_runtime=lambda: False,
                   _BOM_SEARCH_ROW_CACHE=state, install_jianghai_search_overlay=overlay,
                   install_amotech_catalogue_overlay=lambda conn: None,
                   _resistance_corrections=SimpleNamespace(install_search_overlay=lambda conn: None))
        exec(self.code, env)
        return env['open_search_db_connection']

    def test_same_public_bom_row_initializes_once_despite_caller_close(self):
        with tempfile.TemporaryDirectory(prefix='bom-connection-test-') as folder:
            path = Path(folder)/'public.sqlite'
            from contextlib import closing
            with closing(sqlite3.connect(path)) as seed:
                seed.execute('CREATE TABLE public_parts (model TEXT)')
                seed.commit()
            state, initialized = threading.local(), []
            state.connections = {}
            opened = []
            try:
                acquire = self.opener(path,state,initialized)
                for timeout in (30,10,30):
                    conn = acquire(timeout)
                    opened.append(conn)
                    self.assertEqual(conn.execute('PRAGMA busy_timeout').fetchone()[0], timeout*1000)
                    conn.close()
                self.assertEqual(len(initialized), 1)
                self.assertTrue(all(conn is opened[0] for conn in opened))
                self.assertEqual(opened[0].execute('SELECT COUNT(*) FROM public_parts').fetchone()[0], 0)
                with self.assertRaises(sqlite3.OperationalError):
                    opened[0].execute("INSERT INTO public_parts VALUES ('MUST NOT WRITE')")
            finally:
                for conn in opened:
                    getattr(conn,'release',conn.close)()

    def test_non_bom_search_connections_keep_normal_close_behavior(self):
        with tempfile.TemporaryDirectory(prefix='bom-connection-test-') as folder:
            path = Path(folder)/'public.sqlite'
            path.touch()
            state, initialized = threading.local(), []
            acquire = self.opener(path,state,initialized)
            for _ in range(3):
                conn = acquire()
                conn.close()
                with self.assertRaises(sqlite3.ProgrammingError):
                    conn.execute('SELECT 1')
            self.assertEqual(len(initialized),3)

    def test_scope_releases_on_error_and_does_not_leak_to_next_row(self):
        from bom_run_control import search_connection_scope, lease_public_search_connection
        state = threading.local()
        with self.assertRaisesRegex(RuntimeError,'interrupt'):
            with search_connection_scope(state):
                conn = lease_public_search_connection(state.connections,'public',
                           lambda **kwargs: sqlite3.connect(':memory:',**kwargs),lambda conn: None)
                conn.close()
                self.assertEqual(conn.execute('SELECT 7').fetchone()[0],7)
                raise RuntimeError('interrupt')
        self.assertFalse(hasattr(state,'connections'))
        with self.assertRaises(sqlite3.ProgrammingError):
            conn.execute('SELECT 1')
        with search_connection_scope(state):
            other = lease_public_search_connection(state.connections,'public',
                         lambda **kwargs: sqlite3.connect(':memory:',**kwargs),lambda conn: None)
            self.assertIsNot(conn,other)
        with self.assertRaises(sqlite3.ProgrammingError):
            other.execute('SELECT 1')

    def test_initialization_failure_closes_handle_and_never_caches_it(self):
        from bom_run_control import lease_public_search_connection
        pool, opened = {}, []
        def create(**kwargs):
            conn = sqlite3.connect(':memory:',**kwargs)
            opened.append(conn)
            return conn
        def fail(conn):
            raise ValueError('failed overlay')
        with self.assertRaisesRegex(ValueError,'failed overlay'):
            lease_public_search_connection(pool,'public',create,fail)
        self.assertEqual(pool,{})
        with self.assertRaises(sqlite3.ProgrammingError):
            opened[0].execute('SELECT 1')

    def test_connections_are_worker_local_not_shared_between_parallel_rows(self):
        from bom_run_control import search_connection_scope, lease_public_search_connection
        state, barrier = threading.local(), threading.Barrier(4)
        def worker(value):
            with search_connection_scope(state):
                conn = lease_public_search_connection(state.connections,'public',
                           lambda **kwargs: sqlite3.connect(':memory:',**kwargs),lambda conn: None)
                conn.execute('CREATE TEMP TABLE own_value (value INTEGER)')
                conn.execute('INSERT INTO own_value VALUES (?)',(value,))
                barrier.wait(timeout=20)
                same = lease_public_search_connection(state.connections,'public',lambda **kw: None,lambda conn: None)
                self.assertIs(conn,same)
                self.assertEqual(conn.execute('SELECT value FROM own_value').fetchone()[0],value)
                return conn
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            handles = list(executor.map(worker,range(4)))
        self.assertEqual(len({id(conn) for conn in handles}),4)


if __name__ == '__main__':
    unittest.main()
