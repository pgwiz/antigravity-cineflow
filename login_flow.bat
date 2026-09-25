@echo off
title Google Flow Ultra Login (Port 9222)
echo =======================================================
echo  Opening Google Chrome for Google Flow Ultra Login
echo =======================================================
echo 1. Chrome will open to Google Sign-In.
echo 2. Sign in to peterbrian484@gmail.com and complete 2FA.
echo 3. Google Flow will load at https://flow.google.com/u/5/.
echo =======================================================

start "Google Flow Chrome" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="%~dp0temp\flow_profile" "https://accounts.google.com/ServiceLogin?continue=https://flow.google.com/u/5/"

echo Chrome launched!
echo After you complete sign-in in the Chrome window, press any key below to extract cookies:
pause

echo Extracting cookies from Chrome into .env...
python main.py --extract-cookies
echo Done! You can now close this window and run the season.
pause
