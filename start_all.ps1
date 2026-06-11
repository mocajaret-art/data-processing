# FBS 一键启动脚本
$root = $PSScriptRoot

Write-Host "============================================"
Write-Host "  FBS 分布式任务调度与数据处理平台"
Write-Host "============================================"
Write-Host ""
Write-Host "[1/3] 启动后端 (端口 8002)..."

Start-Process python -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8002" -WorkingDirectory "$root\backend" -WindowStyle Minimized

Start-Sleep -Seconds 3
Write-Host "[2/3] 启动 Celery Worker..."

Start-Process python -ArgumentList "-m celery -A app.celery_app.celery worker --loglevel=info --concurrency=2 -P solo" -WorkingDirectory "$root\backend" -WindowStyle Minimized

Write-Host "[3/3] 启动前端 (端口 3000)..."

Start-Process cmd -ArgumentList "/c cd /d $root\frontend && npx vite --host 0.0.0.0 --port 3000" -WindowStyle Minimized

Write-Host ""
Write-Host "============================================"
Write-Host "  启动完成"
Write-Host "  API 文档:  http://localhost:8002/docs"
Write-Host "  前端页面:  http://localhost:3000"
Write-Host "============================================"
Write-Host ""
Write-Host "按任意键停止所有服务..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host "正在停止服务..."
Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "已停止。"