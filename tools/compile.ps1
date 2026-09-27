# 用 MAIN 端真实 classpath + 本地 jar 直接 javac 编译，快速拿到英文错误清单
param([switch]$Quiet)
$ErrorActionPreference = 'Continue'
$proj = 'E:\Files\milky-addon-26.1.2'
$jdk  = (Get-ChildItem "$proj\tools" -Directory | Where-Object Name -like 'jdk-25*' | Select-Object -First 1).FullName
$out  = "$proj\build\classes"
New-Item -ItemType Directory -Force -Path $out, "$proj\build" | Out-Null

# 类路径：复用 PCL 启动脚本里的真实 -cp（躲开 libraries 里旧版 Forge/NeoForge 的 MC jar）
$cpList = @()
$bat = 'D:\mc\PCL\LatestLaunch.bat'
if (Test-Path $bat) {
    $raw = [IO.File]::ReadAllText($bat)                       # 只提取 -cp 段，绝不回显文件内容
    $m = [regex]::Match($raw, '-cp\s+"([^"]+)"')
    if ($m.Success) {
        foreach ($p in ($m.Groups[1].Value -split ';')) { if ($p -like '*.jar') { $cpList += $p } }
    }
    Remove-Variable raw
}
if ($cpList.Count -eq 0) {
    $cpList += (Get-ChildItem 'D:\mc\.minecraft\libraries' -Recurse -File -Filter *.jar |
        Where-Object { $_.FullName -notmatch '\\net\\minecraft\\client\\' -and $_.Name -notlike '*srg.jar' -and $_.FullName -notmatch 'net(forge|neoforged)' } |
        Select-Object -ExpandProperty FullName)
    $cpList += 'D:\mc\.minecraft\versions\MAIN\MAIN.jar'
}
$cpList += (Get-ChildItem "$proj\libs" -File -Filter *.jar | Select-Object -ExpandProperty FullName)
$cpStr = ($cpList -join ';')

$srcs = Get-ChildItem "$proj\src" -Recurse -Filter *.java | Select-Object -ExpandProperty FullName
$argfile = "$proj\build\javac.args"
$lines = @('-encoding', 'UTF-8', '-proc:none', '-nowarn', '-Xmaxerrs', '10000', '-d', $out, '-cp', $cpStr) + $srcs
[IO.File]::WriteAllLines($argfile, $lines, [Text.UTF8Encoding]::new($false))   # javac 不认 BOM

$log = "$proj\build\javac.log"
Remove-Item $log -ErrorAction SilentlyContinue
# 走 cmd 重定向：避免 PowerShell 把 stderr 包装/折行
& cmd /c "`"$jdk\bin\javac.exe`" -J-Duser.language=en -J-Duser.country=US @`"$argfile`" > `"$log`" 2>&1"
$exit = $LASTEXITCODE
$c = @(Get-Content -LiteralPath $log -ErrorAction SilentlyContinue)
$errs = @($c | Select-String ': error:')
"EXIT=$exit  errors=$($errs.Count)  sources=$($srcs.Count)  cpJars=$($cpList.Count)"
if (-not $Quiet) {
    $errs | Select-Object -First 30 | ForEach-Object { $_.Line }
}
