# -*- coding: utf-8 -*-

from enum import Enum
from tool import random_gen
from error import error
import time

class rps(object):
    """Game of Rock-Paper-Scissors"""

    def __init__(self, vs_bot):
        self._gap_time = -1
        self._vs_bot = vs_bot

    def register(self, rock, paper, scissor):
        if scissor == rock == paper:
            return error.main.miscellaneous(u'剪刀、石頭、布不可相同，請重新輸入。')
        elif scissor == rock:
            return error.main.miscellaneous(u'剪刀和石頭的定義衝突(相同)，請重新輸入。')
        elif rock == paper:
            return error.main.miscellaneous(u'石頭和布的定義衝突(相同)，請重新輸入。')
        elif paper == scissor:
            return error.main.miscellaneous(u'布和剪刀的定義衝突(相同)，請重新輸入。')
        
        self._battle_dict = {rock: battle_item.rock,
                             paper: battle_item.paper,
                             scissor: battle_item.scissor}
        
        self._play_entered = False
        self._play1 = battle_item.none
        self._play2 = battle_item.none
        self._player1_name = u'(Undefined)'
        self._player2_name = u'(Undefined)'
        self._result_enum = battle_result.undefined
        self._play_begin_time = 0

    def play(self, item, player):
        if self._play_entered:
            return self._play2(item, player)
        else:
            return self._play1(item, player)

    def result_analyze(self):
        if self._result_enum == battle_result.tie:
            text = u'平手'
        elif self._result_enum == battle_result.win1:
            text = u'{} 勝利'.format(self._player1_name)
        elif self._result_enum == battle_result.win2:
            text = u'{} 勝利'.format(self._player2_name)
        elif self._result_enum == battle_result.undefined:
            text = u'尚未猜拳'
        else:
            raise ValueError(error.main.invalid_thing(u'猜拳結果', result_enum))

        if instance_rps is not None:
            text += u'\n\n兩拳間格時間 {:.2f} 秒'.format(self._gap_time)

        return text

    def _play1(self, item, player):
        try:
            self._play1 = self._battle_dict[item]
            self._player1_name = player

            if self._vs_bot:
                self._gap_time = 0
                self._play2(random_gen.random_drawer.draw_number(1, 3), u'(Auto)')
            else:
                self._play_entered = True
                self._play_begin_time = time.time()

        except KeyError:
            self._play_entered = False

    def _play2(self, item, player):
        try:
            self._play2 = self._battle_dict[item]
            self._player2_name = player
            self._gap_time = time.time() - self._play_begin_time
            self._calculate_result()
        except KeyError:
            pass

    def _calculate_result(self):
        result = int(self._play1) - int(self._play2)
        result = result % 3
        self._play_entered = False
        self._result_enum = battle_result(result)

    def in_battle_dict(self, sticker_id):
        try:
            return sticker_id in self._battle_dict.iterkeys()
        except NameError:
            return False

    @property
    def gap_time(self):
        return self._gap_time

    @property
    def play_entered(self):
        try:
            return self._play_entered
        except NameError:
            return False

    @property
    def player1_name(self):
        try:
            return self._player1_name
        except NameError:
            pass

    @property
    def player2_name(self):
        try:
            return self._player2_name
        except NameError:
            pass

    @property
    def vs_bot(self):
        return self._vs_bot

class battle_item(Enum):
    rock = 1
    paper = 2
    scissor = 3
    none = -1

class battle_result(Enum):
    undefined = -1
    tie = 0
    win1 = 1
    win2 = 2
