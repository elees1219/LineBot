# -*- coding: utf-8 -*-
import os, sys

from error import error
from bot.system import line_api_proc, string_is_int

import game

from linebot.models import SourceUser

class game_msg(object):
    def __init__(self, game_data, line_api_proc):
        self._game_data = game_data
        self._line_api = line_api_proc

    def RPS(self, src, params):
        cid = line_api_proc.source_channel_id(src)
        uid = line_api_proc.source_user_id(src)

        if params[4] is not None:
            rps_obj = self._game_data.get_rps(cid)
            if rps_obj is not None and isinstance(rps_obj, game.rps):
                action = params[1]
                if action == 'ADD':
                    item_type = params[2]
                    is_sticker = params[3]
                    content = params[4]

                    battle_item = None

                    if item_type == 'R':
                        battle_item = game.battle_item.rock
                    if item_type == 'P':
                        battle_item = game.battle_item.paper
                    if item_type == 'S':
                        battle_item = game.battle_item.scissor

                    if battle_item is not None:
                        if is_sticker == 'STK':
                            if string_is_int(content):
                                rps_obj.register_battle_item(battle_item, True, content)
                                text = rps_obj.battle_item_dict_text()
                            else:
                                text = error.main.incorrect_param(u'參數4', u'整數，以代表貼圖ID')
                        elif is_sticker == 'TXT':
                            rps_obj.register_battle_item(battle_item, False, content)
                            text = rps_obj.battle_item_dict_text()
                        else:
                            text = error.main.incorrect_param(u'參數3', u'STK(是貼圖ID)或TXT(文字訊息)')
                    else:
                        text = error.main.incorrect_param(u'參數2', u'S(剪刀)、R(石頭)或P(布)')
                else:
                    text = error.main.incorrect_param(u'參數1', u'ADD')
            else:
                text = error.main.miscellaneous(u'尚未建立猜拳遊戲。')
        elif params[3] is not None:
            scissor = params[1]
            rock = params[2]
            paper = params[3]

            rps_obj = game.rps(True if isinstance(src, SourceUser) else False, rock, paper, scissor)
            if isinstance(rps_obj, game.rps):
                if line_api_proc.is_valid_user_id(uid):
                    rps_obj.register_player(self._line_api.profile(uid).display_name, uid)
                    text = u'遊戲建立成功。\n\n剪刀貼圖ID: {}\n石頭貼圖ID: {}\n布貼圖ID: {}'.format(scissor, rock, paper)
                    self._game_data.set_rps(cid, rps_obj)
                else:
                    text = error.main.unable_to_receive_user_id()
            else:
                text = rps_obj
        elif params[2] is not None:
            rps_obj = self._game_data.get_rps(cid)
            if rps_obj is not None and isinstance(rps_obj, game.rps):
                action = params[1]
                battle_item_text = params[2]

                if action == 'RST':
                    if battle_item_text == 'R':
                        rps_obj.reset_battle_item(game.battle_item.rock)
                        text = u'已重設代表【石頭】的物件。'
                    elif battle_item_text == 'P':
                        rps_obj.reset_battle_item(game.battle_item.paper)
                        text = u'已重設代表【布】的物件。'
                    elif battle_item_text == 'S':
                        rps_obj.reset_battle_item(game.battle_item.scissor)
                        text = u'已重設代表【剪刀】的物件。'
                    else:
                        text = error.main.incorrect_param(u'參數2', u'R(石頭), P(布), S(剪刀)')
                else:
                    text = error.main.incorrect_param(u'參數1', u'RST')
            else:
                text = error.main.miscellaneous(u'尚未建立猜拳遊戲。')
        elif params[1] is not None:
            rps_obj = self._game_data.get_rps(cid)
            action = params[1]

            if rps_obj is not None and isinstance(rps_obj, game.rps):
                if action == 'DEL':
                    self._game_data.del_rps(cid)
                    text = u'猜拳遊戲已刪除。'
                elif action == 'RST':
                    rps_obj.reset_statistics()
                    text = u'猜拳遊戲統計資料已重設。'
                elif action == 'R':
                    text = rps_obj.battle_item_dict_text(game.battle_item.rock)
                elif action == 'P':
                    text = rps_obj.battle_item_dict_text(game.battle_item.paper)
                elif action == 'S':
                    text = rps_obj.battle_item_dict_text(game.battle_item.scissor)
                elif action == 'PLAY':
                    uid = line_api_proc.source_user_id(src)
                    if line_api_proc.is_valid_user_id(uid):
                        player_name = self._line_api.profile(uid).display_name
                        reg_success = rps_obj.register_player(player_name, uid)
                        if reg_success:
                            text = u'成功註冊玩家 {}。'.format(player_name)
                        else:
                            text = u'玩家 {} 已存在於玩家清單中。'.format(player_name)
                    else:
                        text = error.main.unable_to_receive_user_id()
                elif action == 'SW':
                    rps_obj.enabled = not rps_obj.enabled
                    if rps_obj.enabled:
                        text = u'遊戲已繼續。'
                    else:
                        text = u'遊戲已暫停。'
                else:
                    text = error.main.incorrect_param(u'參數1', u'DEL, RST, R, P, S, PLAY, SW')
            else:
                text = error.main.miscellaneous(u'尚未建立猜拳遊戲。')
        else:
            rps_obj = self._game_data.get_rps(cid)
            if rps_obj is not None and isinstance(rps_obj, game.rps):
                if rps_obj.player_dict is not None and len(rps_obj.player_dict) > 0:
                    text = game.rps.player_stats_text(rps_obj.player_dict)
                    text += '\n\n'
                    text += rps_obj.battle_item_dict_text()
                else:
                    text = error.main.miscellaneous(u'無玩家資料。')
            else:
                text = error.main.miscellaneous(u'尚未建立猜拳遊戲。')

        return text
