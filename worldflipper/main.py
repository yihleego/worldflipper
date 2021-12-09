import uvicorn

from worldflipper import config

if __name__ == '__main__':
    # Init
    config.init()
    # Start web
    uvicorn.run(app='api:app', port=config.get_web_port())
