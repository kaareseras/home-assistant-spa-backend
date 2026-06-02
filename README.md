# Norviq Home Assistant Integration

This repository contains a minimal Home Assistant custom integration for Norviq spa control.

Highlights:
- Username/password login against the backend
- A simple climate entity for spa temperature control
- Basic switches for common spa controls (jets, blower, lights)
- WebSocket streaming for live backend updates
- No filter, optimization, or advanced scheduling logic

## Layout

- custom_components/spa_backend/  Home Assistant custom component
- scripts/push_home_assistant_integration.sh  Push this repo to a remote

## HACS install

This repository is structured for HACS as a custom integration repository.

1. Add this GitHub repo as a custom repository in HACS.
2. Install the integration from HACS.
3. Restart Home Assistant.
4. Add the integration from Settings → Devices & Services → Add Integration.

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
