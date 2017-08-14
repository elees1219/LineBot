# -*- coding: utf-8 -*-
import errno, os, sys
import validators
import urllib
from urlparse import urlparse
import requests

from flask import Flask, request, abort, url_for
import hashlib 

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

from db import kw_dict_mgr, kwdict_col, group_ban, gb_col, message_tracker, msg_track_col

from error import error
from bot import system, webpage_auto_gen
from bot.system import line_api_proc, system_data

# tool import
from tool import mff, random_gen
from db.msg_track import msg_event_type

class text_msg(object):
    def __init__(self, api_proc, kw_dict_mgr, group_ban, msg_trk, oxford_obj, permission_key_list, system_data, game_object):
        self.kwd = kw_dict_mgr
        self.gb = group_ban
        self.msg_trk = msg_trk
        self.oxford_obj = oxford_obj
        self._webpage_generator = webpage_auto_gen.webpage()
        self.permission_verifier = system.permission_verifier(permission_key_list)
        self.api_proc = api_proc
        self.system_data = system_data
        self.game_object = game_object

    def S(self, src, params):
        key = params.pop(1)
        sql = params[1]

        if isinstance(src, SourceUser) and self.permission_verifier.permission_level(key) >= system.permission.bot_admin:
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
        new_uid = line_api_proc.source_user_id(src)
        
        if not line_api_proc.is_valid_user_id(new_uid):
            text = error.main.unable_to_receive_user_id()
        else:
            if params[4] is not None:
                action_kw = params[1]
                kw = params[2]
                action_rep = params[3]
                rep = params[4]
                 
                if action_kw != 'STK':
                    results = None
                    text = error.main.incorrect_param(u'參數1', u'STK')
                elif not system.string_is_int(kw):
                    results = None
                    text = error.main.incorrect_param(u'參數2', u'整數數字')
                elif action_rep != 'PIC':
                    results = None
                    text =  error.main.incorrect_param(u'參數3', u'PIC')
                else:
                    if system.string_is_int(rep):
                        rep = kw_dict_mgr.sticker_png_url(rep)
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

                    if system.string_is_int(rep):
                        rep = kw_dict_mgr.sticker_png_url(rep)
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

                    if system.string_is_int(kw):
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

    def M(self, src, params):
        key = params.pop(1)
        if not isinstance(src, SourceUser) or self.permission_verifier.permission_level(key) < system.permission.moderator:
            text = error.main.restricted(1)
        elif not line_api_proc.is_valid_user_id(line_api_proc.source_user_id(src)):
            text = error.main.unable_to_receive_user_id()
        else:
            text = self.A(src, params)

        return text

    def D(self, src, params, pinned=False):
        deletor_uid = line_api_proc.source_user_id(src)
        if not line_api_proc.is_valid_user_id(deletor_uid):
            text = error.main.unable_to_receive_user_id()
        else:
            if params[2] is None:
                kw = params[1]

                results = self.kwd.delete_keyword(kw, deletor_uid, pinned)
            else:
                action = params[1]

                if action == 'ID':
                    pair_id = params[2]

                    if system.string_is_int(pair_id):
                        results = self.kwd.delete_keyword_id(pair_id, deletor_uid, pinned)
                    else:
                        results = None
                        text = error.main.incorrect_param(u'參數2', u'整數數字')
                else:
                    results = None
                    text = error.main.incorrect_param(u'參數1', u'ID')

            if results is not None and len(results) > 0:
                for result in results:
                    line_profile = self.api_proc.profile(result[int(kwdict_col.creator)])

                    text = u'已刪除回覆組。{}\n'.format(u'(置頂)' if pinned else '')
                    text += kw_dict_mgr.entry_basic_info(result)
                    text += u'\n此回覆組由 {} 製作。'.format(
                         error.main.line_account_data_not_found() if line_profile is None else line_profile.display_name)
            else:
                if system.string_is_int(kw):
                    text = error.main.miscellaneous(u'偵測到參數1是整數。若欲使用ID作為刪除根據，請參閱小水母使用說明。')
                else:
                    text = error.main.pair_not_exist_or_insuffieicnt_permission()

        return text

    def R(self, src, params):
        key = params.pop(1)
        if not isinstance(src, SourceUser) or self.permission_verifier.permission_level(key) < system.permission.group_admin:
            text = error.main.restricted(2)
        elif not line_api_proc.is_valid_user_id(line_api_proc.source_user_id(src)):
            text = error.main.unable_to_receive_user_id()
        else:
            text = self.D(src, params, True)

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
            text += u'\n完整搜尋結果顯示: {}'.format(self._webpage_generator.rec_query(q_list['full']))
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
                if system.string_is_int(pair_id):
                    results = self.kwd.get_info_id(pair_id)   
                else:
                    results = None
                    text += error.main.invalid_thing_with_correct_format(u'參數2', u'正整數', pair_id)
        else:
            kw = params[1]
            text = u'搜尋條件: 【關鍵字】或【回覆】為【{}】的回覆組。\n'.format(kw)

            results = self.kwd.get_info(kw)

        if results is not None:
            i_object = kw_dict_mgr.list_keyword_info(self.kwd, self.api_proc, results)
            text += i_object['limited']
            text += u'\n完整資訊URL: {}'.format(self._webpage_generator.rec_info(i_object['full']))
        else:
            text = error.main.miscellaneous(u'資料查詢主體為空。')

        return text

    def K(self, src, params):
        ranking_type = params[1]
        limit = params[2]

        try:
            limit = int(limit)
        except ValueError as err:
            text = error.main.incorrect_param(u'參數2(數量)', u'整數')
        else:
            Valid = True

            if ranking_type == 'USER':
                text = kw_dict_mgr.list_user_created_ranking(self.api_proc, self.kwd.user_created_rank(limit))
            elif ranking_type == 'KW':
                text = kw_dict_mgr.list_keyword_ranking(self.kwd.order_by_usedrank(limit))
            else:
                text = error.main.incorrect_param(u'參數1(種類)', u'USER(使用者排行)或KW(關鍵字排行)')
                Valid = False

            if Valid:
                text += u'\n\n完整使用者排名: {}\n完整關鍵字排名: {}'.format(
                    request.url_root + url_for('full_ranking', type='user')[1:],
                    request.url_root + url_for('full_ranking', type='used')[1:])

        return text

    def P(self, src, params):
        if params[1] is not None:
            category = params[1]

            if category == 'MSG':
                limit = 5

                sum_data = self.msg_trk.count_sum()
                tracking_data = message_tracker.entry_detail_list(self.msg_trk.order_by_recorded_msg_count(), limit, self.gb)

                text = u'【訊息流量統計】'
                text += u'\n收到(無對應回覆組): {}則文字訊息 | {}則貼圖訊息'.format(sum_data[msg_event_type.recv_txt], sum_data[msg_event_type.recv_stk])
                text += u'\n收到(有對應回覆組): {}則文字訊息 | {}則貼圖訊息'.format(sum_data[msg_event_type.recv_txt_repl], sum_data[msg_event_type.recv_stk_repl])
                text += u'\n回覆: {}則文字訊息 | {}則貼圖訊息'.format(sum_data[msg_event_type.send_txt], sum_data[msg_event_type.send_stk])

                text += u'\n\n【群組訊息統計資料 - 前{}名】\n'.format(limit)
                text += tracking_data['limited']
                text += u'\n\n完整資訊URL: {}'.format(self._webpage_generator.rec_info(tracking_data['full']))
            elif category == 'KW':
                kwpct = self.kwd.row_count()

                user_list_top = self.kwd.user_sort_by_created_pair()[0]
                line_profile = self.api_proc.profile(user_list_top[0])
                
                first = self.kwd.most_used()
                last = self.kwd.least_used()
                last_count = len(last)
                limit = 10

                text = u'【回覆組相關統計資料】'
                text += u'\n\n已使用回覆組【{}】次'.format(self.kwd.used_count_sum())
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

                text += u'\n\n使用次數最多的回覆組【{}次，{}組】:\n'.format(first[0][int(kwdict_col.used_count)], len(first))
                text += u'\n'.join([u'ID: {} - {}'.format(entry[int(kwdict_col.id)],
                                                         u'(貼圖ID {})'.format(entry[int(kwdict_col.keyword)].decode('utf-8')) if entry[int(kwdict_col.is_sticker_kw)] else entry[int(kwdict_col.keyword)].decode('utf-8')) for entry in first[0 : limit - 1]])
                
                text += u'\n\n使用次數最少的回覆組 【{}次，{}組】:\n'.format(last[0][int(kwdict_col.used_count)], len(last))
                text += u'\n'.join([u'ID: {} - {}'.format(entry[int(kwdict_col.id)],
                                                         u'(貼圖ID {})'.format(entry[int(kwdict_col.keyword)].decode('utf-8')) if entry[int(kwdict_col.is_sticker_kw)] else entry[int(kwdict_col.keyword)].decode('utf-8')) for entry in last[0 : limit - 1]])
                if last_count - limit > 0:
                    text += u'\n...(還有{}組)'.format(last_count - limit)
            elif category == 'SYS':
                global game_object

                text = u'【系統統計資料 - 開機後重設】\n'
                text += u'開機時間: {} (UTC+8)\n'.format(self.system_data.boot_up)
                text += u'\n【自動產生網頁相關】\n瀏覽次數: {}'.format(self.system_data.webpage_viewed)
                text += u'\n\n【系統指令相關(包含呼叫失敗)】\n總呼叫次數: {}\n'.format(self.system_data.sys_cmd_called)
                text += u'\n'.join([u'指令{} - {}'.format(cmd, cmd_obj.count) for cmd, cmd_obj in self.system_data.sys_cmd_dict.items()])
                text += u'\n\n【內建小工具相關】\nMFF傷害計算輔助 - {}'.format(self.system_data.helper_cmd_dict['MFF'].count)
                text += u'\n\n【小遊戲相關】\n猜拳遊戲數量 - {}\n猜拳次數 - {}'.format(self.game_object.rps_instance_count, self.system_data.game_cmd_dict['RPS'].count)
            else:
                text = error.main.invalid_thing_with_correct_format(u'參數1', u'GRP、KW或SYS', params[1])
        else:
            text = error.main.incorrect_param(u'參數1', u'MSG、KW或SYS')

        return text

    def G(self, src, params):
        if params[1] is not None:
            gid = params[1]
        else:
            gid = line_api_proc.source_channel_id(src)

        if params[1] is None and isinstance(src, SourceUser):
            text = error.main.incorrect_channel(False, True, True)
        else:
            if line_api_proc.is_valid_room_group_id(gid):
                group_detail = self.gb.get_group_by_id(gid)

                uids = {u'管理員': group_detail[int(gb_col.admin)], u'副管I': group_detail[int(gb_col.moderator1)], 
                        u'副管II': group_detail[int(gb_col.moderator2)], u'副管III': group_detail[int(gb_col.moderator3)]}

                text = u'群組/房間頻道ID: {}\n'.format(gid)
                if group_detail is not None:
                    text += u'\n自動回覆機能狀態【{}】'.format(u'已停用' if group_detail[int(gb_col.silence)] else u'使用中')
                    for txt, uid in uids.items():
                        if uid is not None:
                            prof = self.api_proc.profile(uid)
                            text += u'\n\n{}: {}\n'.format(txt, error.main.line_account_data_not_found() if prof is None else prof.display_name)
                            text += u'{} 使用者ID: {}'.format(txt, uid)
                else:
                    text += u'\n自動回覆機能狀態【使用中】'

                group_tracking_data = self.msg_trk.get_data(gid)
                text += u'\n\n收到(無對應回覆組): {}則文字訊息 | {}則貼圖訊息'.format(group_tracking_data[int(msg_track_col.text_msg)], 
                                                                                    group_tracking_data[int(msg_track_col.stk_msg)])
                text += u'\n收到(有對應回覆組): {}則文字訊息 | {}則貼圖訊息'.format(group_tracking_data[int(msg_track_col.text_msg_trig)], 
                                                                                 group_tracking_data[int(msg_track_col.stk_msg_trig)])
                text += u'\n回覆: {}則文字訊息 | {}則貼圖訊息'.format(group_tracking_data[int(msg_track_col.text_rep)], 
                                                                    group_tracking_data[int(msg_track_col.stk_rep)])
            else:
                text = error.main.invalid_thing_with_correct_format(u'群組/房間ID', u'R或C開頭，並且長度為33字元', gid)

        return text

    def GA(self, src, params):
        error_no_action_fetch = error.main.miscellaneous(u'無對應指令。有可能是因為權限不足或是缺少參數造成的。')
       
        perm_dict = {3: u'權限: 開發者/機器人管理員',
                     2: u'權限: Group Admin',
                     1: u'權限: Group Moderator',
                     0: u'權限: User'}
        perm = int(self.permission_verifier.permission_level(params.pop(1)))
        pert = perm_dict[perm]

        param_count = len(params) - params.count(None)

        if isinstance(src, SourceUser):
            text = error_no_action_fetch

            # Set bot auto-reply switch
            if perm >= 1 and param_count == 3:
                action = params[1].replace(' ', '')
                gid = params[2]
                pw = params[3]

                action_dict = {'SF': True, 'ST': False}
                status_silence = {True: u'停用', False: u'啟用'}

                if action in action_dict:
                    settarget = action_dict[action]

                    if self.gb.set_silence(gid, str(settarget), pw):
                        text = u'群組自動回覆功能已{}。\n\n群組/房間ID: {}'.format(status_silence[settarget], gid)
                    else:
                        text = u'群組靜音設定變更失敗。\n\n群組/房間ID: {}'.format(gid)
                else:
                    text = error.main.invalid_thing(u'參數1(動作)', action)
            # Set new admin/moderator 
            elif perm >= 2 and param_count == 5:
                action = params[1]
                gid = params[2]
                new_uid = params[3]
                pw = params[4]
                new_pw = params[5]

                action_dict = {'SA': self.gb.change_admin, 
                               'SM1': self.gb.set_mod1,
                               'SM2': self.gb.set_mod2,
                               'SM3': self.gb.set_mod3}
                pos_name = {'SA': u'群組管理員',
                            'SM1': u'群組副管 1',
                            'SM2': u'群組副管 2',
                            'SM3': u'群組副管 3'}

                line_profile = self.api_proc.profile(new_uid)

                if line_profile is not None:
                    try:
                        if action_dict[action](gid, new_uid, pw, new_pw):
                            position = pos_name[action]

                            text = u'群組管理員已變更。\n'
                            text += u'群組/房間ID: {}\n\n'.format(gid)
                            text += u'新{}使用者ID: {}\n'.format(position, new_uid)
                            text += u'新{}使用者名稱: {}\n\n'.format(position, line_profile.display_name)
                            text += u'新{}密碼: {}\n'.format(position, new_pw)
                            text += u'請記好密碼，嚴禁洩漏，或在群頻中直接開關群組自動回覆功能！'
                        else:
                            text = u'{}變更作業失敗。'.format(pos_name[action])
                    except KeyError as Ex:
                        text = error.main.invalid_thing(u'參數1(動作)', action)
                else:
                    text = error.main.line_account_data_not_found()
            # Add new group - only execute when data not found
            elif perm >= 3 and param_count == 4:
                action = params[1]
                gid = params[2]
                uid = params[3]
                pw = params[4]
                
                if action != 'N':
                    text = error.main.invalid_thing(u'參數1(動作)', action)
                else:
                    group_data_test = self.gb.get_group_by_id(gid)
                    if len(group_data_test) > 0:
                        text = u'群組資料已存在。'
                    else:
                        line_profile = self.api_proc.profile(uid)

                        if line_profile is not None:
                            if self.gb.new_data(gid, uid, pw):
                                text = u'群組資料註冊成功。\n'
                                text += u'群組ID: {}'.format(gid)
                                text += u'群組管理員ID: {}'.format(uid)
                                text += u'群組管理員名稱: {}'.format(line_profile.display_name)
                            else:
                                text = u'群組資料註冊失敗。'
                        else:
                            text = error.main.line_account_data_not_found()
        else:
            text = error.main.incorrect_channel()

        return pert, text

    def H(self, src, params):
        if params[1] is not None:
            uid = params[1]
            line_profile = self.api_proc.profile(uid)
            
            source_type = u'使用者詳細資訊'

            if not line_api_proc.is_valid_user_id(uid):
                text = error.main.invalid_thing_with_correct_format(u'使用者ID', u'U開頭，並且長度為33字元', uid)
            else:
                if line_profile is not None:
                    kwid_arr = self.kwd.user_created_id_array(uid)
                    if len(kwid_arr) < 1:
                        kwid_arr = [u'無']

                    text = u'使用者ID: {}\n'.format(uid)
                    text += u'使用者名稱: {}\n'.format(line_profile.display_name)
                    text += u'使用者頭貼網址: {}\n'.format(line_profile.picture_url)
                    text += u'使用者狀態訊息: {}\n\n'.format(line_profile.status_message)
                    text += u'使用者製作的回覆組ID: {}'.format(u', '.join(map(unicode, kwid_arr)))
                else:
                    text = u'找不到使用者ID - {} 的詳細資訊。'.format(uid)
        else:
            text = line_api_proc.source_channel_id(src)
            if isinstance(src, SourceUser):
                source_type = u'頻道種類: 使用者(私訊)'
            elif isinstance(src, SourceGroup):
                source_type = u'頻道種類: 群組'
            elif isinstance(src, SourceRoom):
                source_type = u'頻道種類: 房間'
            else:
                source_type = u'頻道種類: 不明'

        return [source_type, text]

    def SHA(self, src, params):
        target = params[1]

        if target is not None:
            text = hashlib.sha224(target.encode('utf-8')).hexdigest()
        else:
            text = error.main.incorrect_param(u'參數1', u'非空參數')

        return text

    def O(self, src, params):
        voc = params[1]

        if not self.oxford_obj.enabled:
            text = error.main.miscellaneous(u'牛津字典功能已停用。可能是因為超過單月查詢次數或無效的API密鑰。')
        else:
            j = self.oxford_obj.get_data_json(voc)

            if type(j) is int:
                code = j

                if code == 404:
                    text = error.main.no_result()
                else:
                    text = u'查詢字典時發生錯誤。\n\n狀態碼: {} ({}).'.format(code, httplib.responses[code])
            else:
                text = u''
                section_splitter = u'.................................................................'

                lexents = j['results'][0]['lexicalEntries']
                for lexent in lexents:
                    text += u'=={} ({})=='.format(lexent['text'], lexent['lexicalCategory'])
                    
                    lexentarr = lexent['entries']
                    for lexentElem in lexentarr:
                        if 'senses' in lexentElem:
                            sens = lexentElem['senses']
                            
                            text += u'\nDefinition:'
                            for index, sen in enumerate(sens, start=1):
                                if 'definitions' in sen:
                                    for de in sen['definitions']:
                                        text += u'\n{}. {} {}'.format(index, de, u'({})'.format(u', '.join(sen['registers'])) if u'registers' in sen else u'')
                                        
                                if 'crossReferenceMarkers' in sen:
                                    for crm in sen['crossReferenceMarkers']:
                                        text += u'\n{}. {} (Cross Reference Marker)'.format(index, crm)
                                
                                if 'examples' in sen:
                                    for ex in sen['examples']:
                                        text += u'\n------{}'.format(ex['text'])
                        else:
                            print xxxxxx
                            text += u'Senses not found in dictionary.'

                    text += u'\n{}\n'.format(section_splitter)

                text += u'Powered by Oxford Dictionary.'

        return text

    def RD(self, src, params):
        if params[2] is not None:
            if params[1].endswith('%') and params[1].count('%') == 1:
                opportunity = params[1].replace('%', '')
                scout_count = params[2]
                shot_count = 0
                miss_count = 0
                if not system.string_is_float(opportunity):
                    text = error.main.incorrect_param(u'參數1(機率)', u'百分比加上符號%')
                elif not system.string_is_float(scout_count):
                    text = error.main.incorrect_param(u'參數2(抽籤次數)', u'整數')
                elif int(scout_count) > 999999:
                    text = error.main.invalid_thing_with_correct_format(u'參數2(抽籤次數)', u'小於999999的整數', scout_count)
                else:
                    for i in range(int(scout_count)):
                        result = random_gen.random_drawer.draw_probability(float(opportunity) / 100.0)
                        if result:
                            shot_count += 1
                        else:
                            miss_count += 1
                    text = u'抽籤機率【{}%】\n抽籤結果【中{}次 | 失{}次】\n實際中率【{:.2%}】'.format(opportunity, shot_count, miss_count, shot_count / float(scout_count))
            else:
                start_index = params[1]
                end_index = params[2]
                if not start_index.isnumeric():
                    text = error.main.invalid_thing_with_correct_format(u'起始抽籤數字', u'整數', start_index)
                elif not end_index.isnumeric():
                    text = error.main.invalid_thing_with_correct_format(u'終止抽籤數字', u'整數', start_index)
                else:
                    text = u'抽籤範圍【{}~{}】\n抽籤結果【{}】'.format(start_index, end_index, random_gen.random_drawer.draw_number(start_index, end_index))
        elif params[1] is not None:
            text_splitter = '  '
            if text_splitter in params[1]:
                texts = params[1]
                text_list = texts.split(text_splitter)
                text = u'抽籤範圍【{}】\n抽籤結果【{}】'.format(', '.join(text_list), random_gen.random_drawer.draw_text(text_list))
            elif params[1].endswith('%') and params[1].count('%') == 1:
                opportunity = params[1].replace('%', '')
                text = u'抽籤機率【{}%】\n抽籤結果【{}】'.format(
                    opportunity, 
                    u'恭喜中獎' if random_gen.random_drawer.draw_probability(float(opportunity) / 100.0) else u'銘謝惠顧')
            else:
                text = error.main.invalid_thing(u'參數1', params[1])
        else:
            text = error.main.lack_of_thing(u'參數')

        return text

    def STK(self, src, params):
        last_sticker = self.system_data.get_last_sticker(line_api_proc.source_channel_id(src))
        if last_sticker is not None:
            text = u'最後一個貼圖的貼圖ID為{}。'.format(last_sticker)
        else:
            text = u'沒有登記到本頻道的最後貼圖ID。如果已經有貼過貼圖，則可能是因為機器人剛剛才啟動而造成。\n\n本次開機時間: {}'.format(self.system_data.boot_up)

        return text

    def T(self, src, params):
        if params[1] is not None:
            text = params[1]

            if isinstance(text, unicode):
                # unicode to utf-8
                text = text.encode('utf-8')
            else:
                try:
                    # maybe utf-8
                    text = text.decode('utf-8').encode('utf-8')
                except UnicodeError:
                    # gbk to utf-8
                    text = text.decode('gbk').encode('utf-8')
        else:
            text = error.main.lack_of_thing(u'參數')
        
        return urllib.quote(text)

    @staticmethod
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

    def split_verify(self, cmd, splitter, param_text):
        if cmd not in self.system_data.sys_cmd_dict:
            return error.main.invalid_thing(u'指令', cmd)

        max_prm = self.system_data.sys_cmd_dict[cmd].split_max
        min_prm = self.system_data.sys_cmd_dict[cmd].split_min
        params = text_msg.split(param_text, splitter, max_prm)

        if min_prm > len(params) - params.count(None):
            return error.main.lack_of_thing(u'參數')

        params.insert(0, None)
        self.system_data.sys_cmd_dict[cmd].count += 1
        return params


class oxford_dict(object):
    def __init__(self, language):
        """
        Set environment variable "OXFORD_ID", "OXFORD_KEY" as presented api id and api key.
        """
        self._language = language
        self._url = 'https://od-api.oxforddictionaries.com:443/api/v1/entries/{}/'.format(self._language)
        self._id = os.getenv('OXFORD_ID', None)
        self._key = os.getenv('OXFORD_KEY', None)
        self._enabled = False if self._id is None or self._key is None else True

    def get_data_json(self, word):
        url = self._url + word.lower()
        r = requests.get(url, headers = {'app_id': self._id, 'app_key': self._key})
        status_code = r.status_code

        if status_code != requests.codes.ok:
            return status_code
        else:
            return r.json()

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

