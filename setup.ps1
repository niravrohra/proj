#!/usr/bin/env pwsh
# Books4U Library Management System - Setup Script
# This script will install all dependencies and set up the database

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Books4U Library Management System" -ForegroundColor Cyan
Write-Host "  Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = py --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Install required packages
Write-Host ""
Write-Host "Installing required packages..." -ForegroundColor Yellow
Write-Host "  - Flask (web framework)" -ForegroundColor Gray
Write-Host "  - Werkzeug (password hashing)" -ForegroundColor Gray

py -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to upgrade pip" -ForegroundColor Red
    exit 1
}

py -m pip install Flask Werkzeug --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Packages installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install packages" -ForegroundColor Red
    exit 1
}

# Check if database exists
Write-Host ""
if (Test-Path "library.db") {
    Write-Host "Database 'library.db' already exists." -ForegroundColor Yellow
    $response = Read-Host "Do you want to reload the database? This will delete all existing data. (y/N)"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Reloading database..." -ForegroundColor Yellow
        py load_data.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Database reloaded successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to reload database" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Skipping database reload" -ForegroundColor Gray
    }
} else {
    Write-Host "Creating database..." -ForegroundColor Yellow
    py load_data.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Database created successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create database" -ForegroundColor Red
        exit 1
    }
}

# Setup complete
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application, run:" -ForegroundColor Yellow
Write-Host "  py app.py" -ForegroundColor White
Write-Host ""
Write-Host "Then open your browser to:" -ForegroundColor Yellow
Write-Host "  http://127.0.0.1:5000" -ForegroundColor White
Write-Host ""
Write-Host "Default login credentials:" -ForegroundColor Yellow
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter to start the application now, or Ctrl+C to exit..."
Read-Host

# Start the application
Write-Host "Starting Books4U..." -ForegroundColor Cyan
py app.py
