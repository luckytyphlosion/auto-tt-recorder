# Copyright (C) 2022 luckytyphlosion
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

MUSIC_NONE = 0
MUSIC_GAME_BGM = 1
MUSIC_CUSTOM_MUSIC = 2

class MusicOption:
    __slots__ = ("option", "music_filename")

    def __init__(self, option, music_filename=None):
        self.option = option
        self.music_filename = music_filename

music_option_bgm = MusicOption(MUSIC_GAME_BGM)
