@echo off
setlocal enabledelayedexpansion

set FASTQC_DIR=C:\Path to\FastQC
set OUTDIR=
set FILES=

:parse_args
if "%~1"=="" goto run_fastqc

if "%~1"=="-o" (
    set OUTDIR=%~f2
    shift
    shift
    goto parse_args
)

if "%~1"=="--outdir" (
    set OUTDIR=%~f2
    shift
    shift
    goto parse_args
)

if "%~1"=="-t" (
    shift
    shift
    goto parse_args
)

if "%~1"=="--threads" (
    shift
    shift
    goto parse_args
)

set FILES=!FILES! "%~f1"
shift
goto parse_args

:run_fastqc
if "%OUTDIR%"=="" (
    set OUTDIR=%CD%
)

if not exist "%OUTDIR%" (
    mkdir "%OUTDIR%"
)

for %%F in (%FILES%) do (
    echo Running FastQC on %%F

    java -Xmx250m -classpath "%FASTQC_DIR%";"%FASTQC_DIR%\sam-1.103.jar";"%FASTQC_DIR%\jbzip2-0.9.jar" uk.ac.babraham.FastQC.FastQCApplication "%%~fF"

    set BASENAME=%%~nF

    if "!BASENAME:~-6!"=="." (
        echo.
    )

    rem Handle .fastq.gz and .fq.gz names
    set NAME=%%~nF
    if "!NAME:~-6!"==".fastq" set NAME=!NAME:~0,-6!
    if "!NAME:~-3!"==".fq" set NAME=!NAME:~0,-3!

    if exist "%%~dpF!NAME!_fastqc.html" (
        move /Y "%%~dpF!NAME!_fastqc.html" "%OUTDIR%\"
    )

    if exist "%%~dpF!NAME!_fastqc.zip" (
        move /Y "%%~dpF!NAME!_fastqc.zip" "%OUTDIR%\"
    )
)

endlocal