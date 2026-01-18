@echo off
REM SSE 实时性测试 - 不同 Uvicorn 配置

echo ========================================
echo SSE 实时性测试 - Uvicorn 配置测试
echo ========================================
echo.

cd backend

echo 测试配置 1: 标准配置 + PYTHONUNBUFFERED
echo ----------------------------------------
echo set PYTHONUNBUFFERED=1
echo uvicorn app.main:app --reload --log-level info --timeout-keep-alive 300
echo.

echo 按任意键开始测试...
pause > nul

set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

REM 使用 h11 HTTP 实现（更简单，可能缓冲更少）
REM 禁用访问日志以减少开销
REM 增加超时时间
uvicorn app.main:app ^
  --reload ^
  --log-level info ^
  --timeout-keep-alive 300 ^
  --http h11 ^
  --no-access-log ^
  --interface asgi3

pause
