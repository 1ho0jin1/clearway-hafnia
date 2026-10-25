<#
start_smartclient.ps1 - start XProtect Smart Client as a normal, non-elevated user (Medium integrity).

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_smartclient.ps1

On the hackathon machines everyone works as the built-in Administrator, whose programs all run elevated. Smart
Client's HTML page item (plugin VideoOS.RemoteClient.Plugin.HtmlViewItem) shows standard display mode with the legacy
Edge engine (EdgeHTML, the Windows Community Toolkit's WebViewCompatible), refuses it in elevated processes ("when you
run XProtect Smart Client as administrator, the webpage cannot be loaded using Standard display mode") and falls back
to Internet Explorer in IE 7 mode. runas /trustlevel:0x20000 removes the Administrators group but leaves High
integrity; this script takes that Basic User token, lowers it to Medium integrity (allowed for one's own token) and
starts Smart Client with it: nothing on the system changes.
Result on this Windows Server 2022 machine (2026-10-25): Smart Client ran at Medium integrity, and the HTML page item
still fell back to Internet Explorer with either rendering-engine value, so the Clearway board opens in its own window
(scripts\open_board.ps1). Kept for anything else that needs Smart Client not elevated.
#>
$ErrorActionPreference = 'Stop'
$Client = 'C:\Program Files\Milestone\XProtect Smart Client\Client.exe'
if (-not (Test-Path $Client)) { throw "Smart Client not found at ${Client}" }
if (Get-Process Client -ErrorAction SilentlyContinue | Where-Object Path -eq $Client) {
    Write-Host 'Smart Client is already running: close it first, then run this again.'
    exit 1
}
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class MediumIntegrity {
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool SaferCreateLevel(uint scope, uint level, uint flags, out IntPtr handle, IntPtr reserved);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool SaferComputeTokenFromLevel(IntPtr level, IntPtr inToken, out IntPtr outToken, uint flags, IntPtr reserved);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool SaferCloseLevel(IntPtr level);
    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)] static extern bool ConvertStringSidToSid(string sid, out IntPtr psid);
    [DllImport("advapi32.dll")] static extern int GetLengthSid(IntPtr psid);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool SetTokenInformation(IntPtr token, int infoClass, ref TOKEN_MANDATORY_LABEL info, int length);
    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)] static extern bool CreateProcessAsUser(IntPtr token, string app, string cmd, IntPtr pa, IntPtr ta, bool inherit, uint flags, IntPtr env, string dir, ref STARTUPINFO si, out PROCESS_INFORMATION pi);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr h);
    [StructLayout(LayoutKind.Sequential)] struct SID_AND_ATTRIBUTES { public IntPtr Sid; public uint Attributes; }
    [StructLayout(LayoutKind.Sequential)] struct TOKEN_MANDATORY_LABEL { public SID_AND_ATTRIBUTES Label; }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] struct STARTUPINFO {
        public int cb; public string lpReserved; public string lpDesktop; public string lpTitle;
        public int dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute, dwFlags;
        public short wShowWindow, cbReserved2; public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError; }
    [StructLayout(LayoutKind.Sequential)] struct PROCESS_INFORMATION { public IntPtr hProcess, hThread; public int dwProcessId, dwThreadId; }

    // The Basic User token of runas /trustlevel:0x20000 (Administrators group deny-only), lowered to Medium integrity.
    public static int Start(string app, string commandLine, string dir) {
        IntPtr level, token, sid;
        if (!SaferCreateLevel(2 /* user scope */, 0x20000 /* normal user */, 1 /* open */, out level, IntPtr.Zero)) throw new Win32Exception();
        try { if (!SaferComputeTokenFromLevel(level, IntPtr.Zero, out token, 0, IntPtr.Zero)) throw new Win32Exception(); }
        finally { SaferCloseLevel(level); }
        try {
            if (!ConvertStringSidToSid("S-1-16-8192" /* Medium */, out sid)) throw new Win32Exception();
            try {
                var label = new TOKEN_MANDATORY_LABEL();
                label.Label.Sid = sid; label.Label.Attributes = 0x20; // SE_GROUP_INTEGRITY
                if (!SetTokenInformation(token, 25 /* TokenIntegrityLevel */, ref label, Marshal.SizeOf(label) + GetLengthSid(sid))) throw new Win32Exception();
            } finally { LocalFree(sid); }
            var si = new STARTUPINFO(); si.cb = Marshal.SizeOf(si); si.lpDesktop = @"winsta0\default";
            PROCESS_INFORMATION pi;
            if (!CreateProcessAsUser(token, app, commandLine, IntPtr.Zero, IntPtr.Zero, false, 0, IntPtr.Zero, dir, ref si, out pi)) throw new Win32Exception();
            CloseHandle(pi.hThread); CloseHandle(pi.hProcess);
            return pi.dwProcessId;
        } finally { CloseHandle(token); }
    }
}
'@
$id = [MediumIntegrity]::Start($Client, "`"$Client`"", (Split-Path $Client))
Write-Host "started: XProtect Smart Client, not elevated (Medium integrity), pid $id"
