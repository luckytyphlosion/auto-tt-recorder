----- GLOBAL VARIABLES -----
package.path = GetScriptsDir() .. "MKW/MKW_core.lua"
local core = require("MKW_core")
--Add an underscore (_) to the beginning of the filename if you want the script to auto launch once you start a game!

function onScriptStart()
	if GetGameID() ~= "RMCP01" and GetGameID() ~= "RMCJ01" and GetGameID() ~= "RMCE01" and GetGameID() ~= "RMCK01" then
		SetScreenText("")
		CancelScript()
	end
end

function onScriptCancel()
	SetScreenText("")
end

local actions = {
	{
		frame = 100,
		action = "A",
	},
	{
		frame = 400,
		action = "A"
	},
	{
		frame = 550,
		action = "A"
	},
	{
		frame = 600,
		action = "A"
	},
	{
		frame = 675,
		action = "A"
	},
	{
		frame = 1025,
		action = "A"
	},
	{
		frame = 1050,
		action = "A",
	},
	{
		frame = 1051,
		action = "done"
	}
};

local ADVANCE_TO_TRACK_SELECT = 0
local CHOOSE_TRACK = 1
--local 

function onScriptUpdate()
	CancelScript()
	if true then
		return
	end

	local text = ""
	local frame = GetFrameCount()
	text = text .. string.format("\nFrame: %d\n", frame)
	text = text .. string.format("\nRunning Play Ghost!\n")
	SetScreenText(text)
	
	if frame == 100 then
		PressButton("A")
		SetFrameAndAudioDump(true)
	elseif frame == 400 then
		PressButton("A")
	elseif frame == 550 then
		PressButton("A")
	elseif frame == 600 then
		PressButton("A")
	elseif frame == 675 then
		PressButton("A")
	elseif frame == 1025 then
		SetMainStickY(0)
	elseif frame == 1050 then
		PressButton("A")
		SetFrameAndAudioDump(false)
	elseif frame == 1051 then
		file = io.open("kill.txt", "w")
		file:close()
	end
end

function onStateLoaded()

end

function onStateSaved()

end
