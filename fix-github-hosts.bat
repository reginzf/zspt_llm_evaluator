@echo off
chcp 65001 >nul
title GitHub Hosts 修复工具

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 需要管理员权限！
    echo 请右键点击此脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo ==========================================
echo     GitHub Hosts 修复工具
echo ==========================================
echo.

:: 备份 hosts 文件
set "backup_name=hosts.bak.%date:~0,4%%date:~5,2%%date:~8,2%-%time:~0,2%%time:~3,2%%time:~6,2%"
set "backup_name=%backup_name: =0%"
copy /Y C:\Windows\System32\drivers\etc\hosts C:\Windows\System32\drivers\etc\%backup_name% >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] 已备份 hosts 文件到: %backup_name%
) else (
    echo [!] 备份失败，继续执行...
)
echo.

:: 删除旧的 GitHub hosts 配置
echo [1/3] 清理旧的 GitHub 配置...
findstr /V /C:"github" C:\Windows\System32\drivers\etc\hosts > %TEMP%\hosts_new.txt 2>nul
findstr /V /C:"Github Hosts" %TEMP%\hosts_new.txt > %TEMP%\hosts_clean.txt 2>nul
findstr /V /C:"#Project:" %TEMP%\hosts_clean.txt > %TEMP%\hosts_final.txt 2>nul

:: 添加新的 GitHub hosts 配置
echo [2/3] 写入新的 GitHub IP 地址...
echo. >> %TEMP%\hosts_final.txt
echo # ========================================== >> %TEMP%\hosts_final.txt
echo # GitHub Hosts Start >> %TEMP%\hosts_final.txt
echo # 更新日期: %date% %time% >> %TEMP%\hosts_final.txt
echo # ========================================== >> %TEMP%\hosts_final.txt
echo. >> %TEMP%\hosts_final.txt

:: GitHub 主要域名
echo # GitHub 主域名 >> %TEMP%\hosts_final.txt
echo 140.82.114.4    github.com >> %TEMP%\hosts_final.txt
echo 140.82.113.4    github.com >> %TEMP%\hosts_final.txt
echo 140.82.112.4    github.com >> %TEMP%\hosts_final.txt
echo 20.205.243.166  github.com >> %TEMP%\hosts_final.txt
echo. >> %TEMP%\hosts_final.txt

:: Gist
echo # Gist >> %TEMP%\hosts_final.txt
echo 140.82.121.4    gist.github.com >> %TEMP%\hosts_final.txt
echo 140.82.121.3    gist.github.com >> %TEMP%\hosts_final.txt
echo. >> %TEMP%\hosts_final.txt

:: API
echo # GitHub API >> %TEMP%\hosts_final.txt
echo 140.82.121.6    api.github.com >> %TEMP%\hosts_final.txt
echo 140.82.121.5    api.github.com >> %TEMP%\hosts_final.txt
echo. >> %TEMP%\hosts_final.txt

:: Raw Content
echo # Raw Content >> %TEMP%\hosts_final.txt
echo 185.199.108.133 raw.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.109.133 raw.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.110.133 raw.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.111.133 raw.githubusercontent.com >> %TEMP%\hosts_final.txt
echo. >> %TEMP%\hosts_final.txt

:: User Content
echo # User Content >> %TEMP%\hosts_final.txt
echo 185.199.108.133 user-images.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.109.133 user-images.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.110.133 user-images.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.111.133 user-images.githubusercontent.com >> %TEMP%\hosts_final.txt
echo. >> %TEMP%\hosts_final.txt

:: Assets
echo # Assets >> %TEMP%\hosts_final.txt
echo 185.199.108.153 github.io >> %TEMP%\hosts_final.txt
echo 185.199.110.154 github.githubassets.com >> %TEMP%\hosts_final.txt
echo 185.199.111.133 desktop.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.110.133 camo.githubusercontent.com >> %TEMP%\hosts_final.txt
echo. >> %TEMP%\hosts_final.txt

:: Avatars
echo # Avatars >> %TEMP%\hosts_final.txt
echo 185.199.108.133 avatars.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.109.133 avatars1.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.110.133 avatars2.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.111.133 avatars3.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.108.133 avatars4.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.109.133 avatars5.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.110.133 avatars0.githubusercontent.com >> %TEMP%\hosts_final.txt
echo. >> %TEMP%\hosts_final.txt

:: Other
echo # Other >> %TEMP%\hosts_final.txt
echo 140.82.112.22 collector.github.com >> %TEMP%\hosts_final.txt
echo 140.82.121.10 codeload.github.com >> %TEMP%\hosts_final.txt
echo 140.82.113.17 github.community >> %TEMP%\hosts_final.txt
echo 192.0.66.2    github.blog >> %TEMP%\hosts_final.txt
echo 185.199.108.153 githubstatus.com >> %TEMP%\hosts_final.txt
echo 185.199.108.133 media.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.108.133 cloud.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 185.199.110.133 objects.githubusercontent.com >> %TEMP%\hosts_final.txt
echo 146.75.121.194 github.global.ssl.fastly.net >> %TEMP%\hosts_final.txt
echo. >> %TEMP%\hosts_final.txt
echo # ========================================== >> %TEMP%\hosts_final.txt
echo # GitHub Hosts End >> %TEMP%\hosts_final.txt
echo # ========================================== >> %TEMP%\hosts_final.txt

:: 替换 hosts 文件
echo [3/3] 更新 hosts 文件...
copy /Y %TEMP%\hosts_final.txt C:\Windows\System32\drivers\etc\hosts >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] 更新失败！请手动运行此脚本作为管理员
    pause
    exit /b 1
)

:: 清理临时文件
del %TEMP%\hosts_new.txt 2>nul
del %TEMP%\hosts_clean.txt 2>nul
del %TEMP%\hosts_final.txt 2>nul

echo.
echo ==========================================
echo [✓] Hosts 文件更新成功！
echo ==========================================
echo.
echo 正在刷新 DNS 缓存...
ipconfig /flushdns >nul 2>&1
echo [✓] DNS 缓存已刷新
echo.
echo 测试连接 GitHub...
ping -n 2 github.com
echo.
echo 如果 ping 仍然失败，请尝试：
echo 1. 重启浏览器或终端
echo 2. 更换网络环境（如使用手机热点测试）
echo 3. 使用代理工具
echo.
pause
