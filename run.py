import os

import uvicorn


def main() -> None:
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '8000'))
    reload_enabled = os.getenv('RELOAD', '1') in {'1', 'true', 'True'}
    uvicorn.run('app.main:app', host=host, port=port, reload=reload_enabled)


if __name__ == '__main__':
    main()
