@echo off
rem Start Laundry Manager in debug mode (CDP debug port).
rem 注意：下面的 --remote-debugging-port 必须与 config.json 里的 cdp.port 保持一致，
rem 否则主程序按 cdp.port 去连调试端口会连不上，自动退回图像/坐标兼容模式。
rem 若修改了 config.json → cdp.port，请同步修改本行端口号（默认 9222）。
start "" "D:\Blending_Release-6.1.17\xygjwinapp.exe" --remote-debugging-port=9222
