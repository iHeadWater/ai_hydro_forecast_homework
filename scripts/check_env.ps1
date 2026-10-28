# Read-only Windows environment doctor for the songliao homework.
# This wrapper never installs packages, never writes files, never changes
# ExecutionPolicy, and never modifies user/system environment variables.
#
# Usage (from the repository root):
#   powershell -NoProfile -File scripts\check_env.ps1
#   .\scripts\check_env.ps1
#
# Extra arguments are forwarded to scripts/check_env.py.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

function Write-DoctorLine {
    param(
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Message,
        [string]$Fix = ""
    )
    Write-Host ("  [{0}] {1}" -f $Status, $Message)
    if ($Fix) {
        Write-Host ("          -> {0}" -f $Fix)
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$PythonDoctor = Join-Path $ScriptDir "check_env.py"

Write-Host "Songliao Windows 预检（只读，不会改系统）"
Write-Host ("=" * 72)
Write-Host ("仓库根目录 : {0}" -f $RepoRoot)
Write-Host ("PowerShell : {0}" -f $PSVersionTable.PSVersion)
Write-Host ("当前目录   : {0}" -f (Get-Location).Path)

$consoleEncoding = [Console]::OutputEncoding
if ($null -ne $consoleEncoding) {
    Write-DoctorLine -Status "INFO" -Message ("控制台 OutputEncoding = {0}" -f $consoleEncoding.WebName) -Fix "若中文乱码或 hydromodel 打印 emoji 时报 UnicodeEncodeError，先在本窗口执行: `$env:PYTHONUTF8='1' ；cmd 则用 set PYTHONUTF8=1。本脚本不会永久改编码。"
}

try {
    $codePage = (chcp | Out-String).Trim()
    Write-DoctorLine -Status "INFO" -Message $codePage
}
catch {
    Write-DoctorLine -Status "INFO" -Message "无法读取代码页（可忽略）。"
}

$policy = Get-ExecutionPolicy -Scope Process
Write-DoctorLine -Status "INFO" -Message ("当前进程 ExecutionPolicy = {0}" -f $policy) -Fix "若无法直接运行 .ps1，请用: powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_env.ps1 。-ExecutionPolicy Bypass 只作用于这一次命令，不是改系统策略。"

$condaEnv = $env:CONDA_DEFAULT_ENV
if ($condaEnv) {
    $status = "OK"
    $fix = ""
    if ($condaEnv -ne "hydro_homework") {
        $status = "WARN"
        $fix = "文档推荐 conda activate hydro_homework 。若你自己的环境已经装好依赖，可忽略名字。"
    }
    Write-DoctorLine -Status $status -Message ("conda 环境: {0}" -f $condaEnv) -Fix $fix
}
else {
    Write-DoctorLine -Status "WARN" -Message "未检测到 CONDA_DEFAULT_ENV。" -Fix "先打开 Anaconda Prompt 或在 PowerShell 执行 conda activate hydro_homework，再跑本脚本。"
}

$pythonCmd = $null
$pythonArgs = @()
$found = Get-Command python -ErrorAction SilentlyContinue
if ($null -ne $found) {
    $pythonCmd = $found.Source
}
else {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) {
        $pythonCmd = $pyLauncher.Source
        $pythonArgs = @("-3")
    }
}

if ($null -eq $pythonCmd) {
    Write-DoctorLine -Status "FAIL" -Message "PATH 里找不到 python 或 py。" -Fix "安装 Miniconda 后新开终端: conda create -n hydro_homework python=3.11 ; conda activate hydro_homework 。PyCharm 请选择该环境的 python.exe，不要点 IDE 右上角用错解释器。"
    Write-Host ""
    Write-Host "cmd / Anaconda Prompt 切目录:  cd /d `"$RepoRoot`""
    Write-Host "PowerShell 切目录:            Set-Location -LiteralPath '$RepoRoot'"
    exit 1
}

Write-DoctorLine -Status "OK" -Message ("将使用解释器: {0} {1}" -f $pythonCmd, ($pythonArgs -join " "))

if (-not (Test-Path -LiteralPath $PythonDoctor)) {
    Write-DoctorLine -Status "FAIL" -Message "找不到 scripts/check_env.py 。" -Fix "请确认在作业仓库里运行本脚本。"
    exit 1
}

# Forward to the cross-platform Python doctor. No packages are installed.
$allArgs = $pythonArgs + @($PythonDoctor) + $args
Write-Host ""
Write-Host "开始运行 Python 检测..."
Write-Host ("=" * 72)
& $pythonCmd @allArgs
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) {
    $exitCode = 0
}
exit $exitCode
