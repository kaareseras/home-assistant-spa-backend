# Home Assistant Spa Backend Integration

This repository contains a minimal Home Assistant custom integration for the existing spa backend.

Highlights:
- Username/password login against the backend
- A simple climate entity for spa temperature control
- Basic switches for common spa controls (jets, blower, lights)
- WebSocket streaming for live backend updates
- No filter, optimization, or advanced scheduling logic

## Layout

- custom_components/spa_backend/  Home Assistant custom component
- scripts/push_home_assistant_integration.sh  Push this repo to a remote

## Quick start

1. Copy this folder into your Home Assistant custom_components directory.
2. Restart Home Assistant.
3. Add the integration from the UI and enter:
   - your Norviq username
   - your Norviq password
   - the spa you want to control from the selection list
4. The integration connects to the default Norviq backend URL automatically.
5. Use the generated climate and switch entities.

## Notes

- The backend token is obtained from /users/login.
- Commands are sent through the existing /devices/{device_id}/commands endpoint.
- Live updates are streamed over /ws/telemetry?token=... .
- This version intentionally keeps only the simple control path.
