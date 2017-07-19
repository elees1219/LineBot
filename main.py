# -*- coding: utf-8 -*-

import errno, os, sys
import validators
import time
from collections import defaultdict
from datetime import datetime, timedelta
from error import error
from flask import Flask, request, abort, url_for

# import some methods defined in app.py
from app import permission_level

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


class command(object):
    def __init__(self, kw_dict_mgr):
        self.kwd = kw_dict_mgr

    def S(self, src, params):
        """'S'QL Command"""
        key = params.pop(1)
        sql = params[1]

        if isinstance(src, SourceUser) and permission_level(key) >= 3:
            results = self.self.kwd.sql_cmd_only(sql)
            text = u'資料庫指令:\n{}\n\n'.format(sql)
            if results is not None and len(results) > 0:
                text += u'輸出結果(共{}筆):'.format(len(results))
                for result in results:
                    text += u'\n[{}]'.format(', '.join(str(s).decode('utf-8') for s in result))
            else:
                text += error.main.no_result()
        else:
            text = error.main.restricted(3)

        return text

    def A(self, src, params, pinned=False):
        """'A'DD Keyword Pair"""
        if params[4] is not None:
            action_kw = params[1]
            kw = params[2]
            action_rep = params[3]
            rep = params[4]
             
            if action_kw != 'STK':
                results = None
                text = error.main.incorrect_param(u'參數1', u'STK')
            elif not string_is_int(kw):
                results = None
                text = error.main.incorrect_param(u'參數2', u'整數數字')
            elif action_rep != 'PIC':
                results = None
                text =  error.main.incorrect_param(u'參數3', u'PIC')
            else:
                if string_is_int(rep):
                    rep = sticker_png_url(rep)
                    url_val_result = True
                else:
                    url_val_result = url_val_result = True if validators.url(rep) and urlparse(rep).scheme == 'https' else False

                if type(url_val_result) is bool and url_val_result:
                    results = self.kwd.insert_keyword(kw, rep, new_uid, pinned, True, True)
                else:
                    results = None
                    text = error.main.incorrect_param(u'參數4', u'HTTPS協定，並且是合法的網址。')
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
                    results = self.kwd.insert_keyword(kw, rep, new_uid, pinned, False, True)
                else:
                    results = None
                    text = error.main.incorrect_param(u'參數3', u'HTTPS協定，並且是合法的網址。')
            elif params[1] == 'STK':
                kw = params[2]

                if string_is_int(kw):
                    results = self.kwd.insert_keyword(kw, rep, new_uid, pinned, True, False)
                else:
                    results = None
                    text = error.main.incorrect_param(u'參數2', u'整數數字')
            else:
                text = error.main.unable_to_determine()
                results = None
        elif params[2] is not None:
            kw = params[1]
            rep = params[2]

            results = self.kwd.insert_keyword(kw, rep, new_uid, pinned, False, False)
        else:
            results = None
            text = error.main.lack_of_thing(u'參數')

        if results is not None:
            text = u'已新增回覆組。{}\n'.format(u'(置頂)' if pinned else '')
            for result in results:
                text += kw_dict_mgr.entry_basic_info(result)

        return text

    def M(self, src, params, pinned):
        """'M'AKE pinned Keyword Pair"""
        if pinned and permission_level(params.pop(1)) < 1:
            text = error.main.restricted(1)
        elif not is_valid_user_id(new_uid):
            text = error.main.unable_to_receive_user_id()
        else:
            text = self.A(src, params)

            return text
