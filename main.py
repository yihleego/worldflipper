import uvicorn
from airtest.core.settings import Settings

if __name__ == '__main__':
    # Airtest Settings
    Settings.FIND_TIMEOUT = 1
    Settings.FIND_TIMEOUT_TMP = 1
    # Start web
    uvicorn.run(app='api:app', port=18000)
