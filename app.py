# -*- coding: utf-8 -*-

import errno
import os
import sys
import tempfile
import traceback
import md5

# Database import
from db import kw_dict_mgr, kwdict_col

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
admin = '37f9105623c89106783932dffac1ce11'

# Database initializing
db = kw_dict_mgr("postgres", os.environ["DATABASE_URL"])

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
            split_count = {'S': 4, 'A': 4, 'M': 5, 'D': 3, 'R': 5, 'Q': 3, 'C': 2, 'I': 3}

            if head == 'JC':
                params = split(oth, splitter, split_count[oth[0]] - 1)
                cmd, param1, param2, param3 = [params.pop(0) if len(params) > 0 else None for i in range(4)]

                # SQL Command
                if cmd == 'S':
                    if isinstance(event.source, SourceUser) and md5.new(param2).hexdigest() == admin:
                        results = db.sql_cmd(param1.decode('utf8'))
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
                        results = db.insert_keyword(param1, param2, uid)
                        text = u'Pair Added. Total: {len}\n'.format(len=len(results))
                        for result in results:
                            text += u'ID: {id}\n'.format(id=result[kwdict_col.id])
                            text += u'Keyword: {kw}\n'.format(kw=result[kwdict_col.keyword].decode('utf8'))
                            text += u'Reply: {rep}\n'.format(rep=result[kwdict_col.reply].decode('utf8'))

                    api.reply_message(rep, TextSendMessage(text=text))
                # ADD keyword(sys)
                elif cmd == 'M':
                    text = 'Restricted Function.'

                    if isinstance(event.source, SourceUser) and md5.new(param3).hexdigest() == admin:
                        uid = event.source.user_id
                        results = db.insert_keyword_sys(param1, param2, uid)
                        text = u'System Pair Added. Total: {len}\n'.format(len=len(results))
                        for result in results:
                            text += u'ID: {id}\n'.format(id=result[kwdict_col.id])
                            text += u'Keyword: {kw}\n'.format(kw=result[kwdict_col.keyword].decode('utf8'))
                            text += u'Reply: {rep}\n'.format(rep=result[kwdict_col.reply].decode('utf8'))

                    api.reply_message(rep, TextSendMessage(text=text))
                # DELETE keyword
                elif cmd == 'D':
                    text = u'Specified keyword({kw}) to delete not exists.'.format(kw=param1.decode('utf8'))
                    results = db.delete_keyword(param1)

                    if results is not None:
                        for result in results:
                            text = 'Pair below DELETED.\n'
                            text += u'ID: {id}\n'.format(id=result[kwdict_col.id])
                            text += u'Keyword: {kw}\n'.format(kw=result[kwdict_col.keyword].decode('utf8'))
                            text += u'Reply: {rep}\n'.format(rep=result[kwdict_col.reply].decode('utf8'))

                    api.reply_message(rep, TextSendMessage(text=text))
                # DELETE keyword(sys)
                elif cmd == 'R':
                    text = 'Restricted Function.'

                    if isinstance(event.source, SourceUser) and md5.new(param3).hexdigest() == admin:
                        text = u'Specified keyword({kw}) to delete not exists.'.format(kw=param1.decode('utf8'))
                        results = db.delete_keyword_sys(param1)

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
                        paramQ = split(param1, splitter, 2)
                        param1, param2 = [paramQ.pop(0) if len(paramQ) > 0 else None for i in range(2)]
                        if int(param2) - int(param1) <= 15:
                            results = db.search_keyword_index(param1, param2)
                        else:
                            results = None
                            text = 'Maximum selecting range by ID is 15.'
                    else:
                        results = db.search_keyword(keyword=param1)
                        

                    if results is not None:
                        text = u'Keyword found. Total: {len}. Listed below.\n'.format(len=len(results))
                        text += str(results)
                        
                        for result in results:
                            break
                            text += u'ID: {id} - {kw} {od} {delete} \n'.format(
                                kw=result[kwdict_col.keyword],
                                od='(Overrided)' if bool(result[kwdict_col.override]) == True else '',
                                delete='(Deleted)' if bool(result[kwdict_col.deleted]) == True else '',
                                id=result[kwdict_col.id])

                    api.reply_message(rep, TextSendMessage(text=text))
                # CREATE kw_dict
                elif cmd == 'C':
                    api.reply_message(rep, TextSendMessage(text=db.create_kwdict()))
                # INFO of keyword
                elif cmd == 'I':
                    results = db.get_info(param1)

                    if results is None:
                        text = u'Specified keyword: {kw} not exists.'.format(kw=param1.decode('utf8'))
                        api.reply_message(rep, TextSendMessage(text=text))
                    else:
                        text = ''
                        for result in results:
                            text += u'ID: {id}\n'.format(id=result[kwdict_col.id])
                            text += u'Keyword: {kw}\n'.format(kw=result[kwdict_col.keyword].decode('utf8'))
                            text += u'Reply: {rep}\n'.format(rep=result[kwdict_col.reply].decode('utf8'))
                            text += u'Has been called {ut} time(s).\n'.format(ut=result[kwdict_col.used_time])
                            profile = api.get_profile(result[kwdict_col.creator].decode('utf8'))
                            text += u'Created by {name}.\n'.format(name=profile.display_name.decode('utf8'))
                        api.reply_message(rep, TextSendMessage(text=text))
        except KeyError as ex:
            text = u'Invalid Command: {cmd}. Please recheck the user manual.'.format(cmd=ex.message)
            api.reply_message(rep, TextSendMessage(text=text))
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
        res = db.get_reply(text)
        if res is not None:
            result = res[0]
            api.reply_message(rep, TextSendMessage(text=result[kwdict_col.reply].decode('utf8')))

    return

    # MD5 generator
    # calculator

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


# Other Message Type
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
    api.reply_message(
        event.reply_token,
        TextSendMessage(text='Welcome to use the shadow of JELLYFISH!\n\n' + 
                             '======================================\n'+
                             'USAGE: \n'+
                             '\'ADD|(Keyword)|(Reply)\' to add new word pair.\n' + 
                             '\'DEL|(Keyword)|\' to delete the specified word pair.\n' + 
                             '======================================\n'+
                             'Other function such as locking specified user\'s keyword, or gaming... etc. ' + 
                             'has not yet developed. The only function is to reply something with keyword sent.\n' + 
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
    for i in range(size - 1):
        list.append(text[0:text.index(splitter)])
        text = text[text.index(splitter)+len(splitter):]
  
    list.append(text)
    return list


if __name__ == "__main__":
    # create tmp dir for download content
    make_static_tmp_dir()

    app.run(port=os.environ['PORT'], host='0.0.0.0')
