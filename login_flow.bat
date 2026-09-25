@echo off
title Google Flow Ultra Login & Cookie Extractor
echo =======================================================
echo  Google Flow Ultra Login & Cookie Extractor
echo =======================================================
echo 1. Launching Chrome on a dynamic random port...
echo 2. Chrome will open to Google Sign-In.
echo 3. Sign in with peterbrian484@gmail.com and approve 2FA.
echo 4. Once Google Flow opens, this script auto-extracts
echo    all cookies into .env for headless generation!
echo =======================================================

python main.py --login-flow

pause
