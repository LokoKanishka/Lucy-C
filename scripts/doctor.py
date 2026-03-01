#!/usr/bin/env python3
"""
Lucy-C Doctor: System Health & Diagnostics Tool.
Validates environment, dependencies, hardware, and services.
"""
import sys
import os
import subprocess
import platform
import shutil
import requests
from pathlib import Path

# ANSI colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(component, status, message=""):
    if status == "PASS":
        print(f"[{Colors.OKGREEN}PASS{Colors.ENDC}] {component}: {message}")
    elif status == "FAIL":
        print(f"[{Colors.FAIL}FAIL{Colors.ENDC}] {component}: {message}")
    elif status == "WARN":
        print(f"[{Colors.WARNING}WARN{Colors.ENDC}] {component}: {message}")
    else:
        print(f"[{Colors.OKBLUE}INFO{Colors.ENDC}] {component}: {message}")

def check_python_version():
    minor = sys.version_info.minor
    if sys.version_info.major == 3 and minor >= 10:
        print_status("Python Version", "PASS", f"{platform.python_version()}")
        return True
    else:
        print_status("Python Version", "FAIL", f"Required >= 3.10, found {platform.python_version()}")
        return False

def check_venv():
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        print_status("Virtual Environment", "PASS", f"Active ({sys.prefix})")
    else:
        print_status("Virtual Environment", "WARN", "Running outside of a virtual environment is not recommended.")
    return in_venv

def check_binary(binary_name):
    path = shutil.which(binary_name)
    if path:
        print_status(f"Binary: {binary_name}", "PASS", path)
        return True
    else:
        print_status(f"Binary: {binary_name}", "FAIL", "Not found in PATH")
        return False

def check_pip_package(package_name):
    try:
        # Use importlib.metadata to check if package is installed
        import importlib.metadata
        version = importlib.metadata.version(package_name)
        print_status(f"Package: {package_name}", "PASS", f"v{version}")
        return True
    except importlib.metadata.PackageNotFoundError:
        print_status(f"Package: {package_name}", "FAIL", "Not installed")
        return False

def check_ollama():
    url = "http://127.0.0.1:11434/api/tags"
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            print_status("Service: Ollama", "PASS", f"Online. Models: {', '.join(model_names[:3])}...")
            return True
        else:
            print_status("Service: Ollama", "FAIL", f"Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_status("Service: Ollama", "FAIL", "Connection refused. Is 'ollama serve' running?")
        return False

def check_audio():
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devs = [d['name'] for d in devices if d['max_input_channels'] > 0]
        output_devs = [d['name'] for d in devices if d['max_output_channels'] > 0]
        
        if input_devs:
            print_status("Hardware: Audio Input", "PASS", f"Found {len(input_devs)} devices")
        else:
            print_status("Hardware: Audio Input", "FAIL", "No input devices found")

        if output_devs:
            print_status("Hardware: Audio Output", "PASS", f"Found {len(output_devs)} devices")
        else:
            print_status("Hardware: Audio Output", "FAIL", "No output devices found")
            
    except ImportError:
        print_status("Hardware: Audio", "FAIL", "sounddevice package not installed")
    except Exception as e:
        print_status("Hardware: Audio", "FAIL", str(e))

def main():
    print(f"{Colors.HEADER}=== Lucy-C System Doctor ==={Colors.ENDC}")
    
    # Check Environment
    check_python_version()
    check_venv()
    
    # Check Critical Binaries
    run_status = True
    run_status &= check_binary("ffmpeg")
    check_binary("wmctrl")  # Optional but good for window management
    check_binary("xdotool") # Optional
    
    # Check Python Packages
    run_status &= check_pip_package("flask")
    run_status &= check_pip_package("flask_socketio")
    run_status &= check_pip_package("eventlet")
    run_status &= check_pip_package("faster_whisper")
    # run_status &= check_pip_package("mimic3_tts") # May be installed via git/local
    
    # Check External Services
    check_ollama()
    
    # Check Hardware
    check_audio()

    print(f"\n{Colors.HEADER}=== Diagnosis Complete ==={Colors.ENDC}")
    if run_status:
        print(f"{Colors.OKGREEN}System is HEALTHY for basic operation.{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"{Colors.FAIL}System has CRITICAL ISSUES.{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
