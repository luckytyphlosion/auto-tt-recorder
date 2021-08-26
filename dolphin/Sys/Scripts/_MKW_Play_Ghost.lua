----- GLOBAL VARIABLES -----
package.path = GetScriptsDir() .. "MKW/MKW_core.lua"
local core = require("MKW_core")
--Add an underscore (_) to the beginning of the filename if you want the script to auto launch once you start a game!

function onScriptStart()
	if GetGameID() ~= "RMCP01" and GetGameID() ~= "RMCJ01" and GetGameID() ~= "RMCE01" and GetGameID() ~= "RMCK01" then
		SetScreenText("")
		CancelScript()
	end
	--SetScreenText(GetGameID())
	initializePlayGhost()
end

local advanceToCharacterSelectSegment = {
	{"none", 70},
	{"A", 230},
	{"A", 50},
	{"A", 75},
	{"A", 350},
	{"down", 25},
	{"A", 25},
	{"done", 0},
}

local ADVANCE_TO_TRACK_SELECT = 1
local CHOOSE_TRACK = 2

local EXECUTING_ACTION = 1
local IN_DELAY = 2

local segments = {
	[ADVANCE_TO_TRACK_SELECT] = advanceToCharacterSelectSegment
}

local curSegmentIndexG = ADVANCE_TO_TRACK_SELECT
local curActionIndexG = 1
local curStateG = EXECUTING_ACTION
local delayEndFrameCountG = 0

local curSegmentIndexForNextFrame = ADVANCE_TO_TRACK_SELECT
local curActionIndexForNextFrame = 1
local curStateForNextFrame = EXECUTING_ACTION
local delayEndFrameCountForNextFrame = 0


function initializeSegmentTable()
	for i, segment in ipairs(segments) do
		for i, action in ipairs(segment) do
			segment[i] = {
				command = action[1],
				delay = action[2]
			}
		end
	end
end

function initializePlayGhost()
	initializeSegmentTable()
end

pressButtonCommands = {
	["A"] = true,
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
	local text = ""
	local frame = GetFrameCount()

	if prevFrame ~= frame then
		curSegmentIndexG = curSegmentIndexForNextFrame
		curActionIndexG = curActionIndexForNextFrame
		curStateG = curStateForNextFrame
		delayEndFrameCountG = delayEndFrameCountForNextFrame
	end
	prevFrame = frame

	local curSegmentIndex = curSegmentIndexG
	local curActionIndex = curActionIndexG
	local curState = curStateG
	local delayEndFrameCount = delayEndFrameCountG

	entryCount = entryCount + 1
	text = text .. string.format("\n\n\n\n\n\nFrame: %d, entryCount: %d\n", frame, entryCount)
	text = text .. string.format("\nRunning Play Ghost!\n")

	if curState == IN_DELAY then
		if frame >= delayEndFrameCount then
			curSegment = segments[curSegmentIndex]
			curActionIndex = curActionIndex + 1
			if curActionIndex > #curSegment then
				curSegmentIndex = curSegmentIndex + 1
				curActionIndex = 1
			end
			curState = EXECUTING_ACTION
		else
			text = text .. "Waiting until frame " .. delayEndFrameCount .. "!\n"
		end
	end

	if curState == EXECUTING_ACTION then
		curAction = segments[curSegmentIndex][curActionIndex]
		if type(curAction.command) == "string" then
			if pressButtonCommands[curAction.command] == true then
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
				CancelScript()
			end
		end
		curState = IN_DELAY
		delayEndFrameCount = frame + curAction.delay
	end

	curAction = segments[curSegmentIndex][curActionIndex]
	--permaText = string.format("type(curAction.command): %s, curAction.command: %s\n", type(curAction.command), curAction.command)
	--permaText = permaText .. string.format("curActionIndex: %d\n", curActionIndex)
	--if pressedButton ~= "" then
	--	permaText = permaText .. pressedButton
	--end

	curSegmentIndexForNextFrame = curSegmentIndex
	curActionIndexForNextFrame = curActionIndex
	curStateForNextFrame = curState
	delayEndFrameCountForNextFrame = delayEndFrameCount

	text = text -- .. "\n" .. permaText
	SetScreenText(text)
end

function onStateLoaded()

end

function onStateSaved()

end
