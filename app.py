# -*- coding: utf-8 -*-

import errno, os, sys, tempfile

import traceback
import validators
import time
from collections import defaultdict
from cgi import escape
from datetime import datetime, timedelta
from error import error
from operator import itemgetter, attrgetter

# import for 'SHA'
import hashlib 

# import for Oxford Dictionary
import http.client
import requests
import json

# Database import
from db import kw_dict_mgr, group_ban, kwdict_col, gb_col

from flask import Flask, request, abort, url_for

from linebot import (
    LineBotApi, WebhookHandler, exceptions
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageTemplateAction,
    ButtonsTemplate, URITemplateAction, PostbackTemplateAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent
)

# Main initializing
app = Flask(__name__)
boot_up = datetime.now() + timedelta(hours=8)

class msg_counter(object):
    def __init__(self):
        self._rcv = 0
        self._rep = 0

    @property
    def recv(self):
        return self._rcv

    @property
    def repl(self):
        return self._rep

    def received(self):
        self._rcv += 1

    def replied(self):
        self._rep += 1

    def __repr__(self):
        return u'收到: {}, 回覆: {}'.format(self._rcv, self._rep)

rec = {'JC_called': 0, 'Msg': defaultdict(msg_counter), 'Silence': False, 'Intercept': True, 'webpage': 0}
report_content = {'Error': {}, 
                  'FullQuery': {}, 
                  'FullInfo': {},
                  'Text': {}}

class command(object):
    def __init__(self, min_split=2, max_split=2, non_user_permission_required=False):
        self._split_max = max_split
        self._split_min = min_split
        self._count = 0
        self._non_user_permission_required = non_user_permission_required

    @property
    def split_max(self):
        """Maximum split count."""
        return self._split_max + (1 if self._non_user_permission_required else 0) 

    @property
    def split_min(self):
        """Minimum split count."""
        return self._split_min

    @property
    def count(self):
        """Called count."""
        return self._count

    @count.setter
    def count(self, value):
        """Called count."""
        self._count = value 

    @property
    def non_user_permission_required(self):
        """Required Permission"""
        return self._non_user_permission_required

cmd_dict = {'S': command(1, 1, True), 
            'A': command(2, 4, False), 
            'M': command(2, 4, True), 
            'D': command(1, 2, False), 
            'R': command(1, 2, True), 
            'Q': command(1, 2, False), 
            'C': command(0, 0, True), 
            'I': command(1, 2, False), 
            'K': command(2, 2, False), 
            'P': command(0, 0, False), 
            'G': command(0, 0, False), 
            'GA': command(1, 5, True), 
            'H': command(0, 0, False), 
            'SHA': command(1, 1, False), 
            'O': command(1, 1, False), 
            'B': command(0, 0, False), 
            'U': command(0, 1, False)}

# Line Bot Environment initializing
MAIN_UID = 'Ud5a2b5bb5eca86342d3ed75d1d606e2c'
main_silent = False
administrator = os.getenv('ADMIN', None)
group_admin = os.getenv('G_ADMIN', None)
group_mod = os.getenv('G_MOD', None)
if administrator is None:
    print('The SHA224 of ADMIN not defined. Program will be terminated.')
    sys.exit(1)
if group_admin is None:
    print('The SHA224 of G_ADMIN not defined. Program will be terminated.')
    sys.exit(1)
if group_mod is None:
    print('The SHA224 of G_MOD not defined. Program will be terminated.')
    sys.exit(1)
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)
api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# Database initializing
kwd = kw_dict_mgr("postgres", os.environ["DATABASE_URL"])
gb = group_ban("postgres", os.environ["DATABASE_URL"])

# Oxford Dictionary Environment initializing
oxford_id = os.getenv('OXFORD_ID', None)
oxford_key = os.getenv('OXFORD_KEY', None)
oxford_disabled = False
if oxford_id is None:
    oxford_disabled = True
if oxford_key is None:
    oxford_disabled = True
language = 'en'
oxdict_url = 'https://od-api.oxforddictionaries.com:443/api/v1/entries/' + language + '/'


# File path
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')


# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except exceptions.InvalidSignatureError:
        abort(400)

    return 'OK'



@app.route("/error", methods=['GET'])
def get_error_list():
    rec['webpage'] += 1
    content = 'Boot up at {time}\n\nError list: '.format(time=boot_up)
    error_timestamps = report_content['Error'].keys()

    for timestamp in error_timestamps:
        content += html_hyperlink(timestamp, request.url_root + url_for('get_error_message', timestamp=timestamp)[1:])
        content += '\n'
        
    return content.replace('\n', '<br/>')

@app.route("/error/<timestamp>", methods=['GET'])
def get_error_message(timestamp):
    rec['webpage'] += 1
    error_message = report_content['Error'].get(timestamp)

    if error_message is None:
        content = error.webpage.no_content_at_time('error', float(timestamp))
    else:
        content = error_message
        
    return html_paragraph(content)

@app.route("/query/<timestamp>", methods=['GET'])
def full_query(timestamp):
    rec['webpage'] += 1
    query = report_content['FullQuery'].get(timestamp)
    
    if query is None:
        content = error.webpage.no_content_at_time('query', float(timestamp))
    else:
        content = query
        
    return html_paragraph(content)

@app.route("/info/<timestamp>", methods=['GET'])
def full_info(timestamp):
    rec['webpage'] += 1
    info = report_content['FullInfo'].get(timestamp)
    
    if info is None:
        content = error.webpage.no_content_at_time('info query', float(timestamp))
    else:
        content = info
        
    return html_paragraph(content)

@app.route("/full/<timestamp>", methods=['GET'])
def full_content(timestamp):
    rec['webpage'] += 1
    content_text = report_content['Text'].get(timestamp)
    
    if content_text is None:
        content = error.webpage.no_content_at_time('full text', float(timestamp))
    else:
        content = content_text
        
    return html_paragraph(content)

@app.route("/ranking/<type>", methods=['GET'])
def full_ranking(type):
    rec['webpage'] += 1
    if type == 'user':
        content = kw_dict_mgr.list_user_created_ranking(api, kwd.user_created_rank())
    elif type == 'used':
        content = kw_dict_mgr.list_keyword_ranking(kwd.order_by_usedrank())
    else:
        content = error.webpage.no_content()
        
    return html_paragraph(content)

def html_paragraph(content):
    return '<p>' + escape(content).replace(' ', '&nbsp;').replace('\n', '<br/>') + '</p>'

def html_hyperlink(content, link):
    return '<a href=\"{link}\">{content}</a>'.format(link=link, content=content)

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    token = event.reply_token
    text = event.message.text
    src = event.source
    splitter = '  '

    rec['Msg'][get_source_channel_id(src)].received()

    if text == administrator:
        rec['Silence'] = not rec['Silence']
        api.reply_message(token, TextSendMessage(text='Bot set to {mute}.'.format(mute='Silent' if rec['Silence'] else 'Active')))
        return
    elif rec['Silence']:
        return

    if text == '561563ed706e6f696abbe050ad79cf334b9262da6f83bc1dcf7328f2':
        rec['Intercept'] = not rec['Intercept']
        api.reply_message(token, TextSendMessage(text='Bot {}.'.format(
            'start to intercept messages.' if rec['Intercept'] else 'stop intercepting messages.')))
        return
    elif rec['Intercept']:
        intercept_text(event)

    try:
        if len(text.split(splitter)) >= 2 and text.startswith('JC'):
            head, cmd, oth = split(text, splitter, 3)

            if head == 'JC':
                rec['JC_called'] += 1

                if cmd not in cmd_dict:
                    text = error.main.invalid_thing(u'指令', cmd)
                    api_reply(token, TextSendMessage(text=text))
                    return

                max_prm = cmd_dict[cmd].split_max
                min_prm = cmd_dict[cmd].split_min
                params = split(oth, splitter, max_prm)

                if min_prm > len(params) - params.count(None):
                    text = error.main.lack_of_thing(u'參數')
                    api_reply(token, TextSendMessage(text=text))
                    return

                params.insert(0, None)
                cmd_dict[cmd].count += 1
                
                # SQL Command
                if cmd == 'S':
                    key = params.pop(1)
                    sql = params[1]

                    if isinstance(src, SourceUser) and permission_level(key) >= 3:
                        results = kwd.sql_cmd_only(sql)
                        if results is not None:
                            text = u'資料庫回傳結果({len}筆): \n'.format(len=len(results))
                            for result in results:
                                text += u'{result}\n'.format(result=result)
                        else:
                            text = error.main.no_result()
                    else:
                        text = error.main.restricted(3)

                    api_reply(token, TextSendMessage(text=text))
                # ADD keyword & ADD top keyword
                elif cmd == 'A' or cmd == 'M':
                    pinned = cmd_dict[cmd].non_user_permission_required
                    if pinned and permission_level(params.pop(1)) < 1:
                        text = error.main.restricted(1)
                    elif not isinstance(src, SourceUser):
                        text = error.main.incorrect_channel()
                    else:
                        new_uid = src.sender_id

                        if params[4] is not None:
                            action_kw = params[1]
                            kw = params[2]
                            action_rep = params[3]
                            rep = params[4]
                             
                            if action_kw != 'STK':
                                results = None
                                text = 'To use sticker-received-picture-or-sticker-reply function, the 1st parameter must be \'STK\'.'
                            elif not string_is_int(kw):
                                results = None
                                text = 'The 2nd parameter must be integer to represent sticker ID.'
                            elif action_rep != 'PIC':
                                results = None
                                text = 'To use sticker-received-picture-or-sticker-reply function, the 3rd parameter must be \'PIC\'.'
                            else:
                                if string_is_int(rep):
                                    rep = sticker_png_url(rep)
                                    url_val_result = True
                                else:
                                    url_val_result = url_val_result = True if validators.url(rep) and urlparse(rep).scheme == 'https' else False

                                if type(url_val_result) is bool and url_val_result:
                                    results = kwd.insert_keyword(kw, rep, new_uid, pinned, True, True)
                                else:
                                    results = None
                                    text = 'URL(parameter 4) is illegal. Probably URL not exist or incorrect format. Ensure to include protocol(http://).'
                        elif params[3] is not None:
                            rep = params[3]

                            if params[2] == 'PIC':
                                kw = params[1]

                                if string_is_int(rep):
                                    rep = sticker_png_url(rep)
                                    url_val_result = True
                                else:
                                    url_val_result = True if validators.url(rep) and urlparse(rep).scheme == 'https' else False

                                if type(url_val_result) is bool and url_val_result:
                                    results = kwd.insert_keyword(kw, rep, new_uid, pinned, False, True)
                                else:
                                    results = None
                                    text = 'URL(parameter 3) is illegal. Probably URL not exist or incorrect format. Ensure to include protocol(https://) and the URL scheme is HTTPS.\n'
                            elif params[1] == 'STK':
                                kw = params[2]

                                if string_is_int(kw):
                                    results = kwd.insert_keyword(kw, rep, new_uid, pinned, True, False)
                                else:
                                    results = None
                                    text = 'The 2nd parameter must be integer to represent sticker ID.'
                            else:
                                text = 'Unable to determine the function to use. parameter 1 must be \'STK\' or parameter 2 must be \'PIC\'. Check the user manual to get more details.'
                                results = None
                        elif params[2] is not None:
                            kw = params[1]
                            rep = params[2]

                            results = kwd.insert_keyword(kw, rep, new_uid, pinned, False, False)
                        else:
                            results = None
                            text = 'Lack of parameter(s). Please recheck your parameter(s) that correspond to the command.'

                        if results is not None:
                            text = u'已新增{top}回覆組。\n'.format(len=len(results), 
                                                                 top=u'置頂' if pinned else '')
                            for result in results:
                                text += kw_dict_mgr.entry_basic_info(result)

                    api_reply(token, TextSendMessage(text=text))
                # DELETE keyword & DELETE top keyword
                elif cmd == 'D' or cmd == 'R':
                    pinned = cmd_dict[cmd].non_user_permission_required
                    if pinned and permission_level(paramA.pop(1)) < 2:
                        text = 'Insufficient Permission.'
                    else:
                        if params[2] is None:
                            kw = params[1]

                            results = kwd.delete_keyword(kw, pinned)
                        else:
                            action = params[1]

                            if action == 'ID':
                                pair_id = params[2]

                                if string_is_int(pair_id):
                                    results = kwd.delete_keyword_id(pair_id, pinned)
                                else:
                                    results = None
                                    text = 'Illegal parameter 2. Parameter 2 need to be integer to delete keyword by ID.'
                            else:
                                results = None
                                text = 'Incorrect 1st parameter to delete keyword pair. To use ID to delete keyword, 1st parameter needs to be \'ID\'.'

                    if results is not None:
                        for result in results:
                            line_profile = profile(result[kwdict_col.creator])

                            text = 'Pair Deleted. {top}\n'.format(top='(top)' if pinned else '')
                            text += kw_dict_mgr.entry_basic_info(result)
                            text += u'\nThis pair is created by {name}.'.format(
                                name='(LINE account data not found)' if line_profile is None else line_profile.display_name)

                    api_reply(token, TextSendMessage(text=text))
                # QUERY keyword
                elif cmd == 'Q':
                    if params[2] is not None:
                        si = params[1]
                        ei = params[2]

                        try:
                            begin_index = int(si)
                            end_index = int(ei)

                            if end_index - begin_index < 0:
                                results = None
                                text = '2nd parameter must bigger than 1st parameter.'
                            else:
                                results = kwd.search_keyword_index(begin_index, end_index)
                        except ValueError:
                            results = None
                            text = 'Illegal parameter. 1rd parameter and 2nd parameter must be integer.'
                    else:
                        kw = params[1]

                        results = kwd.search_keyword(kw)

                    if results is not None:
                        q_list = kw_dict_mgr.list_keyword(results)
                        text = q_list['limited']
                        text += '\n\nFull Query URL: {url}'.format(url=rec_query(q_list['full']))
                    else:
                        if params[2] is not None:
                            text = 'Specified ID range to QUERY ({si}~{ei}) returned no data.'.format(si=si, ei=ei)
                        else:
                            text = u'Specified keyword to QUERY ({kw}) returned no data.'.format(kw=kw)

                    api_reply(token, TextSendMessage(text=text))
                # INFO of keyword
                elif cmd == 'I':
                    if params[2] is not None:
                        action = params[1]

                        if action != 'ID':
                            text = 'Incorrect 1st parameter to query information. To use this function, 1st parameter needs to be \'ID\'.'
                            results = None
                        else:
                            pair_id = params[2]

                            if string_is_int(pair_id):
                                results = kwd.get_info_id(pair_id)   
                            else:
                                results = None
                                text = 'Parameter 2 must be integer to represent pair ID.'
                    else:
                        kw = params[1]

                        results = kwd.get_info(kw)

                    if results is not None:
                        i_object = kw_dict_mgr.list_keyword_info(api, results)
                        text = i_object['limited']
                        text += '\n\nFull Info URL: {url}'.format(url=rec_info(i_object['full']))
                    else:
                        if params[2] is not None:
                            text = 'Specified ID to get INFORMATION (ID: {id}) returned no data.'.format(id=pair_id)
                        else:
                            text = u'Specified keyword to get INFORMATION ({kw}) returned no data.'.format(kw=kw)

                    api_reply(token, TextSendMessage(text=text))
                # RANKING
                elif cmd == 'K':
                    ranking_type = params[1]
                    limit = params[2]

                    try:
                        limit = int(limit)
                    except ValueError as err:
                        text = u'Invalid parameter. The 1st parameter of \'K\' function can be number only.\n\n'
                        text += u'Error message: {msg}'.format(msg=err.message)
                    else:
                        Valid = True

                        if ranking_type == 'USER':
                            text = kw_dict_mgr.list_user_created_ranking(api, kwd.user_created_rank(limit))
                        elif ranking_type == 'KW':
                            text = kw_dict_mgr.list_keyword_ranking(kwd.order_by_usedrank(limit))
                        else:
                            text = 'Parameter 1 must be \'USER\'(to look up the ranking of pair created group by user) or \'KW\' (to look up the ranking of pair\'s used time)'
                            Valid = False

                        if Valid:
                            text += '\n\nFull Ranking(user created) URL: {url_u}\nFull Ranking(keyword used) URL: {url_k}'.format(
                                url_u=request.url_root + url_for('full_ranking', type='user')[1:],
                                url_k=request.url_root + url_for('full_ranking', type='used')[1:])
                    
                    api_reply(token, TextSendMessage(text=text))
                # SPECIAL record
                elif cmd == 'P':
                    kwpct = kwd.row_count()

                    user_list_top = kwd.user_sort_by_created_pair()[0]
                    line_profile = profile(user_list_top[0])
                    
                    first = kwd.most_used()
                    last = kwd.least_used()
                    last_count = len(last)
                    limit = 10

                    sorted_msg = sorted(rec['Msg'].items(), key=lambda counter: (counter[1].recv + counter[1].repl), reverse=True)

                    text = u'從開機後開始統計的資料(連續30分鐘沒有收到任何訊息的話以下資料會全部歸零)\n'
                    text += u'開機時間: {bt} (台北時間)\n'.format(bt=boot_up)
                    text += u'\n收到了{}則訊息；回覆了{}則訊息\n'.format(sum(counter[1].recv for counter in sorted_msg), 
                                                                       sum(counter[1].repl for counter in sorted_msg))
                    for channel, counter in sorted_msg:
                        text += u'\n{} - {}'.format(channel, counter)

                    cmd_dict_text = ''
                    for cmd, cmd_obj in cmd_dict.items():
                        cmd_dict_text += u'\n指令{} - 呼叫{}次'.format(cmd, cmd_obj.count)
                    text += u'\n系統指令呼叫次數(包含呼叫失敗): {t}{info}'.format(t=rec['JC_called'], info=cmd_dict_text)
                    
                    text2 = u'全時統計資料\n\n'
                    text2 += u'已登錄回覆組: {ct}\n貼圖關鍵字: {stk_kw}組 | 圖片回覆: {pic_rep}組\n'.format(ct=kwpct,
                                                                                                            stk_kw=kwd.sticker_keyword_count(),
                                                                                                            pic_rep=kwd.picture_reply_count())
                    text2 += u'可使用回覆組: {ct} ({pct:.2f}%)\n(貼圖關鍵字: {stk_kw} | 圖片回覆: {pic_rep}組\n'.format(
                        ct=kwd.row_count(True),
                        stk_kw=kwd.sticker_keyword_count(True),
                        pic_rep=kwd.picture_reply_count(True),
                        pct=kwd.row_count(True) / float(kwpct) * 100)
                    text2 += u'總回覆次數: {crep}\n\n'.format(crep=kwd.used_count_sum())

                    text2 += u'製作最多回覆組的LINE使用者:\n{name} ({num} Pairs - {pct:.2f}%)\n\n'.format(
                        name=u'(LINE帳號資料不存在)' if line_profile is None else line_profile.display_name,
                        num=user_list_top[1],
                        pct=user_list_top[1] / float(kwpct) * 100)

                    text2 += u'呼叫最多次的回覆組({t}次，共{c}組):'.format(t=first[0][kwdict_col.used_count],
                                                                         c=len(first))
                    for entry in first:
                        text2 += u'\n{kw} (ID: {id})'.format(kw=u'(貼圖ID {id})'.format(id=entry[kwdict_col.keyword]) if entry[kwdict_col.is_sticker_kw] else entry[kwdict_col.keyword].decode('utf-8'),
                                                             id=entry[kwdict_col.id])

                    text2 += u'\n\n呼叫最少次的回覆組({t}次，共{c}組):'.format(t=last[0][kwdict_col.used_count],
                                                                     c=len(last))
                    for entry in last:
                        text2 += u'\n{kw} (ID: {id})'.format(kw=u'(貼圖ID {id})'.format(id=entry[kwdict_col.keyword]) if entry[kwdict_col.is_sticker_kw] else entry[kwdict_col.keyword].decode('utf-8'),
                                                             id=entry[kwdict_col.id])
                        
                        last_count -= 1
                        if len(last) - last_count >= limit:
                            text2 += '\n...(還有{left}組)'.format(left=last_count)
                            break

                    api_reply(token, [TextSendMessage(text=text), TextMessage(text=text2)])
                # GROUP ban basic (info)
                elif cmd == 'G':
                    if not isinstance(src, SourceUser):
                        group_detail = gb.get_group_by_id(gid)
                        gid = get_source_channel_id(src)
                        uid = group_detail[gb_col.admin]
                        admin_profile = profile(uid)

                        if group_detail is not None:
                            text = u'Chat Group ID: {id}\n'.format(id=group_detail[gb_col.groupId])
                            text += u'Silence: {sl}\n\n'.format(sl=group_detail[gb_col.silence])
                            text += u'Admin: {name}\n'.format(name='(LINE account data not found)' if admin_profile is None else admin_profile.display_name)
                            text += u'Admin User ID: {name}'.format(name=group_detail[gb_col.admin])
                        else:
                            text = u'Chat Group ID: {id}\n'.format(id=gid)
                            text += u'Silence: False'
                    else:
                        text = 'This function can be only execute in GROUP or ROOM.'
                    
                    api_reply(token, TextSendMessage(text=text))
                # GROUP ban advance
                elif cmd == 'GA':
                    error_no_action_fetch = 'No command fetched.\nWrong command, parameters or insufficient permission to use the function.'
                    illegal_source = 'This function can be used in 1v1 CHAT only. Permission key required. Please contact admin.'
                    
                    perm_dict = {3: 'Permission: Bot Administrator',
                                 2: 'Permission: Group Admin',
                                 1: 'Permission: Group Moderator',
                                 0: 'Permission: User'}
                    perm = permission_level(params.pop(1))
                    pert = perm_dict[perm]

                    param_count = len(params) - params.count(None) - 1

                    if isinstance(src, SourceUser):
                        text = error_no_action_fetch

                        if perm >= 1 and param_count == 3:
                            action = params[1]
                            gid = params[2]
                            pw = params[3]

                            action_dict = {'SF': True, 'ST': False}
                            status_silence = {True: 'disabled', False: 'enabled'}

                            if action in action_dict:
                                settarget = action_dict[action]

                                if gb.set_silence(params[2], str(settarget), pw):
                                    text = 'Group auto reply function has been {res}.\n\n'.format(res=status_silence[settarget].upper())
                                    text += 'GID: {gid}'.format(gid=gid)
                                else:
                                    text = 'Group auto reply setting not changed.\n\n'
                                    text += 'GID: {gid}'.format(gid=gid)
                            else:
                                text = 'Invalid action: {action}. Recheck User Manual.'.format(action=action)
                        elif perm >= 2 and param_count == 5:
                            action = params[1]
                            gid = params[2]
                            new_uid = params[3]
                            pw = params[4]
                            new_pw = params[5]

                            action_dict = {'SA': gb.change_admin, 
                                           'SM1': gb.set_mod1,
                                           'SM2': gb.set_mod2,
                                           'SM3': gb.set_mod3}
                            pos_name = {'SA': 'Administrator',
                                        'SM1': 'Moderator 1',
                                        'SM2': 'Moderator 2',
                                        'SM3': 'Moderator 3'}

                            line_profile = profile(new_uid)

                            if line_profile is not None:
                                try:
                                    if action_dict[action](gid, new_uid, pw, new_pw):
                                        position = pos_name[action]

                                        text = u'Group administrator has been changed.\n'
                                        text += u'Group ID: {gid}\n\n'.format(gid=gid)
                                        text += u'New {pos} User ID: {uid}\n'.format(uid=new_uid, pos=position)
                                        text += u'New {pos} User Name: {unm}\n\n'.format(
                                            unm=line_profile.display_name,
                                            pos=position)
                                        text += u'New {pos} Key: {npkey}\n'.format(npkey=new_pw, pos=position)
                                        text += u'Please protect your key well!'
                                    else:
                                        text = '{pos} changing process failed.'
                                except KeyError as Ex:
                                    text = 'Invalid action: {action}. Recheck User Manual.'.format(action=action)
                            else:
                                text = 'Profile of \'User ID: {uid}\' not found.'.format(uid=new_uid)
                        elif perm >= 3 and param_count == 4:
                            action = params[1]
                            gid = params[2]
                            uid = params[3]
                            pw = params[4]
                            
                            if action != 'N':
                                text = 'Illegal action: {action}'.format(action=action)
                            else:
                                line_profile = profile(uid)

                                if line_profile is not None:
                                    if gb.new_data(gid, uid, pw):
                                        text = u'Group data registered.\n'
                                        text += u'Group ID: {gid}'.format(gid=gid)
                                        text += u'Admin ID: {uid}'.format(uid=uid)
                                        text += u'Admin Name: {name}'.format(gid=line_profile.display_name)
                                    else:
                                        text = 'Group data register failed.'
                                else:
                                    text = 'Profile of \'User ID: {uid}\' not found.'.format(uid=new_uid)
                    else:
                        text = illegal_source

                    api_reply(token, [TextSendMessage(text=pert), TextSendMessage(text=text)])
                # get CHAT id
                elif cmd == 'H':
                    text = get_source_channel_id(src)

                    if isinstance(src, SourceUser):
                        source_type = 'Type: User'
                    elif isinstance(src, SourceGroup):
                        source_type = 'Type: Group'
                    elif isinstance(src, SourceRoom):
                        source_type = 'Type: Room'
                    else:
                        text = 'Unknown chatting type.'

                    api_reply(token, [TextSendMessage(text=source_type), TextSendMessage(text=text)])
                # SHA224 generator
                elif cmd == 'SHA':
                    target = params[1]

                    if target != None:
                        text = hashlib.sha224(target.encode('utf-8')).hexdigest()
                    else:
                        text = 'Illegal Parameter to generate SHA224 hash.'

                    api_reply(token, TextSendMessage(text=text))
                # Look up vocabulary in OXFORD Dictionary
                elif cmd == 'O':
                    voc = params[1]

                    if oxford_disabled:
                        text = 'Dictionary look up function has disabled because of illegal Oxford API key or ID.'
                    else:
                        j = oxford_json(voc)

                        if type(j) is int:
                            code = j

                            text = 'Dictionary look up process returned status code: {status_code} ({explanation}).'.format(
                                status_code=code,
                                explanation=httplib.responses[code])
                        else:
                            text = 'Powered by Oxford Dictionary.\n'

                            lexents = j['results'][0]['lexicalEntries']
                            for lexent in lexents:
                                text += '\n{text} ({lexCat})'.format(text=lexent['text'], lexCat=lexent['lexicalCategory'])
                                
                                sens = lexent['entries'][0]['senses']
                                
                                text += '\nDefinition:'
                                for index, sen in enumerate(sens):
                                    for de in sen['definitions']:
                                        text += '\n{count}. {de}'.format(count=index+1, de=de)

                    api_reply(token, TextSendMessage(text=text))
                # Leave group or room
                elif cmd == 'B':
                    cid = get_source_channel_id(src)

                    if isinstance(src, SourceUser):
                        text = 'Unable to leave 1v1 chat.'
                        api_reply(token, TextSendMessage(text=text))
                    else:
                        api_reply(token, TextSendMessage(text='Channel ID: {cid}\nBot Contact Link: http://line.me/ti/p/@fcb0332q'.format(cid=cid)))

                        if isinstance(src, SourceRoom):
                            api.leave_room(cid)
                        elif isinstance(src, SourceGroup):
                            api.leave_group(cid)
                # User profile
                elif cmd == 'U':
                    uid = params[1]

                    if uid is not None and len(uid) != 33:
                        text = 'The length of user id must be 33 characters.'   
                    else:
                        if isinstance(src, SourceUser):
                            line_profile = profile(uid if uid is not None else src.sender_id)

                            text = u'User ID:\n{uid}\nUser name:\n{name}\nProfile Picture URL:\n{url}\nStatus Message:\n{msg}'.format(
                                    uid=line_profile.user_id,
                                    name=line_profile.display_name,
                                    url=line_profile.picture_url,
                                    msg=line_profile.status_message)
                        else:
                            text = 'Unable to use this function in Group or Room.'

                    api_reply(token, TextSendMessage(text=text))
                else:
                    cmd_dict[cmd].count -= 1
        else:
            reply_message_by_keyword(get_source_channel_id(src), token, text, False)
    except exceptions.LineBotApiError as ex:
        text = u'開機時間: {boot}\n\n'.format(boot=boot_up)
        text += u'LINE API內部錯誤。狀態碼: {sc}\n\n'.format(sc=ex.status_code)
        for err in ex.error.details:
            text += u'內容: {prop}\訊息: {msg}\n'.format(prop=err.property, msg=err.message)

        send_error_url_line(token, text, get_source_channel_id(src))
    except Exception as exc:
        text = u'開機時間: {boot}\n\n'.format(boot=boot_up)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        text += u'種類: {type}\n詳細訊息: {msg}\n於第{lineno}行'.format(type=exc_type, lineno=exc_tb.tb_lineno, msg=exc.args)

        send_error_url_line(token, text, get_source_channel_id(src))
    return

    if text == 'confirm':
        confirm_template = ConfirmTemplate(text='Do it?', actions=[
            MessageTemplateAction(label='Yes', text='Yes!'),
            MessageTemplateAction(label='No', text='No!'),
        ])
        template_message = TemplateSendMessage(
            alt_text='Confirm alt text', template=confirm_template)
        api_reply(event.reply_token, template_message)
    elif text == 'carousel':
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(text='hoge1', title='fuga1', actions=[
                URITemplateAction(
                    label='Go to line.me', uri='https://line.me'),
                PostbackTemplateAction(label='ping', data='ping')
            ]),
            CarouselColumn(text='hoge2', title='fuga2', actions=[
                PostbackTemplateAction(
                    label='ping with text', data='ping',
                    text='ping'),
                MessageTemplateAction(label='Translate Rice', text='米')
            ]),
        ])
        template_message = TemplateSendMessage(
            alt_text='Buttons alt text', template=carousel_template)
        api_reply(event.reply_token, template_message)


# Incomplete
@handler.add(PostbackEvent)
def handle_postback(event):
    return
    if event.postback.data == 'ping':
        api_reply(
            event.reply_token, TextSendMessage(text='pong'))


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    package_id = event.message.package_id
    sticker_id = event.message.sticker_id
    rep = event.reply_token
    src = event.source

    rec['Msg'][get_source_channel_id(src)].received()

    if isinstance(event.source, SourceUser):
        results = kwd.get_reply(sticker_id, True)
        
        if results is not None:
            result = results[0]
            kwdata = u'相關可用回覆組ID: {id}\n'.format(id=result[kwdict_col.id])
        else:
            kwdata = u'無相關可用回覆組。\n'

        api_reply(
            rep,
            [TextSendMessage(text=kwdata + u'貼圖圖包ID: {pck_id}\n貼圖ID: {stk_id}'.format(
                pck_id=package_id, 
                stk_id=sticker_id)),
             TextSendMessage(text=u'貼圖檔案(png)在「Android手機」上的路徑:\nemulated\\0\\Android\\data\\jp.naver.line.android\\stickers\\{pck_id}\\{stk_id}'.format(
                pck_id=package_id, 
                stk_id=sticker_id)),
             TextSendMessage(text=u'貼圖檔案(png)在「Windows電腦」上的路徑:\nC:\\Users\\USER_NAME\\AppData\\Local\\LINE\\Data\\Sticker\\{pck_id}\\{stk_id}'.format(
                pck_id=package_id, 
                stk_id=sticker_id)),
             TextSendMessage(text=u'貼圖檔案(png)在「網路」上的路徑:\n{stk_url}'.format(stk_url=sticker_png_url(sticker_id)))]
        )
    else:
        reply_message_by_keyword(get_source_channel_id(src), rep, sticker_id, True)


# Incomplete
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    rec['Msg'][get_source_channel_id(event.source)].received()
    return

    api_reply(
        event.reply_token,
        LocationSendMessage(
            title=event.message.title, address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        )
    )


# Incomplete
@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
    rec['Msg'][get_source_channel_id(event.source)].received()
    return

    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_content = api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    api_reply(
        event.reply_token, [
            TextSendMessage(text='Save content.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ])


@handler.add(FollowEvent)
def handle_follow(event):
    api_reply(event.reply_token, introduction_template())

# Incomplete
@handler.add(UnfollowEvent)
def handle_unfollow():
    return

    app.logger.info("Got Unfollow event")


@handler.add(JoinEvent)
def handle_join(event):
    api_reply(event.reply_token, introduction_template())

    if isinstance(event.source, SourceGroup):
        gb.new_data(event.source.group_id, MAIN_UID, 'RaenonX')
        api_reply(event.reply_token, TextMessage(text=u'群組資料已註冊。輸入\'JC G\'以獲得群組資訊。'))
    if isinstance(event.source, SourceRoom):
        gb.new_data(event.source.room_id, MAIN_UID, 'RaenonX')
        api_reply(event.reply_token, TextMessage(text=u'群組資料已註冊. 輸入\'JC G\'以獲得群組資訊。'))


# Encapsulated Functions
def split(text, splitter, size):
    list = []
  
    if text is not None:
        for i in range(size):
            if splitter not in text or i == size - 1:
                list.append(text)
                break
            list.append(text[0:text.index(splitter)])
            text = text[text.index(splitter)+len(splitter):]
  
    while len(list) < size:
        list.append(None)
    
    return list


def permission_level(key):
    if hashlib.sha224(key).hexdigest() == administrator:
        return 3
    elif hashlib.sha224(key).hexdigest() == group_admin:
        return 2
    elif hashlib.sha224(key).hexdigest() == group_mod:
        return 1
    else:
        return 0


def oxford_json(word):
    url = oxdict_url + word.lower()
    r = requests.get(url, headers = {'app_id': oxford_id, 'app_key': oxford_key})
    status_code = r.status_code

    if status_code != requests.codes.ok:
        return status_code
    else:
        return r.json()


def introduction_template():
    buttons_template = ButtonsTemplate(
            title='Introduction', text=u'歡迎使用小水母！', 
            actions=[
                URITemplateAction(label=u'點此開啟使用說明', uri='https://sites.google.com/view/jellybot'),
                URITemplateAction(label=u'點此導向開發者LINE帳號', uri='http://line.me/ti/p/~chris80124')
            ])
    template_message = TemplateSendMessage(
        alt_text='小水母簡介', template=buttons_template)
    return template_message


def sticker_png_url(sticker_id):
    return kw_dict_mgr.sticker_png_url(sticker_id)


def get_source_channel_id(source_event):
    return source_event.sender_id


def string_is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


def api_reply(reply_token, msgs, source):
    rec['Msg'][get_source_channel_id(source)].received()

    if not rec['Silence']:
        if not isinstance(msgs, (list, tuple)):
            msgs = [msgs]

        for msg in msgs:
            if isinstance(msg, TextSendMessage) and len(msg.text) > 2000:
                api.reply_message(reply_token, 
                                  TextSendMessage(
                                      text=u'因回覆內容已超過LINE API單筆訊息限制(2000字)，故無法在此顯示。請點擊以下網址以查看訊息:\n{url}'.format(url=rec_text(msgs))))
                return

        api.reply_message(reply_token, msgs)
    else:
        print('==================================================================')
        print('Bot set to silence. Expected message to reply will display below: ')
        print(msgs)
        print('==================================================================')


def intercept_text(event):
    print('===========================================')
    print('From Channel ID \'{}\''.format(get_source_channel_id(event.source)))
    print('Message \'{}\''.format(event.message.text.encode('utf-8')))
    print('===========================================')


def reply_message_by_keyword(channel_id, token, keyword, is_sticker_kw):
        if gb.is_group_set_to_silence(channel_id):
            return

        res = kwd.get_reply(keyword, is_sticker_kw)
        if res is not None:
            result = res[0]
            reply = result[kwdict_col.reply].decode('utf-8')

            if result[kwdict_col.is_pic_reply]:
                line_profile = profile(result[kwdict_col.creator])

                api_reply(token, TemplateSendMessage(
                    alt_text='Picture / Sticker Reply.\nID: {id}'.format(id=result[kwdict_col.id]),
                    template=ButtonsTemplate(text=u'ID: {id}\nCreated by {creator}.'.format(
                        creator='(LINE account data not found)' if line_profile is None else line_profile.display_name,
                        id=result[kwdict_col.id]), 
                                             thumbnail_image_url=reply,
                                             actions=[
                                                 URITemplateAction(label=u'Original Picture', uri=reply)
                                             ])))
            else:
                api_reply(token, TextSendMessage(text=u'{rep}{id}'.format(rep=reply,
                                                                          id='' if not is_sticker_kw else '\n\nID: {id}'.format(id=result[kwdict_col.id]))))


def rec_error(details, channel_id):
    if details is not None:
        timestamp = str(int(time.time()))
        report_content['Error'][timestamp] = u'發生於 {time}\n'.format(time=datetime.now() + timedelta(hours=8))
        report_content['Error'][timestamp] = u'頻道ID: {cid}'.format(cid=channel_id)
        report_content['Error'][timestamp] += u'\n\n'
        report_content['Error'][timestamp] += details  
        return timestamp


def rec_query(full_query):
    timestamp = str(int(time.time()))
    report_content['FullQuery'][timestamp] = full_query
    return request.url_root + url_for('full_query', timestamp=timestamp)[1:]


def rec_info(full_info):
    timestamp = str(int(time.time()))
    report_content['FullInfo'][timestamp] = full_info
    return request.url_root + url_for('full_info', timestamp=timestamp)[1:]


def rec_text(textmsg_list):
    if not isinstance(textmsg_list, (list, tuple)):
        textmsg_list = [textmsg_list]

    timestamp = str(int(time.time()))
    report_content['Text'][timestamp] = ''
    for index, txt in enumerate(textmsg_list, start=1):
        report_content['Text'][timestamp] += '================第{index}則訊息================\n'.format(index=index)
        report_content['Text'][timestamp] += txt.text
        report_content['Text'][timestamp] += '\n===============================================\n'
    return request.url_root + url_for('full_content', timestamp=timestamp)[1:]



def send_error_url_line(token, error_text, channel_id):
    timestamp = rec_error(traceback.format_exc(), channel_id)
    err_detail = u'完整錯誤訊息: {url}\n發生過的錯誤(清單): {url_full}\n回報錯誤:{issue}'.format(
        url=request.url_root + url_for('get_error_message', timestamp=timestamp)[1:],
        url_full=request.url_root + url_for('get_error_list')[1:],
        issue='https://github.com/RaenonX/LineBot/issues')
    print(report_content['Error'][timestamp])
    api_reply(token, [TextSendMessage(text=error_text), TextSendMessage(text=err_detail)])


def profile(uid):
    try:
        return api.get_profile(uid)
    except exceptions.LineBotApiError as ex:
        if ex.status_code == 404:
            return None


if __name__ == "__main__":
    # create tmp dir for download content
    make_static_tmp_dir()

    app.run(port=os.environ['PORT'], host='0.0.0.0')
