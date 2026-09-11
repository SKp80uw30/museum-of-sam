"""Execute a local Blender Python file through the project's running MCP addon."""
import socket,json,sys
from pathlib import Path
script=Path(sys.argv[1]).resolve()
code='__file__ = '+repr(str(script))+'\n'+script.read_text()
with socket.create_connection(('127.0.0.1',9876),10) as s:
    s.settimeout(600)
    s.sendall(json.dumps({'type':'execute_code','params':{'code':code}}).encode())
    buf=b''
    while True:
        part=s.recv(65536)
        if not part:raise RuntimeError('Blender disconnected before a response')
        buf+=part
        try:result=json.loads(buf);break
        except (json.JSONDecodeError,UnicodeDecodeError):pass
    print(json.dumps(result,indent=2))
    if result.get('status')!='success':sys.exit(1)
