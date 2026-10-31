param([Parameter(Mandatory=$true)][string]$Folder,[Parameter(Mandatory=$true)][string]$ReportPath)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PaperCloudState {
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)]
 public struct FindData {
  public uint Attributes;
  public System.Runtime.InteropServices.ComTypes.FILETIME Creation,Access,Write;
  public uint SizeHigh,SizeLow,ReparseTag,Reserved;
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=260)] public string Name;
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=14)] public string Alternate;
 }
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 public static extern IntPtr FindFirstFile(string path,out FindData data);
 [DllImport("kernel32.dll")] public static extern bool FindClose(IntPtr handle);
 [DllImport("cldapi.dll")] public static extern uint CfGetPlaceholderStateFromAttributeTag(uint attributes,uint reparseTag);
}
'@
$rows=@(Get-ChildItem -LiteralPath $Folder -File | ForEach-Object {
 $data=New-Object PaperCloudState+FindData
 $handle=[PaperCloudState]::FindFirstFile($_.FullName,[ref]$data)
 if ($handle -eq [IntPtr](-1)) { throw 'Cannot inspect file state' }
 try { $state=[PaperCloudState]::CfGetPlaceholderStateFromAttributeTag($data.Attributes,$data.ReparseTag) }
 finally { [void][PaperCloudState]::FindClose($handle) }
 @{name=$_.Name;attributes=$data.Attributes;reparse_tag=$data.ReparseTag;cloud_placeholder_state=$state;
   in_sync=($state -ne [uint32]::MaxValue -and ($state -band 8) -eq 8);
   sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length}
})
$result=@{observed_utc=[DateTime]::UtcNow.ToString('o');folder=$Folder;files=$rows;
 all_client_reported_in_sync=($rows.Count -gt 0 -and @($rows | Where-Object {-not $_.in_sync}).Count -eq 0);
 scope='Windows Cloud Files API reports provider IN_SYNC; hashes verify local bytes. This is client-reported cloud synchronization, not an independent server download.'}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
$result | ConvertTo-Json -Depth 5
