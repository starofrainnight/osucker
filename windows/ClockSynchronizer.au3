#NoTrayIcon
#Region ;**** Directives created by AutoIt3Wrapper_GUI ****
#AutoIt3Wrapper_Change2CUI=y
#EndRegion ;**** Directives created by AutoIt3Wrapper_GUI ****
#include <Date.au3>

;
; A script that synchrone system's time with ntp servers
;
; Why we need this ? Windows already synchrone from their ntp server regularly.
; But they only synchrone time when there does not much difference between
; system time and ntp server obtained time. Motherboard's BIOS time will reset
; to production date if your PC's RTC battery exhausted. Then when you boot to
; windows, the system time is huge different with the real time, so that would
; broken some softwares that depends on current correct time, just like the
; website's ssl verification.
;
; So we wrote a script by AutoIt3 to synchrone system time through ntp server.
; And install as windows's service by `NSSM <https://nssm.cc>`_
;
; It will try 15 minutes to synchrone time with NTP servers and exit if
; successed when system boot up.

;Variables
Global $NTP_Server[4] = ['0.cn.pool.ntp.org','1.cn.pool.ntp.org','2.cn.pool.ntp.org','3.cn.pool.ntp.org'], $NTP_IP[4], $NTPIP[4]
Main()
Exit
Func Main()
	Dim $Ret
	For $i = 0 To 15
		$Ret = SyncSystemTimeThroughNTP()
		If $Ret Then
			ExitLoop
		EndIf
		ConsoleWrite($i & ": Failed to sync time through NTP server! Try again!" & @CRLF)
		Sleep(60 * 1000)
	Next
EndFunc
Func SyncSystemTimeThroughNTP()
	;main program
	Local $NTP_IP = Call('check_internet_connectivity')
	If 	$NTP_IP[0] <> '' Then
		$adata = call('NTP_Connect', $NTP_Server[0])
	ElseIf $NTP_IP[1] <> '' Then
		$adata = call('NTP_Connect', $NTP_Server[1])
	ElseIf $NTP_IP[2] <> '' Then
		$adata = call('NTP_Connect', $NTP_Server[2])
	ElseIf $NTP_IP[3] <> '' Then
		$adata = call('NTP_Connect', $NTP_Server[3])
	Else
		Return False
	EndIf
	If StringLen(StringStripWS($adata, 8)) > 0 Then
		ConsoleWrite("Setting system's time..." & @CRLF)
		Call('Set_Time', $adata)
		Return True
	EndIf
	Return False
EndFunc

;Function to check wich/if servers if you are available to avoid UDP blockage.
Func check_internet_connectivity()
	TCPStartup()
	For $i = 0 to 3
		$NTPIP[$i] = TCPNameToIP ( $NTP_Server[$i])
		Sleep(250)
	Next
	TCPShutdown ()
	Return $NTPIP
EndFunc

;Function to read time from ntp server.
Func NTP_Connect($NTP_Server)
	ConsoleWrite("Connecting to " & $NTP_Server & "..." & @CRLF)
	UDPStartup()
	Dim $socket = UDPOpen(TCPNameToIP($NTP_Server), 123)
	Dim $TimeoutLimit = 30 * 1000
	Dim $ElapsedTime = 0
	Dim $SleepTime = 100
	Dim $data = ""
	$status = UDPSend($socket, MakePacket("1b0e01000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"))
	While $data = ""
		$data = UDPRecv($socket, 100)
		Sleep($SleepTime)
		$ElapsedTime = $ElapsedTime + $SleepTime
		If $ElapsedTime > $TimeoutLimit Then
			ConsoleWrite("UDP Receive Timeout!" & @CRLF)
			ExitLoop
		EndIf
	WEnd
	UDPCloseSocket($socket)
	UDPShutdown()
	Return $data
EndFunc

;Function to decript the time and apply to system
Func Set_Time($bdata)
	$unsignedHexValue = StringMid($bdata, 83, 8); Extract time from packet. Disregards the fractional second.
	$value = UnsignedHexToDec($unsignedHexValue)
	$TZinfo = _Date_Time_GetTimeZoneInformation()
	$UTC = _DateAdd("s", $value, "1900/01/01 00:00:00")
	If 	$TZinfo[0] <> 2 Then ; 0 = Daylight Savings not used in current time zone / 1 = Standard Time
		$TZoffset = ($TZinfo[1]) * - 1
		Else ; 2 = Daylight Savings Time
		$TZoffset = ($TZinfo[1] + $TZinfo[7]) * - 1
	EndIf

	;~ Extracts the data & time into vars
	;~ Date format & offsets
	;~ 2009/12/31 19:26:05
	;~ 1234567890123456789  [1 is start of string]
	$m = StringMid($UTC, 6, 2)
	$d = StringMid($UTC, 9, 2)
	$y = StringMid($UTC, 1, 4)
	$h = StringMid($UTC, 12, 2)
	$mi = StringMid($UTC, 15, 2)
	$s = StringMid($UTC, 18, 2)

	;~ Sets the new current time to the computer
	$tCurr = _Date_Time_EncodeSystemTime($m, $d, $y, $h, $mi, $s)
	_Date_Time_SetSystemTime(DllStructGetPtr($tCurr))
EndFunc

;Function to send packet to ntp server
Func MakePacket($d)
    Local $p = ""
    While $d
        $p &= Chr(Dec(StringLeft($d, 2)))
        $d = StringTrimLeft($d, 2)
    WEnd
    Return $p
EndFunc

;Function to decript UnsignedHexToDec
Func UnsignedHexToDec($n)
    $ones = StringRight($n, 1)
    $n = StringTrimRight($n, 1)
    Return Dec($n) * 16 + Dec($ones)
EndFunc
