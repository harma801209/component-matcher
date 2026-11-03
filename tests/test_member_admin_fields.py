"""Actual admin renderer, synthetic profiles only; never opens a runtime DB."""
import ast
import copy
from pathlib import Path
import unittest

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def render_fixture(st):
    st.session_state.setdefault('fixture_member',dict(id=901,username='DEMO_SALES',
        display_name='本地测试会员',company='富临通测试公司',email='',phone='',
        job_title='销售',role='member',status='active'))
    st.session_state.setdefault('fixture_brands',['FOJAN(富捷)'])
    st.session_state.setdefault('fixture_saves',[])
    st.session_state.setdefault('fixture_brand_reads',[])
    def read_brands(member_id):
        st.session_state.fixture_brand_reads.append(member_id)
        return list(st.session_state.fixture_brands)
    def save_member(**values):
        st.session_state.fixture_saves.append(copy.deepcopy(values))
        member=dict(st.session_state.fixture_member)
        for key in ('username','display_name','company','email','phone','job_title','role','status'):
            member[key]=values[key]
        st.session_state.fixture_member=member
        if values.get('pm_brands') is not None:
            st.session_state.fixture_brands=list(values['pm_brands'])
        return True,'仅本地测试状态已保存'
    def deny_delete(*args,**kwargs):
        raise AssertionError('This fixture never deletes a member')
    env=dict(st=st,pd=pd,re=__import__('re'),
        clean_text=lambda value:'' if value is None else str(value).strip(),
        MEMBER_JOB_TITLE_OPTIONS=('PM','销售','其他'),MEMBER_JOB_TITLE_PM='PM',
        MEMBER_JOB_TITLE_SALES='销售',MEMBER_JOB_TITLE_OTHER='其他',
        render_admin_section_header=lambda title,*args:st.subheader(title),
        render_admin_metric_cards=lambda *args:None,
        render_admin_empty_state=lambda *args:st.info('无测试会员'),
        list_members_for_admin=lambda:[dict(st.session_state.fixture_member)],
        member_matches_admin_keyword=lambda member,keyword:not keyword or keyword.lower() in member['username'].lower(),
        member_admin_summary_dataframe=lambda members:pd.DataFrame([dict(账号=m['username'],职务=m['job_title'],状态=m['status']) for m in members]),
        list_member_pm_brands=read_brands,
        list_pm_brand_options=lambda:['FOJAN(富捷)','信昌PDC'],
        normalize_pm_brand_names=lambda names:list(dict.fromkeys(names)),
        update_member_account_admin=save_member,
        current_member=lambda:dict(username='local-test-admin'),
        get_no_match_admin_credentials=lambda:('local-test-admin',''),
        delete_member_account_admin=deny_delete,
        list_member_sales_customers=lambda *args:[],
        list_member_profile_change_logs=lambda *args,**kwargs:[])
    names={'normalize_member_status','normalize_member_role','normalize_member_job_title',
           'render_member_admin_management_page'}
    tree=ast.parse((ROOT/'component_matcher.py').read_text(encoding='utf-8'))
    nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-member-form-fixture','exec'),env)
    env['render_member_admin_management_page']()


class MemberAdminFieldsTests(unittest.TestCase):
    def app(self,job_title='销售',role='member'):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_string('import streamlit as st\nfrom tests.test_member_admin_fields import render_fixture\nrender_fixture(st)')
        app.session_state['fixture_member']=dict(id=901,username='DEMO_ACCOUNT',display_name='测试会员',
            company='富临通测试公司',email='',phone='',job_title=job_title,role=role,status='active')
        app.run(timeout=30)
        self.assertFalse(app.exception)
        return app

    def save(self,app):
        next(b for b in app.button if b.label=='保存修改').click().run(timeout=30)
        self.assertFalse(app.exception)

    def test_only_pm_sees_brand_selector_regardless_of_member_or_admin_role(self):
        for job,role in [('销售','member'),('销售助理','member'),('其他','member'),('销售','admin'),('其他','admin')]:
            with self.subTest(job=job,role=role):
                app=self.app(job,role)
                self.assertEqual(len(app.multiselect),0)
                self.assertEqual(app.session_state['fixture_brand_reads'],[])
        for role in ('member','admin'):
            app=self.app('PM',role)
            self.assertEqual(app.multiselect[0].label,'PM 负责品牌')
            self.assertFalse(app.multiselect[0].disabled)

    def test_save_non_pm_preserves_inactive_brand_assignments_and_other_details(self):
        app=self.app()
        before=dict(app.session_state['fixture_member'])
        self.save(app)
        self.assertIsNone(app.session_state['fixture_saves'][-1]['pm_brands'])
        self.assertEqual(app.session_state['fixture_brands'],['FOJAN(富捷)'])
        self.assertEqual(app.session_state['fixture_member'],before)
        self.assertEqual(len(app.multiselect),0)

    def test_pm_can_edit_and_save_assigned_brands(self):
        app=self.app('PM')
        app.multiselect[0].select('信昌PDC')
        self.save(app)
        self.assertEqual(app.session_state['fixture_saves'][-1]['pm_brands'],['FOJAN(富捷)','信昌PDC'])
        self.assertEqual(app.session_state['fixture_brands'],['FOJAN(富捷)','信昌PDC'])

    def test_saved_job_changes_hide_or_show_field_without_clearing_existing_assignments(self):
        app=self.app('PM')
        next(s for s in app.selectbox if s.label=='职务').select('销售')
        self.save(app)
        self.assertEqual(app.session_state['fixture_member']['job_title'],'销售')
        self.assertEqual(len(app.multiselect),0)
        self.assertIsNone(app.session_state['fixture_saves'][-1]['pm_brands'])
        self.assertEqual(app.session_state['fixture_brands'],['FOJAN(富捷)'])
        next(s for s in app.selectbox if s.label=='职务').select('PM')
        self.save(app)
        self.assertEqual(app.session_state['fixture_member']['job_title'],'PM')
        self.assertEqual(app.multiselect[0].value,['FOJAN(富捷)'])

    def test_inactive_pm_brand_records_do_not_make_a_sales_member_pm(self):
        names={'normalize_member_role','normalize_member_job_title','member_company_is_fruition',
               'member_cost_access_level','member_pm_can_access_brand'}
        tree=ast.parse((ROOT/'component_matcher.py').read_text(encoding='utf-8'))
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        env=dict(re=__import__('re'),clean_text=lambda value:str(value or '').strip(),
                 MEMBER_JOB_TITLE_PM='PM',MEMBER_JOB_TITLE_SALES='销售',MEMBER_JOB_TITLE_OTHER='其他')
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-sales-permission-guard','exec'),env)
        for job in ('销售','销售助理'):
            member=dict(username='demo',role='member',company='富临通测试公司',job_title=job)
            self.assertEqual(env['member_cost_access_level'](member),'sales')
            self.assertFalse(env['member_pm_can_access_brand'](member,'FOJAN(富捷)',assigned_brands=['FOJAN(富捷)']))


if __name__=='__main__':unittest.main()
