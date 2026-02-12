"""
Virtual Display Service for Lucy
Manages Xvfb (X Virtual Framebuffer) to provide an isolated display environment.
"""

import os
import subprocess
import logging
import time
import signal
from typing import Optional, Dict

log = logging.getLogger("LucyC.VirtualDisplay")


class VirtualDisplay:
    """Manages a virtual X display using Xvfb for isolated GUI automation."""
    
    def __init__(self, display: str = ":99", resolution: str = "1920x1080x24"):
        """
        Initialize virtual display manager.
        
        Args:
            display: X display number (e.g., ":99")
            resolution: Screen resolution in format WIDTHxHEIGHTxDEPTH
        """
        self.display = display
        self.resolution = resolution
        self.process: Optional[subprocess.Popen] = None
        self.log = log
        
    def start(self) -> bool:
        """
        Start the virtual display.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running():
            self.log.info("Virtual display %s already running", self.display)
            return True
        
        try:
            # Check if xvfb is available
            result = subprocess.run(
                ["which", "Xvfb"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.log.warning("Xvfb not found. Install with: sudo apt install xvfb")
                return False
            
            # Start Xvfb
            cmd = [
                "Xvfb",
                self.display,
                "-screen", "0", self.resolution,
                "-ac",  # Disable access control
                "+extension", "GLX",  # Enable GLX for some apps
                "-nolisten", "tcp"  # Security: don't listen on TCP
            ]
            
            self.log.info("Starting virtual display: %s", " ".join(cmd))
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp  # Create new process group
            )
            
            # Wait a moment for Xvfb to initialize
            time.sleep(1)
            
            if self.is_running():
                self.log.info("Virtual display %s started successfully (PID: %d)", 
                            self.display, self.process.pid)
                return True
            else:
                self.log.error("Virtual display failed to start")
                self.process = None
                return False
                
        except Exception as e:
            self.log.error("Failed to start virtual display: %s", e)
            self.process = None
            return False
    
    def stop(self):
        """Stop the virtual display."""
        if not self.process:
            return
        
        try:
            self.log.info("Stopping virtual display %s (PID: %d)", 
                        self.display, self.process.pid)
            
            # Send SIGTERM for graceful shutdown
            self.process.terminate()
            
            # Wait up to 5 seconds
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                self.log.warning("Virtual display not responding, forcing kill")
                self.process.kill()
                self.process.wait()
            
            self.process = None
            self.log.info("Virtual display stopped")
            
        except Exception as e:
            self.log.error("Error stopping virtual display: %s", e)
    
    def is_running(self) -> bool:
        """
        Check if the virtual display is running.
        
        Returns:
            True if running, False otherwise
        """
        if not self.process:
            return False
        
        # Check if process is still alive
        if self.process.poll() is not None:
            # Process has terminated
            self.process = None
            return False
        
        return True
    
    def get_env(self) -> Dict[str, str]:
        """
        Get environment variables for using this display.
        
        Returns:
            Dictionary with DISPLAY variable set
        """
        return {"DISPLAY": self.display}
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.process and self.is_running():
            self.stop()
