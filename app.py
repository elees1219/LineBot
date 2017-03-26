# -*- coding: utf-8 -*-

import errno
import os
import sys
import tempfile
import traceback
import hashlib 
import datetime

# Database import
from db import kw_dict_mgr, group_ban, kwdict_col, gb_col

from flask import Flask, request, abort

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
boot_up = datetime.datetime.now()
rec = {'JC_called': 0}
cmd_called_time = {'S': 0, 'A': 0, 'M': 0, 'D': 0, 'R': 0, 'Q': 0, 
                   'C': 0, 'I': 0, 'K': 0, 'P': 0, 'G': 0, 'GA': 0, 
                   'H': 0, 'SHA': 0}

# Database initializing
kwd = kw_dict_mgr("postgres", os.environ["DATABASE_URL"])
gb = group_ban("postgres", os.environ["DATABASE_URL"])

# get channel_secret and channel_access_token from your environment variable
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


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    rep = event.reply_token
    text = event.message.text
    splitter = '  '

    if len(text.split(splitter)) > 1 and text.startswith('JC'):
        try:
            head, oth = split(text, splitter, 2)

            split_count = {'S': 4, 'A': 4, 'M': 5, 'D': 3, 'R': 5, 'Q': 3, 
                           'C': 2, 'I': 3, 'K': 3, 'P': 2, 'G': 2, 'GA': 3, 
                           'H': 2, 'SHA': 3}

            if head == 'JC':
                rec['JC_called'] += 1

                prm_count = split_count[oth.split(splitter)[0]]
                params = split(text, splitter, prm_count)

                if prm_count != len(params) - params.count(None):
                    text = u'Lack of parameter(s). Please recheck your parameter(s) that correspond to the command.\n\n'
                    api.reply_message(rep, TextSendMessage(text=text))
                    return

                head, cmd, param1, param2, param3 = [params.pop(0) if len(params) > 0 else None for i in range(max(split_count.values()))]

                if cmd not in split_count:
                    text = u'Invalid Command: {cmd}. Please recheck the user manual.'.format(cmd=ex.message)
                    api.reply_message(rep, TextSendMessage(text=text))
                    return

                cmd_called_time[cmd] += 1
                
                # SQL Command
                if cmd == 'S':
                    if isinstance(event.source, SourceUser) and permission_level(param2) >= 3:
                        results = kwd.sql_cmd(param1)
                        if results is not None:
                            text = u'SQL command result({len}): \n'.format(len=len(results))
                            for result in results:
                                text += u'{result}\n'.format(result=result)
                                
                    else:
                        text = 'This is a restricted function.'

                    api.reply_message(rep, TextSendMessage(text=text))
                # ADD keyword
                elif cmd == 'A':
                    text = 'Unavailable to add keyword pair in GROUP or ROOM. Please go to 1v1 CHAT to execute this command.'

                    if isinstance(event.source, SourceUser):
                        uid = event.source.user_id
                        results = kwd.insert_keyword(param1, param2, uid)
                        text = u'Pair Added. Total: {len}\n'.format(len=len(results))
                        for result in results:
                            text += u'ID: {id}\n'.format(id=result[kwdict_col.id])
                            text += u'Keyword: {kw}\n'.format(kw=result[kwdict_col.keyword].decode('utf8'))
                            text += u'Reply: {rep}\n'.format(rep=result[kwdict_col.reply].decode('utf8'))

                    api.reply_message(rep, TextSendMessage(text=text))
                # ADD keyword(sys)
                elif cmd == 'M':
                    text = 'Restricted Function.'

                    if isinstance(event.source, SourceUser) and permission_level(param3) >= 2:
                        uid = event.source.user_id
                        results = kwd.insert_keyword_sys(param1, param2, uid)
                        text = u'System Pair Added. Total: {len}\n'.format(len=len(results))
                        for result in results:
                            text += u'ID: {id}\n'.format(id=result[kwdict_col.id])
                            text += u'Keyword: {kw}\n'.format(kw=result[kwdict_col.keyword].decode('utf8'))
                            text += u'Reply: {rep}\n'.format(rep=result[kwdict_col.reply].decode('utf8'))

                    api.reply_message(rep, TextSendMessage(text=text))
                # DELETE keyword
                elif cmd == 'D':
                    text = u'Specified keyword({kw}) to delete not exists.'.format(kw=param1)

                    if len(param1.split(splitter)) > 1:
                        extra_prm_count = 2
                        paramD = split(param1, splitter, extra_prm_count)
                        param1, param2 = [paramD.pop(0) if len(paramD) > 0 else None for i in range(extra_prm_count)]
                        if param1 != 'ID':
                            text = 'Incorrect 1st parameter to delete keyword pair. To use this function, 1st parameter needs to be \'ID\'.'
                            results = None
                        else:
                            results = kwd.delete_keyword_id(param2)   
                    else:
                        results = kwd.delete_keyword(param1)

                    if results is not None:
                        for result in results:
                            text = 'Pair below DELETED.\n'
                            text += u'ID: {id}\n'.format(id=result[kwdict_col.id])
                            text += u'Keyword: {kw}\n'.format(kw=result[kwdict_col.keyword].decode('utf8'))
                            text += u'Reply: {rep}\n\n'.format(rep=result[kwdict_col.reply].decode('utf8'))
                            profile = api.get_profile(result[kwdict_col.creator])
                            text += u'This pair is created by {name}.\n'.format(name=profile.display_name)

                    api.reply_message(rep, TextSendMessage(text=text))
                # DELETE keyword(sys)
                elif cmd == 'R':
                    text = 'Restricted Function.'

                    if isinstance(event.source, SourceUser) and permission_level(param2) >= 2:
                        text = u'Specified keyword({kw}) to delete not exists.'.format(kw=param1)
                        results = kwd.delete_keyword_sys(param1)

                        if results is not None:
                            for result in results:
                                text = 'System Pair below DELETED.\n'
                                text += u'ID: {id}\n'.format(id=result[kwdict_col.id])
                                text += u'Keyword: {kw}\n'.format(kw=result[kwdict_col.keyword].decode('utf8'))
                                text += u'Reply: {rep}\n'.format(rep=result[kwdict_col.reply].decode('utf8'))

                    api.reply_message(rep, TextSendMessage(text=text))
                # QUERY keyword
                elif cmd == 'Q':
                    text = u'Specified keyword({kw}) to query returned no result.'.format(kw=param1)
                    if len(param1.split(splitter)) > 1:
                        extra_prm_count = 2
                        paramQ = split(param1, splitter, extra_prm_count)
                        param1, param2 = [paramQ.pop(0) if len(paramQ) > 0 else None for i in range(extra_prm_count)]
                        try:
                            num1 = int(param2)
                            num2 = int(param1)

                            if num1 - num2 < 0:
                                results = None
                                text = '2nd parameter must bigger than 1st parameter.'
                            elif num1 - num2 < 15:
                                results = kwd.search_keyword_index(param1, param2)
                            else:
                                results = None
                                text = 'Maximum selecting range by ID is 15.'
                        except ValueError:
                            results = None
                            text = 'Illegal parameter. 2nd parameter and 3rd parameter can be numbers only.'
                        
                    else:
                        results = kwd.search_keyword(param1)

                    if results is not None:
                        text = u'Keyword found. Total: {len}. Listed below.\n'.format(len=len(results))
                        
                        for result in results:
                            text += u'ID: {id} - {kw} {od}{delete}{adm}\n'.format(
                                kw=result[kwdict_col.keyword].decode('utf8'),
                                od='(OVR)' if bool(result[kwdict_col.override]) == True else '',
                                delete='(DEL)' if bool(result[kwdict_col.deleted]) == True else '',
                                adm='(TOP)' if bool(result[kwdict_col.admin]) == True else '',
                                id=result[kwdict_col.id])

                    api.reply_message(rep, TextSendMessage(text=text))
                # CREATE kw_dict
                elif cmd == 'C':
                    text = 'Access denied. Insufficient permission.'

                    if permission_level(param2) >= 3:
                        text = 'Successfully Created.' if kwd.create_kwdict() == True else 'Creating failure.'

                    api.reply_message(rep, TextSendMessage(text=text))
                # INFO of keyword
                elif cmd == 'I':
                    text = u'Specified keyword({kw}) to get information returned no result.'.format(kw=param1)
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
                        if len(results) > 3:
                            text = 'Because the limit of the single search has reached, data will be display in basic form.\n'
                            text += 'To get more information, please input the ID of keyword.\n\n'
                            for result in results:
                                text += u'ID: {id} - {kw}→{rep} ({ct})\n'.format(
                                    id=result[kwdict_col.id],
                                    kw=result[kwdict_col.keyword].decode('utf8'),
                                    rep=result[kwdict_col.reply].decode('utf8'),
                                    ct=result[kwdict_col.used_time])
                        else:
                            text = ''
                            for result in results:
                                text += u'ID: {id}\n'.format(id=result[kwdict_col.id])
                                text += u'Keyword: {kw}\n'.format(kw=result[kwdict_col.keyword].decode('utf8'))
                                text += u'Reply: {rep}\n'.format(rep=result[kwdict_col.reply].decode('utf8'))
                                text += u'Deleted: {de}\n'.format(de=result[kwdict_col.deleted])
                                text += u'Override: {od}\n'.format(od=result[kwdict_col.override])
                                text += u'Admin Pair: {ap}\n'.format(ap=result[kwdict_col.admin])
                                text += u'Has been called {ut} time(s).\n'.format(ut=result[kwdict_col.used_time])
                                profile = api.get_profile(result[kwdict_col.creator])
                                text += u'Created by {name}.\n'.format(name=profile.display_name)

                    api.reply_message(rep, TextSendMessage(text=text))
                # RANKING
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
                    
                    api.reply_message(rep, TextSendMessage(text=text))
                # SPECIAL record
                elif cmd == 'P':
                    kwpct = kwd.row_count()

                    text = u'Boot up Time: {bt} (UTC)\n'.format(bt=boot_up)
                    text += u'Count of Keyword Pair: {ct}\n'.format(ct=kwpct)
                    text += u'Count of Reply: {crep}\n'.format(crep=kwd.used_time_sum())
                    user_list_top = kwd.user_sort_by_created_pair()[0]
                    text += u'Most Creative User:\n{name} ({num} Pairs - {pct:.2f}%)\n'.format(
                        name=api.get_profile(user_list_top[0]).display_name,
                        num=user_list_top[1],
                        pct=user_list_top[1] / float(kwpct) * 100)
                    all = kwd.order_by_usedtime_all()
                    first = all[0]
                    text += u'Most Popular Keyword:\n{kw} (ID: {id}, {c} Time(s))\n'.format(kw=first[kwdict_col.keyword].decode('utf-8'), 
                                                                                c=first[kwdict_col.used_time],
                                                                                id=first[kwdict_col.id])
                    last = all[-1]
                    text += u'Most Unpopular Keyword:\n{kw} (ID: {id}, {c} Time(s))\n\n'.format(kw=last[kwdict_col.keyword].decode('utf-8'), 
                                                                                c=last[kwdict_col.used_time],
                                                                                id=last[kwdict_col.id])
                    text += u'System command called time (including failed): {t}\n'.format(t= rec['JC_called'])
                    for cmd, time in cmd_called_time.iteritems():
                        text += u'Command \'{c}\' Called {t} Time(s).\n'.format(c=cmd, t=time)

                    api.reply_message(rep, TextSendMessage(text=text))
                # GROUP ban basic
                elif cmd == 'G':
                    if isinstance(event.source, SourceGroup):
                        group_detail = gb.get_group_by_id(event.source.group_id)
                        if group_detail is not None:
                            text = u'Group ID: {id}\n'.format(id=group_detail[gb_col.groupId])
                            text += u'Silence: {sl}\n\n'.format(sl=group_detail[gb_col.silence])
                            text += u'Admin: {name}\n'.format(name=api.get_profile(group_detail[gb_col.admin]).display_name)
                            text += u'Admin User ID: {name}'.format(name=api.get_profile(group_detail[gb_col.admin]).user_id)
                        else:
                            text = u'Group ID: {id}\n'.format(id=event.source.group_id)
                            text += u'Silence: False'
                    else:
                        text = 'This function can be only execute in GROUP.'
                    
                    api.reply_message(rep, TextSendMessage(text=text))
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

                    if isinstance(event.source, SourceUser):
                        text = error

                        if perm >= 1 and param_count == 4:
                            cmd_dict = {'ST': True, 'SF': False}
                            status_silence = {True: 'enabled', False: 'disabled'}

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
                                        unm=api.get_profile(uid).display_name.decode('utf-8'),
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
                                        text += u'Admin Name: {name}'.format(gid=api.get_profile(param3).display_name.decode('utf-8'))
                                    else:
                                        text = 'Group data register failed.'
                    else:
                        text = illegal_type

                    api.reply_message(rep, [TextSendMessage(text=pert), TextSendMessage(text=text)])
                # get CHAT id
                elif cmd == 'H':
                    if isinstance(event.source, SourceUser):
                        text = event.source.user_id
                        type = 'Type: User'
                    elif isinstance(event.source, SourceGroup):
                        text = event.source.group_id
                        type = 'Type: Group'
                    elif isinstance(event.source, SourceRoom):
                        text = event.source.room_id
                        type = 'Type: Room'
                    else:
                        text = 'Unknown chatting type.'

                    api.reply_message(rep, [TextSendMessage(text=type), TextSendMessage(text=text)])
                # SHA224 generator
                elif cmd == 'SHA':
                    api.reply_message(rep, TextSendMessage(text=hashlib.sha224(param1.encode('utf-8')).hexdigest()))
                else:
                    cmd_called_time[cmd] -= 1
        except exceptions.LineBotApiError as ex:
            text = u'Line Bot Api Error. Status code: {sc}\n\n'.format(sc=ex.status_code)
            for err in ex.error.details:
                text += u'Property: {prop}\nMessage: {msg}'.format(prop=err.property, msg=err.message)
            api.reply_message(rep, TextSendMessage(text=text))
        except Exception as exc:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            text = u'Type: {type}\nMessage: {msg}\nLine {lineno}'.format(type=exc_type, lineno=exc_tb.tb_lineno, msg=exc.message)
            api.reply_message(rep, TextSendMessage(text=text))
    else:
        res = kwd.get_reply(text)
        if res is not None:
            result = res[0]
            reply = result[kwdict_col.reply].decode('utf8')
            group = None
            if isinstance(event.source, SourceGroup):
                group = gb.get_group_by_id(event.source.group_id)
                if group is not None and group[gb_col.silence]:
                    api.reply_message(rep, TextSendMessage(text=reply))
            else:
                api.reply_message(rep, TextSendMessage(text=reply))


    return

    # MD5 generator

    if text == 'profile':
        if isinstance(event.source, SourceUser):
            profile = api.get_profile(event.source.user_id)
            api.reply_message(
                event.reply_token, [
                    TextSendMessage(text='Display name: ' + profile.display_name),
                    TextSendMessage(text='Status message: ' + profile.status_message),
                ]
            )
        else:
            api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't use profile API without user ID"))
    elif text == 'bye':
        if isinstance(event.source, SourceGroup):
            api.reply_message(
                event.reply_token, TextMessage(text='Leaving group'))
            api.leave_group(event.source.group_id)
        elif isinstance(event.source, SourceRoom):
            api.reply_message(
                event.reply_token, TextMessage(text='Leaving room'))
            api.leave_room(event.source.room_id)
        else:
            api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't leave from 1:1 chat"))
    elif text == 'confirm':
        confirm_template = ConfirmTemplate(text='Do it?', actions=[
            MessageTemplateAction(label='Yes', text='Yes!'),
            MessageTemplateAction(label='No', text='No!'),
        ])
        template_message = TemplateSendMessage(
            alt_text='Confirm alt text', template=confirm_template)
        api.reply_message(event.reply_token, template_message)
    elif text == 'buttons':
        buttons_template = ButtonsTemplate(
            title='My buttons sample', text='Hello, my buttons', actions=[
                URITemplateAction(
                    label='Go to line.me', uri='https://line.me'),
                PostbackTemplateAction(label='ping', data='ping'),
                PostbackTemplateAction(
                    label='ping with text', data='ping',
                    text='ping'),
                MessageTemplateAction(label='Translate Rice', text='米')
            ])
        template_message = TemplateSendMessage(
            alt_text='Buttons alt text', template=buttons_template)
        api.reply_message(event.reply_token, template_message)
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
        api.reply_message(event.reply_token, template_message)
    elif text == 'imagemap':
        pass
    else:
        api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text))


@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    return

    api.reply_message(
        event.reply_token,
        LocationSendMessage(
            title=event.message.title, address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        )
    )


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    package_id = event.message.package_id
    sticker_id = event.message.sticker_id

    return
    api.reply_message(
        event.reply_token,
        StickerSendMessage(package_id=2, sticker_id=144)
    )


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

    api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save content.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ])


@handler.add(FollowEvent)
def handle_follow(event):
    return

    api.reply_message(
        event.reply_token, TextSendMessage(text='Got follow event'))


@handler.add(UnfollowEvent)
def handle_unfollow():
    return

    app.logger.info("Got Unfollow event")


@handler.add(JoinEvent)
def handle_join(event):
    gb.new_data(event.source.groupId, 'Ud5a2b5bb5eca86342d3ed75d1d606e2c', 'RaenonX', 'RaenonX')
    api.reply_message(
        event.reply_token,
        TextSendMessage(text='Welcome to use the shadow of JELLYFISH!\n\n' + 
                             '======================================\n' +
                             'USAGE: type in \'使用說明-JC\'' +
                             '======================================\n' +
                             'To contact the developer, use the URL below http://line.me/ti/p/~chris80124 \n\n' + 
                             'HAVE A FUNNY EXPERIENCE USING THIS BOT!'))


@handler.add(LeaveEvent)
def handle_leave():
    return
    app.logger.info("Got leave event")


@handler.add(PostbackEvent)
def handle_postback(event):
    return
    if event.postback.data == 'ping':
        api.reply_message(
            event.reply_token, TextSendMessage(text='pong'))


@handler.add(BeaconEvent)
def handle_beacon(event):
    return
    api.reply_message(
        event.reply_token,
        TextSendMessage(text='Got beacon event. hwid=' + event.beacon.hwid))


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


if __name__ == "__main__":
    # create tmp dir for download content
    make_static_tmp_dir()

    app.run(port=os.environ['PORT'], host='0.0.0.0')
