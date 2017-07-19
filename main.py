# -*- coding: utf-8 -*-

import errno, os, sys
import validators
import time
from collections import defaultdict
from datetime import datetime, timedelta
from error import error
from flask import Flask, request, abort, url_for

# import some methods defined in app.py
from app import *

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
    def __init__(self, kw_dict_mgr, group_ban, msg_track):
        self.kwd = kw_dict_mgr
        self.gb = group_ban
        self.msg_track = msg_track

    def S(self, src, params):
        key = params.pop(1)
        sql = params[1]

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

    def A(self, src, params, pinned=False):
        new_uid = get_source_user_id(src)

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
        if pinned and permission_level(params.pop(1)) < 1:
            text = error.main.restricted(1)
        elif not is_valid_user_id(new_uid):
            text = error.main.unable_to_receive_user_id()
        else:
            text = A(src, params)

        return text

    def D(self, src, params, pinned=False):
        deletor_uid = src.user_id
        if pinned and permission_level(paramA.pop(1)) < 2:
            text = error.main.restricted(2)
        elif not is_valid_user_id(deletor_uid):
            text = error.main.unable_to_receive_user_id()
        else:
            if params[2] is None:
                kw = params[1]

                results = self.kwd.delete_keyword(kw, deletor_uid, pinned)
            else:
                action = params[1]

                if action == 'ID':
                    pair_id = params[2]

                    if string_is_int(pair_id):
                        results = self.kwd.delete_keyword_id(pair_id, deletor_uid, pinned)
                    else:
                        results = None
                        text = error.main.incorrect_param(u'參數2', u'整數數字')
                else:
                    results = None
                    text = error.main.incorrect_param(u'參數1', u'ID')

        if results is not None and len(results) > 0:
            for result in results:
                line_profile = profile(result[self.kwdict_col.creator])

                text = u'已刪除回覆組。{}\n'.format(u'(置頂)' if pinned else '')
                text += kw_dict_mgr.entry_basic_info(result)
                text += u'\n此回覆組由 {} 製作。'.format(
                    '(LINE account data not found)' if line_profile is None else line_profile.display_name)
        else:
            if string_is_int(kw):
                text = error.main.miscellaneous(u'偵測到參數1是整數。若欲使用ID作為刪除根據，請參閱小水母使用說明。')
            else:
                text = error.main.pair_not_exist_or_insuffieicnt_permission()

        return text

    def R(self, src, params, pinned):
        if pinned and permission_level(params.pop(1)) < 1:
            text = error.main.restricted(2)
        elif not is_valid_user_id(new_uid):
            text = error.main.unable_to_receive_user_id()
        else:
            text = D(src, params)

        return text

    def Q(self, src, params):
        if params[2] is not None:
            si = params[1]
            ei = params[2]
            text = u'搜尋範圍: 【回覆組ID】介於【{}】和【{}】之間的回覆組。\n'.format(si, ei)

            try:
                begin_index = int(si)
                end_index = int(ei)

                if end_index - begin_index < 0:
                    results = None
                    text += error.main.incorrect_param(u'參數2', u'大於參數1的數字')
                else:
                    results = self.kwd.search_keyword_index(begin_index, end_index)
            except ValueError:
                results = None
                text += error.main.incorrect_param(u'參數1和參數2', u'整數數字')
        else:
            kw = params[1]
            text = u'搜尋範圍: 【關鍵字】或【回覆】包含【{}】的回覆組。\n'.format(kw)

            results = self.kwd.search_keyword(kw)

        if results is not None:
            q_list = kw_dict_mgr.list_keyword(results)
            text = q_list['limited']
            text += '\n\n完整搜尋結果顯示: {}'.format(rec_query(q_list['full']))
        else:
            if params[2] is not None:
                text = u'找不到和指定的ID範圍({}~{})有關的結果。'.format(si, ei)
            else:
                text = u'找不到和指定的關鍵字({})有關的結果。'.format(kw)

        return text

    def I(self, src, params):
        if params[2] is not None:
            action = params[1]
            pair_id = params[2]
            text = u'搜尋條件: 【回覆組ID】為【{}】的回覆組。\n'.format(pair_id)

            if action != 'ID':
                text += error.main.invalid_thing_with_correct_format(u'參數1', u'ID', action)
                results = None
            else:
                if string_is_int(pair_id):
                    results = self.kwd.get_info_id(pair_id)   
                else:
                    results = None
                    text += error.main.invalid_thing_with_correct_format(u'參數2', u'正整數', pair_id)
        else:
            kw = params[1]
            text = u'搜尋條件: 【關鍵字】或【回覆】為【{}】的回覆組。\n'.format(kw)

            results = self.kwd.get_info(kw)

        if results is not None:
            i_object = kw_dict_mgr.list_keyword_info(self.kwd, api, results)
            text += i_object['limited']
            text += u'\n\n完整資訊URL: {}'.format(rec_info(i_object['full']))
        else:
            text = error.main.miscellaneous(u'資料查詢主體為空。')

        return text

    def K(self, src, params):
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
                text = kw_dict_mgr.list_user_created_ranking(api, self.kwd.user_created_rank(limit))
            elif ranking_type == 'KW':
                text = kw_dict_mgr.list_keyword_ranking(self.kwd.order_by_usedrank(limit))
            else:
                text = 'Parameter 1 must be \'USER\'(to look up the ranking of pair created group by user) or \'KW\' (to look up the ranking of pair\'s used time)'
                Valid = False

            if Valid:
                text += '\n\nFull Ranking(user created) URL: {url_u}\nFull Ranking(keyword used) URL: {url_k}'.format(
                    url_u=request.url_root + url_for('full_ranking', type='user')[1:],
                    url_k=request.url_root + url_for('full_ranking', type='used')[1:])

        return text

    def P(self, src, params):
        if params[1] is not None:
            category = params[1]

            if category == 'GRP':
                limit = 5

                sum_data = self.msg_track.count_sum()
                tracking_data = message_tracker.entry_detail_list(msg_track.order_by_recorded_msg_count(), limit, gb)

                text = u'【訊息流量統計】'
                text += u'\n收到(無對應回覆組): {}則文字訊息 | {}則貼圖訊息'.format(sum_data['text_msg'], sum_data['stk_msg'])
                text += u'\n收到(有對應回覆組): {}則文字訊息 | {}則貼圖訊息'.format(sum_data['text_msg_trig'], sum_data['stk_msg_trig'])
                text += u'\n回覆: {}則文字訊息 | {}則貼圖訊息'.format(sum_data['text_rep'], sum_data['stk_rep'])

                text += u'\n\n【群組訊息統計資料 - 前{}名】\n'.format(limit)
                text += tracking_data['limited']
                text += u'\n\n完整資訊URL: {}'.format(rec_info(tracking_data['full']))
            elif category == 'KW':
                kwpct = self.kwd.row_count()

                user_list_top = self.kwd.user_sort_by_created_pair()[0]
                line_profile = profile(user_list_top[0])
                
                first = self.kwd.most_used()
                last = self.kwd.least_used()
                last_count = len(last)
                limit = 10

                text = u'【回覆組相關統計資料】'
                text += u'\n\n已使用回覆組【{}】次'.format(kwd.used_count_sum())
                text += u'\n\n已登錄【{}】組回覆組\n【{}】組貼圖關鍵字 | 【{}】組圖片回覆'.format(
                    kwpct,
                    self.kwd.sticker_keyword_count(),
                    self.kwd.picture_reply_count())
                text += u'\n\n共【{}】組回覆組可使用 ({:.2%})\n【{}】組貼圖關鍵字 | 【{}】組圖片回覆'.format(
                    self.kwd.row_count(True),
                    self.kwd.row_count(True) / float(kwpct),
                    self.kwd.sticker_keyword_count(True),
                    self.kwd.picture_reply_count(True))
                
                text += u'\n\n製作最多回覆組的LINE使用者ID:\n{}'.format(user_list_top[0])
                text += u'\n製作最多回覆組的LINE使用者:\n{}【{}組 - {:.2%}】'.format(
                    error.main.line_account_data_not_found() if line_profile is None else line_profile.display_name,
                    user_list_top[1],
                    user_list_top[1] / float(kwpct))

                text += u'\n\n使用次數最多的回覆組【{}次，{}組】:\n'.format(first[0][kwdict_col.used_count], len(first))
                text += u'\n'.join([u'ID: {} - {}'.format(entry[kwdict_col.id],
                                                         u'(貼圖ID {})'.format(entry[kwdict_col.keyword].decode('utf-8')) if entry[kwdict_col.is_sticker_kw] else entry[kwdict_col.keyword].decode('utf-8')) for entry in first[0 : limit - 1]])
                
                text += u'\n\n使用次數最少的回覆組 【{}次，{}組】:\n'.format(last[0][kwdict_col.used_count], len(last))
                text += u'\n'.join([u'ID: {} - {}'.format(entry[kwdict_col.id],
                                                         u'(貼圖ID {})'.format(entry[kwdict_col.keyword].decode('utf-8')) if entry[kwdict_col.is_sticker_kw] else entry[kwdict_col.keyword].decode('utf-8')) for entry in last[0 : limit - 1]])
                if last_count - limit > 0:
                    text += u'\n...(還有{}組)'.format(last_count - limit)
            elif category == 'SYS':
                text = u'【系統統計資料 - 開機後重設】\n'
                text += u'開機時間: {} (UTC+8)\n'.format(boot_up)
                text += u'\n自動產生網頁瀏覽次數: {}'.format(rec['webpage'])
                text += u'\n\n已呼叫系統指令{}次(包含呼叫失敗)。\n'.format(rec['JC_called'])
                text += u'\n'.join([u'{} - {}次'.format(cmd, cmd_obj.count) for cmd, cmd_obj in cmd_dict.items()])
                text += u'\n已使用MFF傷害計算輔助系統{}次。'.format(rec['MFF_called'])
            else:
                text = error.main.invalid_thing_with_correct_format(u'參數1', u'GRP、KW或SYS', params[1])
        else:
            text = error.main.incorrect_param(u'參數1', u'GRP、KW或SYS')

        return text