# -*- coding: utf-8 -*-

import errno, os, sys, tempfile
import traceback
import validators
import time
from cgi import escape
from datetime import datetime, timedelta

# import for 'SHA'
import hashlib 

# import for Oxford Dictionary
import httplib
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
rec = {'JC_called': 0, 'Msg_Replied': 0, 'Msg_Received': 0, 'Silence': False}
report_content = {'Error': dict(), 'FullQuery': dict()}
cmd_called_time = {'S': 0, 'A': 0, 'M': 0, 'D': 0, 'R': 0, 'Q': 0, 
                   'C': 0, 'I': 0, 'K': 0, 'P': 0, 'G': 0, 'GA': 0, 
                   'H': 0, 'SHA': 0, 'O': 0, 'B': 0}

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


@app.route("/error/<timestamp>", methods=['GET'])
def get_error_message(timestamp):
    error_message = report_content['Error'][timestamp]

    if error_message is None:
        content = 'No error recorded at the specified time. ({time})'.format(time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)))
    else:
        content = error_message
        
    return '<p>' + escape(content).replace(' ', '&nbsp;').replace('\n', '<br/>') + '</p>'

@app.route("/query/<timestamp>", methods=['GET'])
def full_query(timestamp):
    query = report_content['FullQuery'][timestamp]
    
    if query is None:
        content = 'No query at the specified time. ({time})'.format(time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)))
    else:
        content = query
        
    return html_paragraph(content)

def html_paragraph(content):
    return '<p>' + escape(content).replace(' ', '&nbsp;').replace('\n', '<br/>') + '</p>'



@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    rec['Msg_Received'] += 1

    rep = event.reply_token
    text = event.message.text
    src = event.source
    splitter = '  '

    if text == administrator:
        rec['Silence'] = not rec['Silence']
        api.reply_message(rep, TextSendMessage(text='Set to {mute}.'.format(mute='Silent' if rec['Silence'] else 'Active')))
        return
    elif rec['Silence']:
        return

    try:
        if len(text.split(splitter)) > 1 and text.startswith('JC'):
            head, cmd, oth = split(text, splitter, 3)

            split_count = {'S': 4, 'A': 3, 'M': 3, 'D': 3, 'R': 3, 'Q': 3, 
                           'C': 2, 'I': 3, 'K': 3, 'P': 2, 'G': 2, 'GA': 3, 
                           'H': 2, 'SHA': 3, 'O': 3, 'B': 3}
            is_top = {'S': True, 'A': False, 'M': True, 'D': False, 'R': True, 'Q': False, 
                      'C': True, 'I': False, 'K': False, 'P': False, 'G': False, 'GA': True, 
                      'H': False, 'SHA': False, 'O': False, 'B': False}

            if head == 'JC':
                rec['JC_called'] += 1

                if cmd not in split_count:
                        text = u'Invalid Command: {cmd}. Please recheck the user manual.'.format(cmd=cmd)
                        api_reply(rep, TextSendMessage(text=text))
                        return

                prm_count = split_count[cmd]
                params = split(text, splitter, prm_count)

                if prm_count != len(params) - params.count(None):
                        text = u'Lack of parameter(s). Please recheck your parameter(s) that correspond to the command.'
                        api_reply(rep, TextSendMessage(text=text))
                        return

                head, cmd, param1, param2 = [params.pop(0) if len(params) > 0 else None for i in range(max(split_count.values()))]

                cmd_called_time[cmd] += 1
                
                # SQL Command
                if cmd == 'S':
                    if isinstance(src, SourceUser) and permission_level(param2) >= 3:
                        results = kwd.sql_cmd_only(param1)
                        if results is not None:
                            text = u'SQL command result({len}): \n'.format(len=len(results))
                            for result in results:
                                text += u'{result}\n'.format(result=result)
                                
                    else:
                        text = 'This is a restricted function.'

                    api_reply(rep, TextSendMessage(text=text))
                # CREATE kw_dict
                elif cmd == 'C':
                    text = 'Access denied. Insufficient permission.'

                    if permission_level(param2) >= 3:
                        text = 'Successfully Created.' if kwd.create_kwdict() == True else 'Creating failure.'

                    api_reply(rep, TextSendMessage(text=text))
                # ADD keyword & ADD top keyword
                elif cmd == 'A' or cmd == 'M':
                    max_param_count = 4
                    paramA = split(param1, splitter, max_param_count)
                    if is_top[cmd] and permission_level(paramA.pop(0)) < 3:
                        text = 'Insufficient Permission.'
                    elif not isinstance(src, SourceUser):
                        text = 'Unable to add keyword pair in GROUP or ROOM. Please go to 1v1 CHAT to execute this command.'
                    else:
                        param1, param2, param3, param4 = [paramA.pop(0) if len(paramA) > 0 else None for i in range(max_param_count)]

                        uid = src.user_id
                        if param4 is not None:
                            if param1 != 'STK':
                                results = None
                                text = 'To use sticker-received-picture-or-sticker-reply function, the 1st parameter must be \'STK\'.'
                            elif not string_is_int(param2):
                                results = None
                                text = 'The 2nd parameter must be integer to represent sticker ID.'
                            elif param3 != 'PIC':
                                results = None
                                text = 'To use sticker-received-picture-or-sticker-reply function, the 3rd parameter must be \'PIC\'.'
                            else:
                                if string_is_int(param4):
                                    param4 = sticker_png_url(param4)

                                url_val_result = validators.url(param4)
                                if type(url_val_result) is bool and url_val_result:
                                    results = kwd.insert_keyword(param2, param4, uid, is_top[cmd], True, True)
                                else:
                                    results = None
                                    text = 'URL(parameter 4) is illegal. \
                                            Probably URL not exist or incorrect format. Ensure to include protocol(http://).\n \
                                            {error}'.format(error=url_val_result)
                        elif param3 is not None:
                            if param2 == 'PIC':
                                if string_is_int(param3):
                                    param3 = sticker_png_url(param3)
                                    
                                    url_val_result = validators.url(param3)
                                    if type(url_val_result) is bool and url_val_result:
                                        results = kwd.insert_keyword(param1, param3, uid, is_top[cmd], False, True)
                                    else:
                                        results = None
                                        text = 'URL(parameter 3) is illegal. \
                                                Probably URL not exist or incorrect format. Ensure to include protocol(http://).\n \
                                                {error}'.format(error=url_val_result)
                            elif param1 == 'STK':
                                if string_is_int(param2):
                                    results = kwd.insert_keyword(param2, param3, uid, is_top[cmd], True, False)
                                else:
                                    results = None
                                    text = 'The 2nd parameter must be integer to represent sticker ID.'
                            else:
                                text = 'Unable to determine the function to use. parameter 1 must be \'STK\' or parameter 2 must be \'PIC\'. Check the user manual to get more details.'
                                results = None
                        elif param2 is not None:
                             results = kwd.insert_keyword(param1, param2, uid, is_top[cmd], False, False)
                        else:
                            results = None
                            text = 'Lack of parameter(s). Please recheck your parameter(s) that correspond to the command.'

                        if results is not None:
                            text = u'Pair Added. {top}\n'.format(len=len(results), 
                                                                 top='(top)' if is_top[cmd] else '')
                            for result in results:
                                text += kw_dict_mgr.entry_basic_info(result)

                    api_reply(rep, TextSendMessage(text=text))
                # DELETE keyword & DELETE top keyword
                elif cmd == 'D' or cmd == 'R':
                    extra_prm_count = 2
                    paramD = split(param1, splitter, extra_prm_count)

                    if is_top[cmd] and permission_level(paramA.pop(0)) < 2:
                        text = 'Insufficient Permission.'
                    else:
                        param1, param2 = [paramD.pop(0) if len(paramD) > 0 else None for i in range(extra_prm_count)]

                        if param2 is None:
                            results = kwd.delete_keyword(param1, is_top[cmd])
                        else:
                            if param1 == 'ID':
                                 if string_is_int(param2):
                                     results = kwd.delete_keyword_id(param2, is_top[cmd])
                                 else:
                                     results = None
                                     text = 'Illegal parameter 2. Parameter 2 need to be integer to delete keyword by ID.'
                            else:
                                results = None
                                text = 'Incorrect 1st parameter to delete keyword pair. To use ID to delete keyword, 1st parameter needs to be \'ID\'.'

                    if results is not None:
                        for result in results:
                            text = 'Pair Deleted. {top}\n'.format(top='(top)' if is_top[cmd] else '')
                            text += kw_dict_mgr.entry_basic_info(result)
                            profile = api.get_profile(result[kwdict_col.creator])
                            text += u'\nThis pair is created by {name}.'.format(name=profile.display_name)

                    api_reply(rep, TextSendMessage(text=text))
                # QUERY keyword
                elif cmd == 'Q':
                    if len(param1.split(splitter)) > 1:
                        extra_prm_count = 2
                        paramQ = split(param1, splitter, extra_prm_count)
                        param1, param2 = [paramQ.pop(0) if len(paramQ) > 0 else None for i in range(extra_prm_count)]
                        try:
                            begin_index = int(param1)
                            end_index = int(param2)

                            if end_index - begin_index < 0:
                                results = None
                                text = '2nd parameter must bigger than 1st parameter.'
                            else:
                                results = kwd.search_keyword_index(begin_index, end_index)
                        except ValueError:
                            results = None
                            text = 'Illegal parameter. 1rd parameter and 2nd parameter must be integer.'
                    else:
                        results = kwd.search_keyword(param1)

                    if results is not None:
                        q_list = kw_dict_mgr.list_keyword(results)
                        text = q_list['limited']
                        text += '\n\nFull Query URL: {url}'.format(url=rec_query(q_list['full']))
                    else:
                        if param2 is not None:
                            text = 'Specified ID range to QUERY ({si}~{ei}) returned no data.'.format(si=param1, ei=param2)
                        else:
                            text = 'Specified keyword to QUERY ({kw}) returned no data.'.format(kw=param1)

                    api_reply(rep, TextSendMessage(text=text))
                # - INFO of keyword
                elif cmd == 'I':
                    if len(param1.split(splitter)) > 1:
                        extra_prm_count = 2
                        paramI = split(param1, splitter, extra_prm_count)
                        param1, param2 = [paramI.pop(0) if len(paramI) > 0 else None for i in range(extra_prm_count)]
                        if param1 != 'ID':
                            text = 'Incorrect 1st parameter to query information. To use this function, 1st parameter needs to be \'ID\'.'
                            results = None
                        else:
                            results = kwd.get_info_id(param2)   
                    else:
                        results = kwd.get_info(param1)

                    if results is not None:
                        text = kw_dict_mgr.list_keyword_info(api, results)
                    else:
                        if param2 is not None:
                            text = 'Specified ID range to get INFORMATION ({si}~{ei}) returned no data.'.format(si=param1, ei=param2)
                        else:
                            text = 'Specified keyword to get INFORMATION ({kw}) returned no data.'.format(kw=param1)

                    print text
                    api_reply(rep, TextSendMessage(text=text))
                # - RANKING
                elif cmd == 'K':
                        try:
                            results = kwd.order_by_usedtime(int(param1))
                            text = u'KEYWORD CALLING RANKING (Top {rk})\n\n'.format(rk=param1)
                            rank = 0

                            for result in results:
                                rank += 1
                                text += u'No.{rk} - {kw} (ID: {id}, {ct} times.)\n'.format(rk=rank, 
                                                                          kw=result[kwdict_col.keyword].decode('utf8'), 
                                                                          id=result[kwdict_col.id],
                                                                          ct=result[kwdict_col.used_time])
                        except ValueError as err:
                            text = u'Invalid parameter. The 1st parameter of \'K\' function can be number only.\n\n'
                            text += u'Error message: {msg}'.format(msg=err.message)
                        
                        api_reply(rep, TextSendMessage(text=text))
                # - SPECIAL record
                elif cmd == 'P':
                        kwpct = kwd.row_count()

                        text = u'Data Recorded since booted up\n'
                        text += u'Boot up Time: {bt} (UTC+8)\n\n'.format(bt=boot_up)
                        text += u'Message Received: {recv}\n'.format(recv=rec['Msg_Received'])
                        text += u'Message Replied: {repl}\n\n'.format(repl=rec['Msg_Replied'])
                        text += u'System command called count (including failed): {t}\n{info}'.format(t=rec['JC_called'], info=cmd_called_time)
                        
                        text2 = u'Data Collected all the time\n\n'
                        text2 += u'Count of Keyword Pair: {ct}\n'.format(ct=kwpct)
                        text2 += u'Count of Reply: {crep}\n\n'.format(crep=kwd.used_time_sum())
                        user_list_top = kwd.user_sort_by_created_pair()[0]
                        text2 += u'The User Created The Most Keyword Pair:\n{name} ({num} Pairs - {pct:.2f}%)\n'.format(
                            name=api.get_profile(user_list_top[0]).display_name,
                            num=user_list_top[1],
                            pct=user_list_top[1] / float(kwpct) * 100)

                        first = kwd.most_used()
                        text2 += u'Most Popular Keyword ({t} Time(s)):\n'.format(t=first[0][kwdict_col.used_time])
                        for entry in first:
                            text2 += u'{kw} (ID: {id}, {c} Time(s))\n'.format(kw=entry[kwdict_col.keyword].decode('utf-8'), 
                                                                           c=entry[kwdict_col.used_time],
                                                                           id=entry[kwdict_col.id])

                        text2 += '\n'

                        last = kwd.least_used()
                        last_count = len(last)
                        limit = 10
                        text2 += u'Most Unpopular Keyword ({t} Time(s)):\n'.format(t=last[0][kwdict_col.used_time])
                        for entry in last:
                            text2 += u'{kw} (ID: {id}, {c} Time(s))\n'.format(kw=entry[kwdict_col.keyword].decode('utf-8'), 
                                                                           c=entry[kwdict_col.used_time],
                                                                           id=entry[kwdict_col.id])
                            
                            last_count -= 1
                            if len(last) - last_count >= limit:
                                text2 += '...({left} more)'.format(left=last_count)
                                break

                        api_reply(rep, [TextSendMessage(text=text), TextMessage(text=text2)])
                # GROUP ban basic (info)
                elif cmd == 'G':
                        if not isinstance(src, SourceUser):
                            gid = get_source_channel_id(src)

                            group_detail = gb.get_group_by_id(gid)
                            if group_detail is not None:
                                text = u'Chat Group ID: {id}\n'.format(id=group_detail[gb_col.groupId])
                                text += u'Silence: {sl}\n\n'.format(sl=group_detail[gb_col.silence])
                                text += u'Admin: {name}\n'.format(name=api.get_profile(group_detail[gb_col.admin]).display_name)
                                text += u'Admin User ID: {name}'.format(name=api.get_profile(group_detail[gb_col.admin]).user_id)
                            else:
                                text = u'Chat Group ID: {id}\n'.format(id=gid)
                                text += u'Silence: False'
                        else:
                            text = 'This function can be only execute in GROUP or ROOM.'
                        
                        api_reply(rep, TextSendMessage(text=text))
                # GROUP ban advance
                elif cmd == 'GA':
                        max_param_count = 6
                        paramI = split(param1, splitter, max_param_count)
                        param_count = len(paramI) - paramI.count(None)
                        param1, param2, param3, param4, param5, param6 = [paramI.pop(0) if len(paramI) > 0 else None for i in range(max_param_count)]
                        public_key = param1

                        error = 'No command fetched.\nWrong command, parameters or insufficient permission to use the function.'
                        illegal_type = 'This function can be used in 1v1 CHAT only. Permission key required. Please contact admin.'

                        perm = permission_level(public_key)
                        pert_dict = {3: 'Permission: Bot Administrator',
                                     2: 'Permission: Group Admin',
                                     1: 'Permission: Group Moderator',
                                     0: 'Permission: User'}
                        pert = pert_dict[perm]

                        if isinstance(src, SourceUser):
                            text = error

                            if perm >= 1 and param_count == 4:
                                cmd_dict = {'SF': True, 'ST': False}
                                status_silence = {True: 'disabled', False: 'enabled'}

                                if param2 in cmd_dict:
                                    settarget = cmd_dict[param2]

                                    if gb.set_silence(param3, str(settarget) , param4):
                                        text = 'Group auto reply function has been {res}.\n\n'.format(res=status_silence[settarget].upper())
                                        text += 'GID: {gid}'.format(gid=param3)
                                    else:
                                        text = 'Group auto reply setting not changed.\n\n'
                                        text += 'GID: {gid}'.format(gid=param3)
                                else:
                                    text = 'Invalid command: {cmd}. Recheck User Manual.'.format(cmd=param2)
                            elif perm >= 2 and param_count == 6:
                                cmd_dict = {'SA': gb.change_admin, 
                                            'SM1': gb.set_mod1,
                                            'SM2': gb.set_mod2,
                                            'SM3': gb.set_mod3}
                                pos_dict = {'SA': 'Administrator',
                                            'SM1': 'Moderator 1',
                                            'SM2': 'Moderator 2',
                                            'SM3': 'Moderator 3'}

                                gid = param3
                                uid = param4
                                pkey = param5
                                npkey = param6

                                try:
                                    if cmd_dict[param2](gid, uid, pkey, npkey):
                                        position = pos_dict[param2]

                                        text = u'Group administrator has been changed.\n'
                                        text += u'Group ID: {gid}\n\n'.format(gid=gid)
                                        text += u'New {pos} User ID: {uid}\n'.format(uid=uid, pos=position)
                                        text += u'New {pos} User Name: {unm}\n\n'.format(
                                            unm=api.get_profile(uid).display_name,
                                            pos=position)
                                        text += u'New {pos} Key: {npkey}\n'.format(npkey=npkey, pos=position)
                                        text += u'Please protect your key well!'
                                    else:
                                        text = '{pos} changing process failed.'
                                except KeyError as Ex:
                                    text = 'Invalid command: {cmd}. Recheck User Manual.'.format(cmd=param2)
                            elif perm >= 3 and (param_count == 2 or param_count == 5):
                                if param2 == 'C' and param_count == 2:
                                    if gb.create_ban():
                                        text = 'Group Ban table successfully created.'
                                    else:
                                        text = 'Group Ban table creating failed.'
                                elif param_count == 5:
                                    if param2 == 'N':
                                        if gb.new_data(param3, param4, param5):
                                            text = u'Group data registered.\n'
                                            text += u'Group ID: {gid}'.format(gid=param2)
                                            text += u'Admin ID: {uid}'.format(uid=param3)
                                            text += u'Admin Name: {name}'.format(gid=api.get_profile(param3).display_name)
                                        else:
                                            text = 'Group data register failed.'
                        else:
                            text = illegal_type

                        api_reply(rep, [TextSendMessage(text=pert), TextSendMessage(text=text)])
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

                    api_reply(rep, [TextSendMessage(text=source_type), TextSendMessage(text=text)])
                # SHA224 generator
                elif cmd == 'SHA':
                    if param1 != None:
                        text = hashlib.sha224(param1.encode('utf-8')).hexdigest()
                    else:
                        text = 'Illegal Parameter to generate SHA224 hash.'

                    api_reply(rep, TextSendMessage(text=text))
                # Look up vocabulary in OXFORD Dictionary
                elif cmd == 'O':
                        if oxford_disabled:
                            text = 'Dictionary look up function has disabled because of illegal Oxford API key or ID.'
                        else:
                            j = oxford_json(param1)

                            if type(j) is int:
                                code = j

                                text = 'Dictionary look up process returned status code: {status_code} ({explanation}).'.format(
                                    status_code=code,
                                    explanation=httplib.responses[code])
                            else:
                                text = 'Powered by Oxford Dictionary.\n\n'

                                lexents = j['results'][0]['lexicalEntries']
                                for lexent in lexents:
                                    text += '{text} ({lexCat})\n'.format(text=lexent['text'], lexCat=lexent['lexicalCategory'])
                                    
                                    sens = lexent['entries'][0]['senses']
                                    
                                    text += 'Definition: \n'
                                    for index, sen in enumerate(sens):
                                        for de in sen['definitions']:
                                            text += '{count}. {de}\n'.format(count=index+1, de=de)
                                            
                                    text += '\n'

                        api_reply(rep, TextSendMessage(text=text))
                # Leave group or room
                elif cmd == 'B':
                    cid = get_source_channel_id(src)

                    api_reply(rep, TextSendMessage(text='Channel ID: {cid}\nBot Contact Link: http://line.me/ti/p/@fcb0332q'.format(
                        cid=cid)))

                    if isinstance(src, SourceUser):
                        text = 'Unable to leave 1v1 chat.'
                        api_reply(rep, TextSendMessage(text=text))
                    else:
                        if isinstance(src, SourceRoom):
                            api.leave_room(cid)
                        elif isinstance(src, SourceGroup):
                            api.leave_group(cid)
                else:
                    cmd_called_time[cmd] -= 1
        else:
            reply_message_by_keyword(get_source_channel_id(src), rep, text, False)
    except exceptions.LineBotApiError as ex:
        text = u'Boot up time: {boot}\n\n'.format(boot=boot_up)
        text += u'Line Bot Api Error. Status code: {sc}\n\n'.format(sc=ex.status_code)
        for err in ex.error.details:
            text += u'Property: {prop}\nMessage: {msg}\n'.format(prop=err.property, msg=err.message)

        send_error_url_line(rep, text)
    except Exception as exc:
        text = u'Boot up time: {boot}\n\n'.format(boot=boot_up)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        text += u'Type: {type}\nMessage: {msg}\nLine {lineno}'.format(type=exc_type, lineno=exc_tb.tb_lineno, msg=exc.message)

        send_error_url_line(rep, text)
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

    if isinstance(event.source, SourceUser):
        results = kwd.get_reply(sticker_id, True)
        
        if results is not None:
            result = results[0]
            kwdata = 'Associated Keyword ID: {id}\n'.format(id=result[kwdict_col.id])
        else:
            kwdata = 'No associated keyword pair.\n'

        api_reply(
            rep,
            [TextSendMessage(text=kwdata + 'Package ID: {pck_id}\nSticker ID: {stk_id}'.format(
                pck_id=package_id, 
                stk_id=sticker_id)),
             TextSendMessage(text='Picture Location on Android(png):\nemulated\\0\\Android\\data\\jp.naver.line.android\\stickers\\{pck_id}\\{stk_id}'.format(
                pck_id=package_id, 
                stk_id=sticker_id)),
             TextSendMessage(text='Picture Location on Windows PC(png):\nC:\\Users\\USER_NAME\\AppData\\Local\\LINE\\Data\\Sticker\\{pck_id}\\{stk_id}'.format(
                pck_id=package_id, 
                stk_id=sticker_id)),
             TextSendMessage(text='Picture Location on Web(png):\n{stk_url}'.format(stk_url=sticker_png_url(sticker_id)))]
        )
    else:
        reply_message_by_keyword(get_source_channel_id(src), rep, sticker_id, True)


# Incomplete
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
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
        api_reply(event.reply_token, TextMessage(text='Group data registered. Type in \'JC G\' to get more details.'))
    if isinstance(event.source, SourceRoom):
        gb.new_data(event.source.room_id, MAIN_UID, 'RaenonX')
        api_reply(event.reply_token, TextMessage(text='Room data registered. Type in \'JC G\' to get more details.'))


# Encapsulated Functions
def split(text, splitter, size):
    list = []
  
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
            title='Introduction', text='Welcome to use the shadow of JELLYFISH!', 
            actions=[
                URITemplateAction(label=u'點此開啟使用說明', uri='https://github.com/RaenonX/LineBot/blob/master/README.md'),
                URITemplateAction(label=u'點此導向開發者LINE帳號', uri='http://line.me/ti/p/~chris80124')
            ])
    template_message = TemplateSendMessage(
        alt_text='Group / Room joining introduction', template=buttons_template)
    return template_message


def sticker_png_url(sticker_id):
    return kw_dict_mgr.sticker_png_url(sticker_id)


def get_source_channel_id(source_event):
    if isinstance(source_event, SourceGroup):
        id = source_event.group_id
    elif isinstance(source_event, SourceRoom):
        id = source_event.room_id
    elif isinstance(source_event, SourceUser):
        id = source_event.user_id
    else:
        id = None
       
    return id


def string_is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


def api_reply(reply_token, msg):
    rec['Msg_Replied'] += 1
    api.reply_message(reply_token, msg)


def reply_message_by_keyword(channel_id, token, keyword, is_sticker_kw):
        if gb.is_group_set_to_silence(channel_id):
            return

        res = kwd.get_reply(keyword, is_sticker_kw)
        if res is not None:
            result = res[0]
            reply = result[kwdict_col.reply].decode('utf-8')

            if result[kwdict_col.is_pic_reply]:
                api_reply(token, TemplateSendMessage(
                    alt_text='Picture / Sticker Reply.\nID: {id}'.format(id=result[kwdict_col.id]),
                    template=ButtonsTemplate(text=u'ID: {id}\nCreated by {creator}.'.format(creator=api.get_profile(result[kwdict_col.creator]).display_name,
                                                                                            id=result[kwdict_col.id]), 
                                             thumbnail_image_url=reply,
                                             actions=[
                                                 URITemplateAction(label=u'Original Picture', uri=reply)
                                             ])))
            else:
                api_reply(token, TextSendMessage(text=reply))


def rec_error(details):
    if details is not None:
        timestamp = str(int(time.time()))
        report_content['Error'][timestamp] = 'Error Occurred at {time}'.format(time=datetime.now() + timedelta(hours=8))
        report_content['Error'][timestamp] += '\n\n'
        report_content['Error'][timestamp] += details  
        return timestamp


def rec_query(full_query):
    timestamp = str(int(time.time()))
    report_content['FullQuery'][timestamp] = full_query
    return request.url_root + url_for('full_query', timestamp=timestamp)[1:]


def send_error_url_line(token, error_text):
    timestamp = rec_error(traceback.format_exc())
    err_detail = u'Detail URL: {url}'.format(url=request.url_root + url_for('get_error_message', timestamp=timestamp)[1:])
    print report_content['Error'][timestamp]
    api_reply(token, [TextSendMessage(text=error_text), TextSendMessage(text=err_detail)])


if __name__ == "__main__":
    # create tmp dir for download content
    make_static_tmp_dir()

    app.run(port=os.environ['PORT'], host='0.0.0.0')
