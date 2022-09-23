-- Copyright (C) 2022 luckytyphlosion
--
-- This program is free software; you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation; either version 2 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program; if not, write to the Free Software
-- Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

----- GLOBAL VARIABLES -----
package.path = GetScriptsDir() .. "MKW/MKW_core.lua"
local core = require("MKW_core")
package.path = GetScriptsDir() .. "MKW/MKW_Pointers.lua"
local Pointers = require("MKW_Pointers")
--Add an underscore (_) to the beginning of the filename if you want the script to auto launch once you start a game!

function onScriptStart()
	if GetGameID() ~= "RMCP01" and GetGameID() ~= "RMCJ01" and GetGameID() ~= "RMCE01" and GetGameID() ~= "RMCK01" then
		SetScreenText("")
		CancelScript()
	end
	--SetScreenText(GetGameID())
	initializePlayGhost()
end

function setFrameOfInput(frame)
	WriteValue32(Pointers.getFrameOfInputAddress(), frame)
end

function getRaceCompletion()
	return ReadValueFloat(Pointers.getRaceData2Pointer() + 0xC + 0x0 + 0xC)
end

local helper_isScriptEnabled = true

LUA_MODE_RECORD_GHOST_FROM_TT_GHOST_SELECT = 0
LUA_MODE_RECORD_TOP_10 = 1
LUA_MODE_RECORD_MK_CHANNEL_GHOST_SCREEN = 2
LUA_MODE_RECORD_GHOST_ONLY = 3

local ADVANCE_TO_TRACK_SELECT = 1
local CHOOSE_MUSHROOM_CUP = 2
local CHOOSE_FLOWER_CUP = 3
local CHOOSE_STAR_CUP = 4
local CHOOSE_SPECIAL_CUP = 5
local CHOOSE_SHELL_CUP = 6
local CHOOSE_BANANA_CUP = 7
local CHOOSE_LEAF_CUP = 8
local CHOOSE_LIGHTNING_CUP = 9
local DETERMINE_CUP_MENU_POS = 10
local CHOOSE_CUP_MENU_POS_DOWN = 11
local CHOOSE_CUP_MENU_POS_UP = 12
local CHOOSE_TRACK_PLAY_GHOST = 13
local NAVIGATE_TO_MAIN_GHOST = 14
local NAVIGATE_TO_2ND_GHOST = 15
local NAVIGATE_TO_3RD_GHOST = 16
local ADV_LIVE_REPLAY_WATCH_REPLAY = 17
local NAVIGATE_TO_2ND_GHOST_2 = 18
local NAVIGATE_TO_3RD_GHOST_2 = 19
local ADV_LIVE_REPLAY_RACE_GHOST = 20
local NAVIGATE_TO_MAIN_GHOST_NO_COMPARE = 21
local NAVIGATE_TO_2ND_GHOST_NO_COMPARE = 22
local ADV_LIVE_REPLAY_WATCH_REPLAY_NO_COMPARE = 23
local NAVIGATE_TO_2ND_GHOST_NO_COMPARE_2 = 24
local ADV_LIVE_REPLAY_SOLO_TIME_TRIAL = 25
local ADV_LIVE_REPLAY_TT_GHOST_SELECT_COMMON = 26
local ADV_LIVE_REPLAY_GHOST_ONLY_COMMON = 27
local ADV_LIVE_REPLAY_COMMON = 28

local DO_CUSTOM_TOP_10 = 1

local DO_MK_CHANNEL_GHOST_SCREEN = 1

local EXECUTING_ACTION = 1
local IN_DELAY = 2
local EXIT_LOOP_NO_DELAY = 3

local WAITING_FOR_KCP0_TO_KCP_LAST = 0
local WAITING_FOR_KCP_LAST_TO_KCP0 = 1
local DETECTED_ULTRA = 2

local curSegmentIndexG = ADVANCE_TO_TRACK_SELECT
local curActionIndexG = 1
local curStateG = EXECUTING_ACTION
local delayEndFrameCountG = 0
local cursorSetManuallyG = false
local glitchDetectionStateG = WAITING_FOR_KCP0_TO_KCP_LAST
local curLapOnPrevFrameG = 0
local curKCPOnPrevFrameG = -1
local curLapOnKCP0EntryG = -1

local curSegmentIndexForNextFrame = ADVANCE_TO_TRACK_SELECT
local curActionIndexForNextFrame = 1
local curStateForNextFrame = EXECUTING_ACTION
local delayEndFrameCountForNextFrame = 0
local cursorSetManuallyForNextFrame = false
local glitchDetectionStateForNextFrame = WAITING_FOR_KCP0_TO_KCP_LAST
local curLapOnPrevFrameForNextFrame = 0
local curKCPOnPrevFrameForNextFrame = -1
local curLapOnKCP0EntryForNextFrame = -1

local params = {}

local outputParams = {}

local lastKCP = -1;

local cupDebugText = ""
local triggeredFlowerCupText = ""
local frameOfInputText = ""
local recordingStartedText = ""
local lastPtsText = ""
local detectedUltraText = ""
local detected95RuleText = ""
local detectedReverse95RuleText = ""
local detectedL4UltraText = ""
local detectedL495RuleText = ""
local detectedL4Reverse95RuleText = ""

function setChooseCupState(curSegmentIndex, curActionIndex, curState)
	cup = tonumber(params["cup"])
	cupDebugText = string.format("cup: %d\n", cup)
	curSegmentIndex = CHOOSE_MUSHROOM_CUP + cup
	curActionIndex = 1
	curState = IN_DELAY
	return curSegmentIndex, curActionIndex, curState
end

function determineCupMenuPos(curSegmentIndex, curActionIndex, curState)
	cupMenuPos = tonumber(params["cupMenuPos"])
	if cupMenuPos == 0 then
		curSegmentIndex = CHOOSE_TRACK_PLAY_GHOST
		curActionIndex = 1
	elseif cupMenuPos == 1 then
		curSegmentIndex = CHOOSE_CUP_MENU_POS_DOWN
		curActionIndex = 2
	elseif cupMenuPos == 2 then
		curSegmentIndex = CHOOSE_CUP_MENU_POS_DOWN
		curActionIndex = 1
	elseif cupMenuPos == 3 then
		curSegmentIndex = CHOOSE_CUP_MENU_POS_UP
		curActionIndex = 1
	else
		error("Unknown case for cupMenuPos")
	end

	curState = EXECUTING_ACTION
	return curSegmentIndex, curActionIndex, curState
end

function determineIsComparison(curSegmentIndex, curActionIndex, curState)
	comparison = (params["comparison"] == "True")
	setFrameOfInput(1)
	if comparison then
		curSegmentIndex = NAVIGATE_TO_MAIN_GHOST
		curActionIndex = 1
	else
		curSegmentIndex = NAVIGATE_TO_MAIN_GHOST_NO_COMPARE
		curActionIndex = 1
	end
	curState = EXECUTING_ACTION
	return curSegmentIndex, curActionIndex, curState
end

function navigateToMainGhost(curSegmentIndex, curActionIndex, curState)
	mainGhostPos = tonumber(params["mainGhostPos"])
	if mainGhostPos == 0 then
		curSegmentIndex = ADV_LIVE_REPLAY_WATCH_REPLAY
		curActionIndex = 1
	elseif mainGhostPos == 1 then
		curSegmentIndex = NAVIGATE_TO_2ND_GHOST
		curActionIndex = 1
	elseif mainGhostPos == 2 then
		curSegmentIndex = NAVIGATE_TO_3RD_GHOST
		curActionIndex = 1
	end
	curState = EXECUTING_ACTION
	return curSegmentIndex, curActionIndex, curState
end

function navigateToCompareGhost(curSegmentIndex, curActionIndex, curState)
	compareGhostPos = tonumber(params["compareGhostPos"])
	if compareGhostPos == 0 then
		curSegmentIndex = ADV_LIVE_REPLAY_RACE_GHOST
		curActionIndex = 1
	elseif compareGhostPos == 1 then
		curSegmentIndex = NAVIGATE_TO_2ND_GHOST_2
		curActionIndex = 1
	elseif compareGhostPos == 2 then
		curSegmentIndex = NAVIGATE_TO_3RD_GHOST_2
		curActionIndex = 1
	else
		CancelScript()
	end

	curState = EXECUTING_ACTION
	return curSegmentIndex, curActionIndex, curState
end

function waitFrameOfInput0(curSegmentIndex, curActionIndex, curState)
	frameOfInput = core.getFrameOfInput()
	if frameOfInput ~= 0 then
		curState = EXIT_LOOP_NO_DELAY
	else
		curActionIndex = curActionIndex + 1
		curState = IN_DELAY
	end
	return curSegmentIndex, curActionIndex, curState
end

function startDumpFrames(curSegmentIndex, curActionIndex, curState)
	SetFrameAndAudioDump(true)
	outputParams["frameRecordingStarts"] = GetFrameCount()
	curActionIndex = curActionIndex + 1
	curState = EXIT_LOOP_NO_DELAY
	return curSegmentIndex, curActionIndex, curState
end

function startDumpFramesForRecordFromTTGhostSelect(curSegmentIndex, curActionIndex, curState)
	if params["mode"] == LUA_MODE_RECORD_GHOST_FROM_TT_GHOST_SELECT then
		SetFrameAndAudioDump(true)
	else
		error("Expected mode to be LUA_MODE_RECORD_GHOST_FROM_TT_GHOST_SELECT!")
	end

	curActionIndex = curActionIndex + 1
	curState = EXIT_LOOP_NO_DELAY

	return curSegmentIndex, curActionIndex, curState
end

function stopDumpFramesForRecordFromTTGhostSelect(curSegmentIndex, curActionIndex, curState)
	if params["mode"] == LUA_MODE_RECORD_GHOST_FROM_TT_GHOST_SELECT then
		SetFrameAndAudioDump(false)
	end

	curActionIndex = curActionIndex + 1
	curState = EXIT_LOOP_NO_DELAY

	return curSegmentIndex, curActionIndex, curState
end

function renameTTGhostSelectDumpFiles(curSegmentIndex, curActionIndex, curState)
	if params["mode"] == LUA_MODE_RECORD_GHOST_FROM_TT_GHOST_SELECT then
		os.rename("User/Dump/Frames/framedump0.avi", "User/Dump/Frames/tt_ghost_select.avi")
		os.rename("User/Dump/Audio/dspdump.wav", "User/Dump/Audio/tt_ghost_select.wav")
	end
	curActionIndex = curActionIndex + 1
	curState = IN_DELAY
	return curSegmentIndex, curActionIndex, curState
end

function startDumpFramesForEncodeLuaModes(curSegmentIndex, curActionIndex, curState)
	if params["mode"] == LUA_MODE_RECORD_GHOST_ONLY or params["mode"] == LUA_MODE_RECORD_GHOST_FROM_TT_GHOST_SELECT then
		SetFrameAndAudioDump(true)
		outputParams["frameRecordingStarts"] = GetFrameCount()		
	end

	curActionIndex = curActionIndex + 1
	curState = EXIT_LOOP_NO_DELAY

	return curSegmentIndex, curActionIndex, curState	
end

function stopDumpFrames(curSegmentIndex, curActionIndex, curState)
	SetFrameAndAudioDump(false)
	curActionIndex = curActionIndex + 1
	curState = EXIT_LOOP_NO_DELAY
	return curSegmentIndex, curActionIndex, curState
end

function waitRaceCompletion(curSegmentIndex, curActionIndex, curState)
	if core.getRaceCompletion() > tonumber(params["lapCount"]) + 1 then
		curActionIndex = curActionIndex + 1
		curState = IN_DELAY
	else
		curState = EXIT_LOOP_NO_DELAY
	end
	return curSegmentIndex, curActionIndex, curState
end

function navigateToMainGhostNoCompare(curSegmentIndex, curActionIndex, curState)
	mainGhostPos = tonumber(params["mainGhostPos"])
	if mainGhostPos == 0 then
		curSegmentIndex = ADV_LIVE_REPLAY_WATCH_REPLAY_NO_COMPARE
		curActionIndex = 1
	elseif mainGhostPos == 1 then
		curSegmentIndex = NAVIGATE_TO_2ND_GHOST_NO_COMPARE
		curActionIndex = 1
	else
		error(string.format("Invalid mainGhostPos %d!", mainGhostPos))
	end
	curState = EXECUTING_ACTION
	return curSegmentIndex, curActionIndex, curState
end

function navigateToMainGhostSoloTimeTrial(curSegmentIndex, curActionIndex, curState)
	mainGhostPos = tonumber(params["mainGhostPos"])
	setFrameOfInput(1)
	if mainGhostPos == 0 then
		curSegmentIndex = ADV_LIVE_REPLAY_SOLO_TIME_TRIAL
		curActionIndex = 1
	elseif mainGhostPos == 1 then
		curSegmentIndex = NAVIGATE_TO_2ND_GHOST_NO_COMPARE_2
		curActionIndex = 1
	else
		error(string.format("Invalid mainGhostPos %d!", mainGhostPos))
	end
	curState = EXECUTING_ACTION
	return curSegmentIndex, curActionIndex, curState
end

function ttGhostSelectOrGhostOnlyBranch(curSegmentIndex, curActionIndex, curState)
	if params["mode"] == LUA_MODE_RECORD_GHOST_FROM_TT_GHOST_SELECT then
		curSegmentIndex = ADV_LIVE_REPLAY_TT_GHOST_SELECT_COMMON
		curActionIndex = 1
	elseif params["mode"] == LUA_MODE_RECORD_GHOST_ONLY then
		curSegmentIndex = ADV_LIVE_REPLAY_GHOST_ONLY_COMMON
		curActionIndex = 1
	else
		error(string.format("Unknown lua mode %d in ttGhostSelectOrGhostOnlyBranch!", params["mode"]))
	end

	curState = EXECUTING_ACTION

	return curSegmentIndex, curActionIndex, curState	
end

function setFrameReplayStarts(curSegmentIndex, curActionIndex, curState)
	outputParams["frameReplayStarts"] = GetFrameCount()
	curState = EXECUTING_ACTION
	curActionIndex = curActionIndex + 1
	return curSegmentIndex, curActionIndex, curState
end

function setLastKCPValue(curSegmentIndex, curActionIndex, curState)
	lastKCP = core.getCurKeyCheckpoint();
	curState = EXECUTING_ACTION
	curActionIndex = curActionIndex + 1
	return curSegmentIndex, curActionIndex, curState
end

function waitFrameOfInput1ThenSetFrameInputStarts(curSegmentIndex, curActionIndex, curState)
	frameOfInput = core.getFrameOfInput()
	if frameOfInput ~= 1 then
		curState = EXIT_LOOP_NO_DELAY
	else
		curActionIndex = curActionIndex + 1
		curState = IN_DELAY
		outputParams["frameInputStarts"] = GetFrameCount()
	end

	return curSegmentIndex, curActionIndex, curState
end

function convertArrayToSet(arr)
	local set = {}
	for i, elem in ipairs(arr) do
		set[elem] = true
	end

	return set
end

-- Basically derived from https://github.com/Chadderz121/wii-ct-code/blob/8aaf1a8/bad1/bad1Data/mod/random.mod
-- License included below
------------------------------------------------------------------------------------
-- Copyright (C) 2011-2014 Alex "Chadderz" Chadwick
-- Copyright (C) 2011-2014 Robert "MrBean35000vr" Chadwick
-- 
-- Permission is hereby granted, free of charge, to any person obtaining a copy of
-- this software and associated documentation files (the "Software"), to deal in
-- the Software without restriction, including without limitation the rights to
-- use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
-- the Software, and to permit persons to whom the Software is furnished to do so,
-- subject to the following conditions:
-- 
-- The above copyright notice and this permission notice shall be included in all
-- copies or substantial portions of the Software.
-- 
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
-- FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
-- COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
-- IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
-- CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
------------------------------------------------------------------------------------

function isScreenDisplayed(menuIdToFind, allowedScreenIds)
	local menuDataPointer = Pointers.getMenuDataPointer()
	-- https://github.com/Chadderz121/wii-ct-code/blob/8aaf1a8/bad1/bad1Data/mod/random.mod#L21-L24
	local menuData = GetPointerNormal(menuDataPointer)
	local menuData_r4 = GetPointerNormal(menuData)

	local panelAddress, menuId
	local panelFound

	-- https://github.com/Chadderz121/wii-ct-code/blob/8aaf1a8/bad1/bad1Data/mod/random.mod#L26-L48
	-- with modifications
	while true do
		panelAddress = GetPointerNormal(menuData_r4 + 0x378)
		if panelAddress == 0 then
			menuData_r4 = menuData_r4 - 4
		else
			menuId = ReadValue32(panelAddress + 4)
			if menuId == menuIdToFind then
				panelFound = true
				break
			end

			if allowedScreenIds[menuId] then
				menuData_r4 = menuData_r4 - 4
			else
				panelFound = false
				break				
			end
		end
	end

	if not panelFound then
		return false
	end

	-- https://github.com/Chadderz121/wii-ct-code/blob/8aaf1a8/bad1/bad1Data/mod/random.mod#L72-L75
	local screenDisplayed = ReadValue32(panelAddress + 0x8)

	return screenDisplayed == 4
end

function waitScreenDisplayed(curSegmentIndex, curActionIndex, curState, menuIdToFind, allowedScreenIds)
	if isScreenDisplayed(menuIdToFind, allowedScreenIds) then
		curActionIndex = curActionIndex + 1
		curState = IN_DELAY
	else
		curState = EXIT_LOOP_NO_DELAY
	end

	return curSegmentIndex, curActionIndex, curState
end

CUP_SELECTION_SCREEN_ID = 0x6e
SINGLE_PLAYER_FROM_TT_CHANGE_COURSE_MENU_ALLOWED_SCREEN_IDS = {[0x6f] = true}

function waitCupSelectionScreenDisplayed(curSegmentIndex, curActionIndex, curState)
	return waitScreenDisplayed(curSegmentIndex, curActionIndex, curState, CUP_SELECTION_SCREEN_ID, SINGLE_PLAYER_FROM_TT_CHANGE_COURSE_MENU_ALLOWED_SCREEN_IDS)
end

local GHOST_HISTOGRAM_SCREEN_ID = 0xA8
local MK_CHANNEL_LEADERBOARDS_MENU_ALLOWED_SCREEN_IDS = convertArrayToSet({0x4E, 0x4F, 0x50, 0x51, 0x52, 0x6E, 0x6F, 0x84, 0x85, 0x86, 0x88, 0x89, 0x95, 0xA7, 0xA8, 0xAA, 0xAB, 0xAC, 0xAD, 0xAE, 0xAF})

function waitGhostHistogramScreenDisplayed(curSegmentIndex, curActionIndex, curState)
	return waitScreenDisplayed(curSegmentIndex, curActionIndex, curState, GHOST_HISTOGRAM_SCREEN_ID, MK_CHANNEL_LEADERBOARDS_MENU_ALLOWED_SCREEN_IDS)
end

local advanceToCharacterSelectSegment = {
	{waitCupSelectionScreenDisplayed, 15},
	{"B", 50},
	{"A", 80},
	{setChooseCupState, 0},
}

local chooseMushroomCupSegment = {
	{DETERMINE_CUP_MENU_POS, 0}
}

local chooseFlowerCupSegment = {
	{"right", 5},
	{DETERMINE_CUP_MENU_POS, 0}
}

local chooseStarCupSegment = {
	{"right", 5},
	{"right", 5},
	{DETERMINE_CUP_MENU_POS, 0}
}

local chooseSpecialCupSegment = {
	{"left", 5},
	{DETERMINE_CUP_MENU_POS, 0}
}

local chooseShellCupSegment = {
	{"down", 5},
	{DETERMINE_CUP_MENU_POS, 0}
}

local chooseBananaCupSegment = {
	{"down", 5},
	{"right", 5},
	{DETERMINE_CUP_MENU_POS, 0}
}

local chooseLeafCupSegment = {
	{"down", 5},
	{"right", 5},
	{"right", 5},
	{DETERMINE_CUP_MENU_POS, 0}
}

local chooseLightningCupSegment = {
	{"down", 5},
	{"left", 5},
	{DETERMINE_CUP_MENU_POS, 0}
}

local determineCupMenuPosSegment = {
	{"A", 25},
	{determineCupMenuPos, 0},
}

local chooseCupMenuPosDownSegment = {
	{"down", 5},
	{"down", 5},
	{CHOOSE_TRACK_PLAY_GHOST, 0}
}

local chooseCupMenuPosUpSegment = {
	{"up", 5},
	{CHOOSE_TRACK_PLAY_GHOST, 0}
}

local chooseTrackPlayGhostSegment = {
	{"A", 80},
	{determineIsComparison, 0}
}

local navigateToMainGhostSegment = {
	{navigateToMainGhost, 0}
}

local navigateTo2ndGhostSegment = {
	{"right", 15},
	{"down", 5},
	{ADV_LIVE_REPLAY_WATCH_REPLAY, 0}
}

local navigateTo3rdGhostSegment = {
	{"left", 15},
	{"down", 5},
	{ADV_LIVE_REPLAY_WATCH_REPLAY, 0}
}

local advLiveReplayWatchReplaySegment = {
	{"down", 5},
	{"A", 30},
	{"A", 10},
	{waitFrameOfInput0, 60},
	{"Start", 25},
	{"up", 5},
	{"A", 70},
	{"up", 5},
	{"A", 5},
	{waitCupSelectionScreenDisplayed, 20},
	{"A", 25},
	{"A", 80},
	{navigateToCompareGhost, 0}	
}

local navigateTo2ndGhost2Segment = {
	{"right", 15},
	{"down", 5},
	{ADV_LIVE_REPLAY_RACE_GHOST, 0}
}

local navigateTo3rdGhost2Segment = {
	{"left", 15},
	{"down", 5},
	{ADV_LIVE_REPLAY_RACE_GHOST, 0}
}

local advLiveReplayRaceGhostSegment = {
	{"none", 30},
	{ttGhostSelectOrGhostOnlyBranch, 0}
}

local navigateToMainGhostNoCompareSegment = {
	{navigateToMainGhostNoCompare, 0}
}

local navigateTo2ndGhostNoCompareSegment = {
	{"right", 15},
	{"down", 5},
	{ADV_LIVE_REPLAY_WATCH_REPLAY_NO_COMPARE, 0}
}

local advLiveReplayWatchReplayNoCompareSegment = {
	{"down", 5},
	{"A", 30},
	{"A", 10},
	{waitFrameOfInput0, 60},
	{"Start", 25},
	{"up", 5},
	{"A", 70},
	{"up", 5},
	{"A", 5},
	{waitCupSelectionScreenDisplayed, 20},
	{"A", 25},
	{"A", 80},
	{navigateToMainGhostSoloTimeTrial, 0}
}

local navigateTo2ndGhostNoCompare2Segment = {
	{"right", 15},
	{ADV_LIVE_REPLAY_SOLO_TIME_TRIAL, 0}
}

local advLiveReplaySoloTimeTrialSegment = {
	{"up", 30},
	{ttGhostSelectOrGhostOnlyBranch, 0}
}

local advLiveReplayTTGhostSelectCommonSegment = {
	{startDumpFramesForRecordFromTTGhostSelect, 0},
	{"none", 60},
	{"A", 30},
	{"A", 96},
	{stopDumpFramesForRecordFromTTGhostSelect, 0},
	{"none", 3},
	{renameTTGhostSelectDumpFiles, 3},
	{ADV_LIVE_REPLAY_COMMON, 0}
}

local advLiveReplayGhostOnlyCommonSegment = {
	{"A", 30},
	{"A", 10},
	{ADV_LIVE_REPLAY_COMMON, 0}
}

local advLiveReplayCommonSegment = {
	{waitFrameOfInput0, 0},
	{startDumpFramesForEncodeLuaModes, 0},
	{setFrameReplayStarts, 0},
	{setLastKCPValue, 0},
	{waitFrameOfInput1ThenSetFrameInputStarts, 0},
	{waitRaceCompletion, 60 * 10},
	{stopDumpFrames, 0},
	{"done", 0}
}

-- ###################################################
-- CUSTOM TOP 10
-- ###################################################

local doCustomTop10Segment = {
	{waitGhostHistogramScreenDisplayed, 300},
	{"A", 44},
	{startDumpFrames, 0},
	{"none", 240},
	{"B", 90},
	{"down", 27},
	{"A", 55},
	{stopDumpFrames, 0},
	{"done", 0}
}

local doMkChannelGhostScreenSegment = {
	{waitGhostHistogramScreenDisplayed, 100},
	{"A", 80},
	{"B", 31},
	{startDumpFrames, 0},
	{"none", 60},
	{"down", 27},
	{"A", 55},
	{stopDumpFrames, 0},
	{"done", 0}
}

local segments = {}

local recordGhostStandardSegments = {
	[ADVANCE_TO_TRACK_SELECT] = advanceToCharacterSelectSegment,
	[CHOOSE_MUSHROOM_CUP] = chooseMushroomCupSegment,
	[CHOOSE_FLOWER_CUP] = chooseFlowerCupSegment,
	[CHOOSE_STAR_CUP] = chooseStarCupSegment,
	[CHOOSE_SPECIAL_CUP] = chooseSpecialCupSegment,
	[CHOOSE_SHELL_CUP] = chooseShellCupSegment,
	[CHOOSE_BANANA_CUP] = chooseBananaCupSegment,
	[CHOOSE_LEAF_CUP] = chooseLeafCupSegment,
	[CHOOSE_LIGHTNING_CUP] = chooseLightningCupSegment,
	[DETERMINE_CUP_MENU_POS] = determineCupMenuPosSegment,
	[CHOOSE_CUP_MENU_POS_DOWN] = chooseCupMenuPosDownSegment,
	[CHOOSE_CUP_MENU_POS_UP] = chooseCupMenuPosUpSegment,
	[CHOOSE_TRACK_PLAY_GHOST] = chooseTrackPlayGhostSegment,
	[NAVIGATE_TO_MAIN_GHOST] = navigateToMainGhostSegment,
	[NAVIGATE_TO_2ND_GHOST] = navigateTo2ndGhostSegment,
	[NAVIGATE_TO_3RD_GHOST] = navigateTo3rdGhostSegment,
	[ADV_LIVE_REPLAY_WATCH_REPLAY] = advLiveReplayWatchReplaySegment,
	[NAVIGATE_TO_2ND_GHOST_2] = navigateTo2ndGhost2Segment,
	[NAVIGATE_TO_3RD_GHOST_2] = navigateTo3rdGhost2Segment,
	[ADV_LIVE_REPLAY_RACE_GHOST] = advLiveReplayRaceGhostSegment,

	[NAVIGATE_TO_MAIN_GHOST_NO_COMPARE] = navigateToMainGhostNoCompareSegment,
	[NAVIGATE_TO_2ND_GHOST_NO_COMPARE] = navigateTo2ndGhostNoCompareSegment,
	[ADV_LIVE_REPLAY_WATCH_REPLAY_NO_COMPARE] = advLiveReplayWatchReplayNoCompareSegment,
	[NAVIGATE_TO_2ND_GHOST_NO_COMPARE_2] = navigateTo2ndGhostNoCompare2Segment,
	[ADV_LIVE_REPLAY_SOLO_TIME_TRIAL] = advLiveReplaySoloTimeTrialSegment,
	[ADV_LIVE_REPLAY_TT_GHOST_SELECT_COMMON] = advLiveReplayTTGhostSelectCommonSegment,
	[ADV_LIVE_REPLAY_GHOST_ONLY_COMMON] = advLiveReplayGhostOnlyCommonSegment,
	[ADV_LIVE_REPLAY_COMMON] = advLiveReplayCommonSegment
}

local recordTop10Segments = {
	[DO_CUSTOM_TOP_10] = doCustomTop10Segment
}

local recordMkChannelGhostScreenSegments = {
	[DO_MK_CHANNEL_GHOST_SCREEN] = doMkChannelGhostScreenSegment
}

function initializeSegmentTable(mode)
	if mode == LUA_MODE_RECORD_TOP_10 then
		segments = recordTop10Segments
	elseif mode == LUA_MODE_RECORD_MK_CHANNEL_GHOST_SCREEN then
		segments = recordMkChannelGhostScreenSegments
	else
		segments = recordGhostStandardSegments
	end

	for i, segment in ipairs(segments) do
		for i, action in ipairs(segment) do
			segment[i] = {
				command = action[1],
				delay = action[2]
			}
		end
	end
end

function readInParams()
	file = io.open("lua_config.txt", "r")
	for line in file:lines() do
		if line ~= "\n" and line ~= "" and line ~= "\r\n" then
			index, value = line:match("([^:]+): *([^:]+)")
			params[index] = value
		end
	end
	file:close()
end

function initializePlayGhost()
	readInParams()
	params["mode"] = tonumber(params["mode"])
	initializeSegmentTable(params["mode"])
end

function writeOutputParams()
	output = ""
	for k, v in pairs(outputParams) do
		output = output .. k .. ": " .. v .. "\n"
	end

	file = io.open("output_params.txt", "w")
	file:write(output)
	file:close()
end

pressButtonCommands = {
	["A"] = true,
	["B"] = true,
	["Start"] = true
}

function onScriptCancel()
	SetScreenText("")
end

local permaText = ""
local pressedButton = ""
local entryCount = 0
local curEntryIndex = 1
local prevFrame = -1

function onScriptUpdate()
	if not helper_isScriptEnabled then
		CancelScript()
		SetScreenText("")
		return
	end

	if LuaNotEnoughGeckoCodeSpace() then
		file = io.open("status.txt", "w")
		file:write("Not enough space for all loaded gecko codes! Try changing some settings around.")
		file:close()
		CancelScript()
		ExitDolphin()
		return
	end

	local text = ""
	local frame = GetFrameCount()
	local isDifferentFrame = false

	if prevFrame ~= frame then
		curSegmentIndexG = curSegmentIndexForNextFrame
		curActionIndexG = curActionIndexForNextFrame
		curStateG = curStateForNextFrame
		delayEndFrameCountG = delayEndFrameCountForNextFrame
		cursorSetManuallyG = cursorSetManuallyForNextFrame
		glitchDetectionStateG = glitchDetectionStateForNextFrame
		curLapOnPrevFrameG = curLapOnPrevFrameForNextFrame
		curKCPOnPrevFrameG = curKCPOnPrevFrameForNextFrame
		curLapOnKCP0EntryG = curLapOnKCP0EntryForNextFrame
		isDifferentFrame = true
	end
	prevFrame = frame

	local curSegmentIndex = curSegmentIndexG
	local curActionIndex = curActionIndexG
	local curState = curStateG
	local delayEndFrameCount = delayEndFrameCountG
	local cursorSetManually = cursorSetManuallyG
	local glitchDetectionState = glitchDetectionStateG
	local curLapOnPrevFrame = curLapOnPrevFrameG
	local curKCPOnPrevFrame = curKCPOnPrevFrameG
	local curLapOnKCP0Entry = curLapOnKCP0EntryG

	entryCount = entryCount + 1
	text = text .. string.format("Frame: %d, entryCount: %d\n", frame, entryCount)
	text = text .. string.format("cursorSetManually: %s\n", cursorSetManually)
	text = text .. string.format("\nRunning Play Ghost!\n")

	if curState == IN_DELAY then
		if frame >= delayEndFrameCount then
			if not cursorSetManually then
				curSegment = segments[curSegmentIndex]
				curActionIndex = curActionIndex + 1
				if curActionIndex > #curSegment then
					curSegmentIndex = curSegmentIndex + 1
					if curSegmentIndex == CHOOSE_FLOWER_CUP then
						triggeredFlowerCupText = string.format("Triggered flower cup! frame: %d\n", frame)
					end

					curActionIndex = 1
				end
			end
			curState = EXECUTING_ACTION
			text = text .. "\n"
		else
			text = text .. "Waiting until frame " .. delayEndFrameCount .. "!\n"
		end
	end

	local failsafeCount = 0

	while curState == EXECUTING_ACTION do
		local curSegment = segments[curSegmentIndex]
		curAction = curSegment[curActionIndex]
		if type(curAction.command) == "string" then
			if pressButtonCommands[curAction.command] then
				PressButton(curAction.command)
			elseif curAction.command == "up" then
				SetMainStickY(255)
			elseif curAction.command == "down" then
				SetMainStickY(0)
			elseif curAction.command == "left" then
				SetMainStickX(0)
			elseif curAction.command == "right" then
				SetMainStickX(255)
			elseif curAction.command == "done" then
				outputParams["frameEnded"] = GetFrameCount()
				writeOutputParams()
				file = io.open("status.txt", "w")
				file:close()
				CancelScript()
				ExitDolphin()
				return
			end
			curState = IN_DELAY
			cursorSetManually = false
			delayEndFrameCount = frame + curAction.delay
		elseif type(curAction.command) == "function" then
			curSegmentIndex, curActionIndex, curState = curAction.command(curSegmentIndex, curActionIndex, curState)
			cursorSetManually = true
			if curState == IN_DELAY then
				delayEndFrameCount = frame + curAction.delay
			elseif curState == EXIT_LOOP_NO_DELAY then
				curState = EXECUTING_ACTION
				break
			end
		elseif type(curAction.command) == "number" then
			curSegmentIndex = curAction.command
			curActionIndex = 1
			cursorSetManually = true
			if curAction.delay ~= 0 then
				curState = IN_DELAY
				delayEndFrameCount = frame + curAction.delay
			end
		end
		failsafeCount = failsafeCount + 1
		if failsafeCount == 101 then
			error(string.format("Infinite loop detected! curSegmentIndex: %d, curActionIndex: %d, curState: %d", curSegmentIndex, curActionIndex, curState))
		end
	end

	local frameOfInput = core.getFrameOfInput()
	if frameOfInput > 22000 and frameOfInput < 22100 then
		error("Run did not terminate within ~6 minutes!")
	end

-- if state == 0:
--   check if in KCP Last, prev KCP is KCP0, kcp0Lap is curLap, and curLap is prevCurLap
--     set state 1
-- elif state == 1:
--   check if in KCP0, and curLap is kcp0Lap + 1
--     isUltra is true
--     set state 2
-- 
-- if state != 2:
--   if prevKCP != curKCP and curKCP is KCP0:
--     kcp0Lap = curLap

	if type(curAction.command) == "function" and curAction.command == waitRaceCompletion then
		local curKCP = core.getCurKeyCheckpoint()
		local curLap = core.getCurrentLap()
		if glitchDetectionState == WAITING_FOR_KCP0_TO_KCP_LAST then
			if curKCP > 1 and curKCPOnPrevFrame == 0 then
				if curLapOnKCP0Entry == curLap and curLap == curLapOnPrevFrame then
					glitchDetectionState = WAITING_FOR_KCP_LAST_TO_KCP0
				elseif curLap + 1 == curLapOnPrevFrame then
					if curState == IN_DELAY then
						outputParams["isL495Rule"] = "true"
						detectedL495RuleText = "Detected 95% Rule After Race!\n"
					else
						outputParams["is95Rule"] = "true"
						detected95RuleText = "Detected 95% Rule!\n"						
					end
				end
			end
		elseif glitchDetectionState == WAITING_FOR_KCP_LAST_TO_KCP0 then
			if curKCP == 0 then
				if curLap == curLapOnKCP0Entry + 1 then
					if curState == IN_DELAY and core.getRaceCompletion() > tonumber(params["lapCount"]) + 2 then
						outputParams["isL4Ultra"] = "true"
						detectedL4UltraText = "Detected Ultra Shortcut After Race!\n"
						glitchDetectionState = DETECTED_ULTRA
					else
						outputParams["isUltra"] = "true"
						detectedUltraText = "Detected Ultra Shortcut!\n"
						glitchDetectionState = DETECTED_ULTRA
					end
				else
					if curState == IN_DELAY then
						outputParams["isL4Reverse95Rule"] = "true"
						detectedL4Reverse95RuleText = "Detected Reverse 95% Rule After Race!\n"
						glitchDetectionState = WAITING_FOR_KCP0_TO_KCP_LAST
					else
						outputParams["isReverse95Rule"] = "true"
						detectedReverse95RuleText = "Detected Reverse 95% Rule!\n"
						glitchDetectionState = WAITING_FOR_KCP0_TO_KCP_LAST
					end
				end
			end
		end

		if glitchDetectionState ~= DETECTED_ULTRA then
			if (curKCPOnPrevFrame ~= curKCP and curKCP == 0) or (curKCP == 0 and curLap == curLapOnPrevFrame + 1) then
				curLapOnKCP0Entry = curLap
			end
		end

		curKCPOnPrevFrame = curKCP
		curLapOnPrevFrame = curLap
	end

	--curAction = segments[curSegmentIndex][curActionIndex]
	--permaText = string.format("type(curAction.command): %s, curAction.command: %s\n", type(curAction.command), curAction.command)
	--permaText = permaText .. string.format("curActionIndex: %d\n", curActionIndex)
	--if pressedButton ~= "" then
	--	permaText = permaText .. pressedButton
	--end

	curSegmentIndexForNextFrame = curSegmentIndex
	curActionIndexForNextFrame = curActionIndex
	curStateForNextFrame = curState
	delayEndFrameCountForNextFrame = delayEndFrameCount
	cursorSetManuallyForNextFrame = cursorSetManually
	glitchDetectionStateForNextFrame = glitchDetectionState
	curLapOnPrevFrameForNextFrame = curLapOnPrevFrame
	curKCPOnPrevFrameForNextFrame = curKCPOnPrevFrame
	curLapOnKCP0EntryForNextFrame = curLapOnKCP0Entry

	frameOfInputText = "frameOfInput: " .. core.getFrameOfInput() .. "\n"
	if outputParams["frameRecordingStarts"] ~= nil then
		recordingStartedText = "Recording started at " .. outputParams["frameRecordingStarts"] .. "\n"
	else
		recordingStartedText = "\n"
	end

	lastPtsText = "lastPts: " .. GetAVIDumpLastPts() .. ", refreshRate: " .. GetTargetRefreshRate() .. ", aviDumpLastFrame: " .. GetAVIDumpLastFrame() .. "\n"

	local checkpointInfoText = ""
	checkpointInfoText = checkpointInfoText .. string.format("CP: %d, KCP: %d, Max KCP: %d, Lap: %d\n", core.getCurCheckpoint(), core.getCurKeyCheckpoint(), core.getMaxKeyCheckpoint(), core.getCurrentLap())
	checkpointInfoText = checkpointInfoText .. string.format("Lap Completion: %6.6f, Lap Completion Max: %6.6f\nRace Completion: %6.6f\n", core.getLapCompletion(), core.getLapCompletionMax(), core.getRaceCompletion())
	checkpointInfoText = checkpointInfoText .. string.format("lastKCP: %d, kcp0Lap: %d, glitchState: %d\n", lastKCP, curLapOnKCP0Entry, glitchDetectionState)

	text = text .. cupDebugText .. triggeredFlowerCupText .. frameOfInputText .. recordingStartedText .. lastPtsText .. checkpointInfoText .. detectedUltraText .. detected95RuleText .. detectedReverse95RuleText .. detectedL4UltraText .. detectedL495RuleText .. detectedL4Reverse95RuleText
	SetScreenText(text)
end

function onStateLoaded()

end

function onStateSaved()

end
