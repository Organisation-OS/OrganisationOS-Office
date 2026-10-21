# Read-only preflight. Does not install tools, fetch sources, change PATH or start a build.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$QtRoot,[Parameter(Mandatory=$true)][string]$BuildRoot,[Parameter(Mandatory=$true)][string]$CefArchive,[Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$CefSha256)
$ErrorActionPreference='Stop'
if (-not [Environment]::Is64BitOperatingSystem -or $env:OS -ne 'Windows_NT') { throw 'Builder Windows x64 requis.' }
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $vswhere)) { throw 'vswhere.exe absent.' }
$vs=@(& $vswhere -products '*' -version '[16.0,17.0)' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -format json | ConvertFrom-Json)
if ($vs.Count -ne 1) { throw 'Une installation Visual Studio 2019 avec outils MSVC x64 doit être désignée sans ambiguïté.' }
$vcvars=Join-Path $vs[0].installationPath 'VC\Auxiliary\Build\vcvarsall.bat'
$qmake=Join-Path $QtRoot 'bin\qmake.exe'
$deploy=Join-Path $QtRoot 'bin\windeployqt.exe'
foreach($file in @($vcvars,$qmake,$deploy,$CefArchive)) { if(-not(Test-Path -LiteralPath $file -PathType Leaf)){throw 'Prérequis absent.'} }
if((Get-FileHash -LiteralPath $CefArchive -Algorithm SHA256).Hash -ine $CefSha256){throw 'Archive CEF différente de la fermeture approuvée.'}
$drive=[IO.DriveInfo]::new([IO.Path]::GetPathRoot([IO.Path]::GetFullPath($BuildRoot)))
# Planning allowance for this fork, not a published upstream minimum.
if($drive.AvailableFreeSpace -lt 150GB){throw 'Prévoir 150 Gio libres sur le builder dédié, dont 40 Gio de réserve opérationnelle.'}
$tools=@{}
foreach($tool in @('git','python','node','npm','7z','iscc')) {
 $command=Get-Command $tool -ErrorAction Stop
 $tools[$tool]=@{Path=$command.Source;SHA256=(Get-FileHash -LiteralPath $command.Source -Algorithm SHA256).Hash;FileVersion=(Get-Item -LiteralPath $command.Source).VersionInfo.FileVersion}
}
[pscustomobject]@{
 Schema='oos-office-desktop-builder-preflight-v1';ReadOnly=$true;BuildStarted=$false
 Architecture='Windows-x64';VisualStudio=$vs[0].installationVersion;VcvarsallSHA256=(Get-FileHash -LiteralPath $vcvars -Algorithm SHA256).Hash
 QtVersion=(& $qmake -query QT_VERSION);QtSpec=(& $qmake -query QMAKE_SPEC);QtQmakeSHA256=(Get-FileHash -LiteralPath $qmake -Algorithm SHA256).Hash
 WindowsSdkVersions=@(Get-ChildItem -LiteralPath "${env:ProgramFiles(x86)}\Windows Kits\10\Include" -Directory | Select-Object -ExpandProperty Name)
 CefSHA256=$CefSha256.ToLowerInvariant();FreeBytes=$drive.AvailableFreeSpace;Tools=$tools
 Remaining='Épingler les versions exactes Qt/SDK/Node/Inno et leurs sources, recevoir le compilateur x64 et la fermeture tierce avant make.py.'
} | ConvertTo-Json -Depth 6
