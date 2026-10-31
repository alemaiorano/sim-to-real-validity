param(
    [Parameter(Mandatory=$true)][string]$SourceArchive,
    [Parameter(Mandatory=$true)][string]$DestinationDirectory,
    [Parameter(Mandatory=$true)][string]$ExpectedSha256,
    [Parameter(Mandatory=$true)][string]$ReportPath
)
# Seal one NEW version only. No inherited policy outside this directory changes.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
if (Test-Path -LiteralPath $DestinationDirectory) { throw 'Destination must be new' }
if ((Get-FileHash -LiteralPath $SourceArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedSha256) { throw 'Wrong source archive' }
New-Item -ItemType Directory -Path $DestinationDirectory | Out-Null
$copy = Join-Path $DestinationDirectory ([IO.Path]::GetFileName($SourceArchive))
Copy-Item -LiteralPath $SourceArchive -Destination $copy
if ((Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedSha256) { throw 'Copy differs' }
$sentinel = Join-Path $DestinationDirectory 'deletion-sentinel.txt'
[IO.File]::WriteAllText($sentinel, 'Disposable probe; never attempt deletion of scientific data.')
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$rights = [Security.AccessControl.FileSystemRights]::Delete -bor [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles -bor [Security.AccessControl.FileSystemRights]::Write
$inherit = [Security.AccessControl.InheritanceFlags]::ObjectInherit -bor [Security.AccessControl.InheritanceFlags]::ContainerInherit
$rule = [Security.AccessControl.FileSystemAccessRule]::new($sid, $rights, $inherit, [Security.AccessControl.PropagationFlags]::None, [Security.AccessControl.AccessControlType]::Deny)
$acl = Get-Acl -LiteralPath $DestinationDirectory
$acl.SetAccessRuleProtection($true, $true)
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $DestinationDirectory -AclObject $acl
$deleteDenied = $false
try { [IO.File]::Delete($sentinel) }
catch [UnauthorizedAccessException] { $deleteDenied = $true }
$writeDenied = $false
try { [IO.File]::WriteAllText($sentinel, 'probe overwrite') }
catch [UnauthorizedAccessException] { $writeDenied = $true }
if (-not $deleteDenied -or -not $writeDenied -or -not (Test-Path -LiteralPath $sentinel)) { throw 'Deletion/write guard failed' }
if ((Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedSha256) { throw 'Sealed archive differs' }
$result = @{
    archive=$copy; sha256=$ExpectedSha256; sid=$sid.Value;
    delete_sentinel_denied=$deleteDenied; overwrite_sentinel_denied=$writeDenied;
    sddl=(Get-Acl -LiteralPath $DestinationDirectory).Sddl;
    scope='Current Windows user ordinary deletion/overwrite; owner can deliberately change ACL; not offsite or disk-failure protection'
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
$result | ConvertTo-Json -Depth 4
