# -*- coding: utf-8 -*-

import errno, os, sys
import validators
import time
from collections import defaultdict
from datetime import datetime, timedelta
from error import error
from flask import Flask, request, abort, url_for
from cgi import escape

# import modules from main.py
import main

# import for 'SHA'
import hashlib 

# import for Oxford Dictionary
import httplib
import requests
import json

# Database import
from db import kw_dict_mgr, kwdict_col, group_ban, gb_col, message_tracker, msg_track_col

# tool import
from tool import mff, random_gen

# import from LINE MAPI
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

# Databases initialization
kwd = kw_dict_mgr("postgres", os.environ["DATABASE_URL"])
gb = group_ban("postgres", os.environ["DATABASE_URL"])
msg_track = message_tracker("postgres", os.environ["DATABASE_URL"])

# Main initialization
app = Flask(__name__)
boot_up = datetime.now() + timedelta(hours=8)

rec = {'JC_called': 0, 'MFF_called': 0, 
       'last_stk': defaultdict(str), 
       'Silence': False, 'Intercept': True, 
       'webpage': 0}
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
            'P': command(0, 1, False), 
            'G': command(0, 1, False), 
            'GA': command(1, 5, True), 
            'H': command(0, 1, False), 
            'SHA': command(1, 1, False), 
            'O': command(1, 1, False), 
            'B': command(0, 0, False), 
            'RD': command(1, 2, False),
            'STK': command(0, 0, False)}

# Line Bot Environment initialization
MAIN_UID_OLD = 'Ud5a2b5bb5eca86342d3ed75d1d606e2c'
MAIN_UID = 'U089d534654e2c5774624e8d8c813000e'
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

# Oxford Dictionary Environment initialization
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
    content = 'Boot up at {}\n\nError list:\n'.format(boot_up)
    content += '\n'.join([html_hyperlink(timestamp, request.url_root + url_for('get_error_message', timestamp=timestamp)[1:]) for timestamp in report_content['Error'].keys()])
        
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
    return '<a href=\"{}\">{}</a>'.format(link, content)

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    command_executor = main.command(kwd, gb, msg_track)

    token = event.reply_token
    text = event.message.text
    src = event.source
    splitter = '  '
    splitter_mff = '\n'
    
    msg_track.log_message_activity(get_source_channel_id(src), 1)

    if text == administrator:
        rec['Silence'] = not rec['Silence']
        api.reply_message(token, TextSendMessage(text='Bot set to {mute}.'.format(mute='Silent' if rec['Silence'] else 'Active')))
        return
    elif rec['Silence']:
        return

    if text == '561563ed706e6f696abbe050ad79cf334b9262da6f83bc1dcf7328f2':
        rec['Intercept'] = not rec['Intercept']
        api.reply_message(token, TextSendMessage(text='Bot {}.'.format(
            'start to intercept messages' if rec['Intercept'] else 'stop intercepting messages')))
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
                    api_reply(token, TextSendMessage(text=text), src)
                    return

                max_prm = cmd_dict[cmd].split_max
                min_prm = cmd_dict[cmd].split_min
                params = split(oth, splitter, max_prm)

                if min_prm > len(params) - params.count(None):
                    text = error.main.lack_of_thing(u'參數')
                    api_reply(token, TextSendMessage(text=text), src)
                    return

                params.insert(0, None)
                cmd_dict[cmd].count += 1
                
                # SQL Command
                if cmd == 'S':
                    text = command_executor.S(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                # ADD keyword & ADD top keyword
                elif cmd == 'A' or cmd == 'M':
                    if cmd_dict[cmd].non_user_permission_required:
                        text = command_executor.M(src, params, True)
                    else:
                        text = command_executor.A(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                # DELETE keyword & DELETE top keyword
                elif cmd == 'D' or cmd == 'R':
                    if cmd_dict[cmd].non_user_permission_required:
                        text = command_executor.R(src, params, True)
                    else:
                        text = command_executor.D(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                # QUERY keyword
                elif cmd == 'Q':
                    text = command_executor.Q(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                # INFO of keyword
                elif cmd == 'I':
                    text = command_executor.I(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                # RANKING
                elif cmd == 'K':
                    text = command_executor.K(src, params)
                    
                    api_reply(token, TextSendMessage(text=text), src)
                # SPECIAL record
                elif cmd == 'P':
                    text = command_executor.P(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                # GROUP ban basic (info)
                elif cmd == 'G':
                    text = command_executor.G(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                # GROUP ban advance
                elif cmd == 'GA':
                    text = command_executor.GA(src, params)

                    api_reply(token, [TextSendMessage(text=pert), TextSendMessage(text=text)], src)
                # get CHAT id
                elif cmd == 'H':
                    text = command_executor.H(src, params)

                    api_reply(token, [TextSendMessage(text=source_type), TextSendMessage(text=text)], src)
                # SHA224 generator
                elif cmd == 'SHA':
                    text = command_executor.SHA(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                # Look up vocabulary in OXFORD Dictionary
                elif cmd == 'O':
                    text = command_executor.O(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                # Leave group or room
                elif cmd == 'B':
                    cid = get_source_channel_id(src)

                    if isinstance(src, SourceUser):
                        text = 'Unable to leave 1v1 chat.'
                        api_reply(token, TextSendMessage(text=text), src)
                    else:
                        api_reply(token, TextSendMessage(text='Channel ID: {cid}\nBot Contact Link: http://line.me/ti/p/@fcb0332q'.format(cid=cid)), src)

                        if isinstance(src, SourceRoom):
                            api.leave_room(cid)
                        elif isinstance(src, SourceGroup):
                            api.leave_group(cid)
                # RANDOM draw
                elif cmd == 'RD':
                    text = command_executor.RD(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                # last STICKER message
                elif cmd == 'STK':
                    text = command_executor.STK(src, params)

                    api_reply(token, TextSendMessage(text=text), src)
                else:
                    cmd_dict[cmd].count -= 1
        elif len(text.split(splitter_mff)) >= 2 and text.startswith('MFF'):
            rec['MFF_called'] += 1
            data = split(text, splitter_mff, 2)

            if data[1].upper().startswith('HELP'):
                api_reply(token, [TextSendMessage(text=mff.mff_dmg_calc.help_code()),
                                  TextSendMessage(text=u'下則訊息是訊息範本，您可以直接將其複製，更改其內容，然後使用。或是遵照以下格式輸入資料。\n\n{代碼(參見上方)} {參數}(%)\n\n例如:\nMFF\nSKC 100%\n魔力 1090%\n魔力 10.9\n\n欲察看更多範例，請前往 https://sites.google.com/view/jellybot/mff傷害計算'),
                                  TextSendMessage(text=mff.mff_dmg_calc.help_sample())], src)
            else:
                job = mff.mff_dmg_calc.text_job_parser(data[1])

                dmg_calc_dict = [[u'破防前非爆擊(弱點屬性)', mff.mff_dmg_calc.dmg_weak(job)],
                                 [u'破防前爆擊(弱點屬性)', mff.mff_dmg_calc.dmg_crt_weak(job)],
                                 [u'已破防非爆擊(弱點屬性)', mff.mff_dmg_calc.dmg_break_weak(job)],
                                 [u'已破防爆擊(弱點屬性)', mff.mff_dmg_calc.dmg_break_crt_weak(job)],
                                 [u'破防前非爆擊(非弱點屬性)', mff.mff_dmg_calc.dmg(job)],
                                 [u'破防前爆擊(非弱點屬性)', mff.mff_dmg_calc.dmg_crt(job)],
                                 [u'已破防非爆擊(非弱點屬性)', mff.mff_dmg_calc.dmg_break(job)],
                                 [u'已破防爆擊(非弱點屬性)', mff.mff_dmg_calc.dmg_break_crt(job)]]

                text = u'傷害表:'
                for title, value in dmg_calc_dict:
                    text += u'\n\n'
                    text += u'{}\n首發: {:.0f}\n連發: {:.0f}\n累積傷害(依次): {}'.format(title,
                                                                                        value['first'],
                                                                                        value['continual'],
                                                                                        u', '.join('{:.0f}'.format(x) for x in value['list_of_sum']))
                
                api_reply(token, TextSendMessage(text=text), src)
        else:
            replied = reply_message_by_keyword(get_source_channel_id(src), token, text, False, src)

            if text.startswith('JC') and ' ' in text and not replied:
                text = error.main.insufficient_space_for_command();
                api_reply(token, TextSendMessage(text=text), src)
                return
    except exceptions.LineBotApiError as ex:
        text = u'Boot up time: {boot}\n\n'.format(boot=boot_up)
        text += u'Line Bot Api Error. Status code: {sc}\n\n'.format(sc=ex.status_code)
        for err in ex.error.details:
            text += u'Property: {prop}\nMessage: {msg}\n'.format(prop=err.property, msg=err.message.decode("utf-8"))

        send_error_url_line(token, text, get_source_channel_id(src))
    except Exception as exc:
        text = u'Boot up time: {boot}\n\n'.format(boot=boot_up)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        text += u'Type: {type}\nMessage: {msg}\nLine {lineno}'.format(type=exc_type, lineno=exc_tb.tb_lineno, msg=exc.message.decode("utf-8"))

        send_error_url_line(token, text, get_source_channel_id(src))
    return

    if text == 'confirm':
        confirm_template = ConfirmTemplate(text='Do it?', actions=[
            MessageTemplateAction(label='Yes', text='Yes!'),
            MessageTemplateAction(label='No', text='No!'),
        ])
        template_message = TemplateSendMessage(
            alt_text='Confirm alt text', template=confirm_template)
        api_reply(event.reply_token, template_message, src)
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
        api_reply(event.reply_token, template_message, src)


# Incomplete
@handler.add(PostbackEvent)
def handle_postback(event):
    return
    if event.postback.data == 'ping':
        api_reply(
            event.reply_token, TextSendMessage(text='pong'), event.source)


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    package_id = event.message.package_id
    sticker_id = event.message.sticker_id
    rep = event.reply_token
    src = event.source
    cid = get_source_channel_id(src)

    rec['last_stk'][cid] = sticker_id
    msg_track.log_message_activity(cid, 3)

    if isinstance(event.source, SourceUser):
        results = kwd.get_reply(sticker_id, True)
        
        if results is not None:
            kwdata = u'相關回覆組ID: {id}。\n'.format(id=u', '.join([unicode(result[kwdict_col.id]) for result in results]))
        else:
            kwdata = u'無相關回覆組ID。\n'

        api_reply(
            rep,
            [TextSendMessage(text=kwdata + u'貼圖圖包ID: {}\n貼圖圖片ID: {}'.format(package_id, sticker_id)),
             TextSendMessage(text=u'圖片路徑(Android):\nemulated\\0\\Android\\data\\jp.naver.line.android\\stickers\\{}\\{}'.format(package_id, sticker_id)),
             TextSendMessage(text=u'圖片路徑(Windows):\nC:\\Users\\USER_NAME\\AppData\\Local\\LINE\\Data\\Sticker\\{}\\{}'.format(package_id, sticker_id)),
             TextSendMessage(text=u'圖片路徑(網路):\n{}'.format(sticker_png_url(sticker_id)))],
            src
        )
    else:
        reply_message_by_keyword(cid, rep, sticker_id, True, src)


# Incomplete
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    msg_track.log_message_activity(get_source_channel_id(event.source), 1)
    return

    api_reply(
        event.reply_token,
        LocationSendMessage(
            title=event.message.title, address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        ),
        event.source
    )


# Incomplete
@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
    msg_track.log_message_activity(get_source_channel_id(event.source), 1)
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
        ], event.source)


@handler.add(FollowEvent)
def handle_follow(event):
    api_reply(event.reply_token, introduction_template(), event.source)

# Incomplete
@handler.add(UnfollowEvent)
def handle_unfollow():
    return

    app.logger.info("Got Unfollow event")


@handler.add(JoinEvent)
def handle_join(event):
    src = event.source
    cid = get_source_channel_id(src)

    if not isinstance(event.source, SourceUser):
        added = gb.new_data(cid, MAIN_UID, 'RaenonX')
        msg_track.new_data(cid)

        api_reply(event.reply_token, 
                  [TextMessage(text='Channel data registering {}. Type in \'JC  G\' to get more details.'.format('succeed' if added else 'failed')),
                   introduction_template()], 
                   cid)


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
            title=u'機器人簡介', text='歡迎使用小水母！', 
            actions=[
                URITemplateAction(label=u'點此開啟使用說明', uri='https://sites.google.com/view/jellybot'),
                URITemplateAction(label=u'點此導向開發者LINE帳號', uri='http://line.me/ti/p/~chris80124')
            ])
    template_message = TemplateSendMessage(
        alt_text=u'機器人簡介', template=buttons_template)
    return template_message


def sticker_png_url(sticker_id):
    return kw_dict_mgr.sticker_png_url(sticker_id)


def get_source_channel_id(source_event):
    return source_event.sender_id

def get_source_user_id(source_event):
    return source_event.user_id


def is_valid_user_id(uid):
    return uid is not None and len(uid) == 33 and uid.startswith('U')

def is_valid_room_group_id(uid):
    return uid is not None and len(uid) == 33 and (uid.startswith('C') or uid.startswith('R'))


def string_is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


def api_reply(reply_token, msgs, src):
    if isinstance(msgs, TemplateSendMessage):
        msg_track.log_message_activity(get_source_channel_id(src), 6)
    elif isinstance(msgs, TextSendMessage):
        msg_track.log_message_activity(get_source_channel_id(src), 5)

    if not rec['Silence']:
        if not isinstance(msgs, (list, tuple)):
            msgs = [msgs]

        for msg in msgs:
            if isinstance(msg, TextSendMessage) and len(msg.text) > 2000:
                api.reply_message(reply_token, 
                                  TextSendMessage(
                                      text=error.main.text_length_too_long(rec_text(msgs))))
                return

        api.reply_message(reply_token, msgs)
    else:
        print '=================================================================='
        print 'Bot set to silence. Expected message to reply will display below: '
        print msgs
        print '=================================================================='


def intercept_text(event):
    user_id = get_source_user_id(event.source)
    user_profile = profile(user_id)

    print '==========================================='
    print 'From Channel ID \'{}\''.format(get_source_channel_id(event.source))
    print 'From User ID \'{}\' ({})'.format(user_id, user_profile.display_name.encode('utf-8') if user_profile is not None else 'unknown')
    print 'Message \'{}\''.format(event.message.text.encode('utf-8'))
    print '==========================================='


def reply_message_by_keyword(channel_id, token, keyword, is_sticker_kw, src):
        if gb.is_group_set_to_silence(channel_id):
            return False

        res = kwd.get_reply(keyword, is_sticker_kw)
        if res is not None:
            msg_track.log_message_activity(get_source_channel_id(src), 4 if is_sticker_kw else 2)
            result = res[0]
            reply = result[kwdict_col.reply].decode('utf-8')

            if result[kwdict_col.is_pic_reply]:
                line_profile = profile(result[kwdict_col.creator])

                api_reply(token, TemplateSendMessage(
                    alt_text='Picture / Sticker Reply.\nID: {id}'.format(id=result[kwdict_col.id]),
                    template=ButtonsTemplate(text=u'ID: {id}\nCreated by {creator}.'.format(
                        creator=u'(LINE account data not found)' if line_profile is None else line_profile.display_name,
                        id=result[kwdict_col.id]), 
                                             thumbnail_image_url=reply,
                                             actions=[
                                                 URITemplateAction(label=u'Original Picture', uri=reply)
                                             ])), src)
                return True
            else:
                api_reply(token, 
                          TextSendMessage(text=u'{rep}{id}'.format(rep=reply,
                                                                   id='' if not is_sticker_kw else '\n\nID: {id}'.format(id=result[kwdict_col.id]))),
                          src)
                return True

        return False


def rec_error(details, channel_id):
    if details is not None:
        timestamp = str(int(time.time()))
        report_content['Error'][timestamp] = 'Error Occurred at {time}\n'.format(time=datetime.now() + timedelta(hours=8))
        report_content['Error'][timestamp] = 'At channel ID: {cid}'.format(cid=channel_id)
        report_content['Error'][timestamp] += '\n\n'
        report_content['Error'][timestamp] += details  
        return timestamp


def rec_query(full_query):
    timestamp = str(int(time.time()))
    report_content['FullQuery'][timestamp] = full_query
    return request.url_root + url_for('full_query', timestamp=timestamp)[1:]


def rec_info(full_info):
    timestamp = str(int(time.time()))
    report_content['FullInfo'][timestamp] = full_info
    
    print report_content['FullInfo']

    return request.url_root + url_for('full_info', timestamp=timestamp)[1:]


def rec_text(textmsg_list):
    if not isinstance(textmsg_list, (list, tuple)):
        textmsg_list = [textmsg_list]

    timestamp = str(int(time.time()))
    report_content['Text'][timestamp] = ''
    for index, txt in enumerate(textmsg_list, start=1):
        report_content['Text'][timestamp] += 'Message {index}\n'.format(index=index)
        report_content['Text'][timestamp] += txt.text
        report_content['Text'][timestamp] += '\n===============================\n'
    return request.url_root + url_for('full_content', timestamp=timestamp)[1:]



def send_error_url_line(token, error_text, channel_id):
    timestamp = rec_error(traceback.format_exc(), channel_id)
    err_detail = u'詳細錯誤URL: {url}\n錯誤清單: {url_full}'.format(
        url=request.url_root + url_for('get_error_message', timestamp=timestamp)[1:],
        url_full=request.url_root + url_for('get_error_list')[1:])
    print report_content['Error'][timestamp]
    api_reply(token, [TextSendMessage(text=error_text), TextSendMessage(text=err_detail)], channel_id)


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
