@echo off
chcp 65001 >nul
title PayMeTrust Reconciliation - Acces reseau
cd /d "%~dp0"

echo.
echo ============================================
echo   PayMeTrust Reconciliation - Mode reseau
echo ============================================
echo.

REM --- Detection IP locale (IPv4 privee) ---
set "LOCAL_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i /c:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        set "CAND=%%b"
        setlocal enabledelayedexpansion
        set "CAND=!CAND: =!"
        echo !CAND! | findstr /r "^192\.168\." >nul && (
            endlocal & set "LOCAL_IP=%%b" & goto :ip_found
        )
        echo !CAND! | findstr /r "^10\." >nul && (
            endlocal & set "LOCAL_IP=%%b" & goto :ip_found
        )
        echo !CAND! | findstr /r "^172\.1[6-9]\." >nul && (
            endlocal & set "LOCAL_IP=%%b" & goto :ip_found
        )
        echo !CAND! | findstr /r "^172\.2[0-9]\." >nul && (
            endlocal & set "LOCAL_IP=%%b" & goto :ip_found
        )
        echo !CAND! | findstr /r "^172\.3[0-1]\." >nul && (
            endlocal & set "LOCAL_IP=%%b" & goto :ip_found
        )
        endlocal
        if not defined LOCAL_IP set "LOCAL_IP=%%b"
    )
)

:ip_found
if defined LOCAL_IP (
    set "LOCAL_IP=%LOCAL_IP: =%"
) else (
    set "LOCAL_IP=INTROUVABLE"
)

set "PORT=8501"
set "URL=http://%LOCAL_IP%:%PORT%"

echo  Votre adresse IP locale : %LOCAL_IP%
echo.
echo  --------------------------------------------
echo   Lien a partager aux collegues :
echo.
echo      %URL%
echo.
echo  --------------------------------------------
echo.
echo  Conditions :
echo   - PC reste allume avec cette fenetre ouverte
echo   - Collegues sur le MEME reseau Wi-Fi / Ethernet
echo   - Pare-feu : autoriser le port %PORT% si besoin
echo.
echo  Connexion app : email @paymetrust.net
echo.
echo  Demarrage de Streamlit...
echo  (Ctrl+C pour arreter)
echo.

REM Autoriser le port dans le pare-feu (ignore si deja present / droits insuffisants)
netsh advfirewall firewall delete rule name="Streamlit PayMeTrust Reco" >nul 2>&1
netsh advfirewall firewall add rule name="Streamlit PayMeTrust Reco" dir=in action=allow protocol=TCP localport=%PORT% >nul 2>&1

streamlit run main.py --server.address 0.0.0.0 --server.port %PORT%

pause
