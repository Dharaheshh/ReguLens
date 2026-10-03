# ReguLens Demo Startup Script

Write-Host "Starting ReguLens Demo Environment..." -ForegroundColor Cyan

# 1. Start the Backend
Write-Host "`n[1/2] Starting FastAPI Backend on port 8000..." -ForegroundColor Yellow
Start-Process -FilePath "uvicorn" -ArgumentList "app.main:app", "--reload", "--port", "8000" -WorkingDirectory "$PSScriptRoot\backend" -NoNewWindow

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

# 2. Start the Frontend
Write-Host "`n[2/2] Starting React Frontend on port 5173..." -ForegroundColor Yellow
Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory "$PSScriptRoot\frontend" -NoNewWindow

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "ReguLens is now running!" -ForegroundColor Green
Write-Host "Frontend URL: http://localhost:5173" -ForegroundColor White
Write-Host "Backend API:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "========================================================`n" -ForegroundColor Green
Write-Host "Press Ctrl+C to terminate both servers (or close the terminal window)." -ForegroundColor Gray

# Keep script running so user can Ctrl+C to stop it (though Start-Process -NoNewWindow can be tricky with Ctrl+C, 
# typically in PowerShell they just close the terminal when done, or we can wait)
Wait-Event -Timeout 86400
