# -*- coding: utf-8 -*-

import game
from collections import defaultdict

class game_objects(object):
    def __init__(self):
        self._rps = defaultdict(game.rps)

    @rps_collection.setter
    def rps_collection(self, value):
        self._rps = value

    def set_rps(self, cid, rps):
        self._rps[cid] = rps

    def del_rps(self, cid):
        del self._rps[cid]

    def get_rps(self, cid):
        return self._rps.get(cid)
