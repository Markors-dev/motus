@ECHO OFF
for %%A in ("%~dp0..\env\Scripts\python.exe")  Do set "_Python=%%~fA"
for %%A in ("%~dp0\uitestsuite")  Do set "_uitestsuite=%%~fA"
%_Python% -m pytest %_uitestsuite% -s
