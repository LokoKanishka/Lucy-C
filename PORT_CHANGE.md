# Port Configuration Change

## Summary
Changed Lucy-C default port from 5000 to 5050 to avoid conflicts with other services.

## Files Modified
- `lucy_c/web/app.py` - Changed PORT env default from "5000" to "5050"
- `start_lucy.sh` - Updated message to show port 5050
- `scripts/run_web_ui.sh` - Changed BASE_PORT default  
- `scripts/verify_web_smoke.sh` - Updated curl endpoints
- `scripts/make_desktop_shortcut.sh` - Updated xdg-open URL

## Access
- **Old**: http://localhost:5000
- **New**: http://localhost:5050

## Environment Variable Override
You can still use a custom port by setting:
```bash
export PORT=8080  # or any other port
python3 lucy_c/web/app.py
```
