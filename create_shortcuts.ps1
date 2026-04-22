# ============================================================
# 在新电脑上使用前，只需修改下方三个参数：
#
# 1. $projectDir : 本项目所在的完整路径
#    查看方法：在项目文件夹按住Shift右键 -> "在此处打开PowerShell窗口"
#              然后输入 pwd 即可看到路径
#
# 2. $condaBase  : Anaconda/Miniconda 安装目录
#    查看方法：在 Anaconda PowerShell Prompt 中输入:
#              echo $env:CONDA_PREFIX
#              (取 envs 之前的部分，即 base 环境路径)
#
# 3. $condaEnv   : 运行脚本所用的 conda 环境名
#    查看方法：conda env list
# ============================================================

$projectDir = "C:\Users\kelin\BNL_CE\BNL_CE_WIB_SW_QC"
$condaBase  = "C:\ProgramData\anaconda3"
$condaEnv   = "femb_env"

# ============================================================
# 以下内容无需修改
# ============================================================

$condaHook  = "$condaBase\shell\condabin\conda-hook.ps1"
$pwsh       = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$desktopDir = [System.Environment]::GetFolderPath("Desktop")
$WshShell   = New-Object -ComObject WScript.Shell

# Shortcut 1: CTS FEMB QC
$s1 = $WshShell.CreateShortcut("$desktopDir\CTS_FEMB_QC.lnk")
$s1.TargetPath       = $pwsh
$s1.Arguments        = "-ExecutionPolicy ByPass -NoExit -Command `"& '$condaHook'; conda activate $condaEnv; cd '$projectDir'; python CTS_FEMB_QC_top.py`""
$s1.WorkingDirectory = $projectDir
$s1.WindowStyle      = 1
$s1.Description      = "Run CTS FEMB QC"
$s1.Save()
Write-Host "Created: CTS_FEMB_QC.lnk"

# Shortcut 2: CTS Real Time Monitor
$s2 = $WshShell.CreateShortcut("$desktopDir\CTS_RealTime_Monitor.lnk")
$s2.TargetPath       = $pwsh
$s2.Arguments        = "-ExecutionPolicy ByPass -NoExit -Command `"& '$condaHook'; conda activate $condaEnv; cd '$projectDir'; python CTS_Real_Time_Monitor.py`""
$s2.WorkingDirectory = $projectDir
$s2.WindowStyle      = 1
$s2.Description      = "Run CTS Real Time Monitor"
$s2.Save()
Write-Host "Created: CTS_RealTime_Monitor.lnk"

Write-Host "Done! Check your Desktop."
