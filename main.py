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

    def S(self, params_array):
        """'S'QL Command"""
        key = params_array.pop(1)
        sql = params_array[1]

        if isinstance(src, SourceUser) and permission_level(key) >= 3:
            results = self.kwd.sql_cmd_only(sql)
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
