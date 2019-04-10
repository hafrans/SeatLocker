#! /usr/bin/env python3
import sys
import os
sys.path.append(".")
from server import *
from server.utils import *

# from seat.__future__ import *

if __name__ == "__main__":
    envaddr = os.environ.get("REDIS_ADDR",None)
    if len(sys.argv) > 1:
        if sys.argv[1] == "server":
            if len(sys.argv) >= 3:
                if sys.argv[2] == "standalone":
                    print("使用单例服务！")
                    from server.cron import *
                    multiprocessing.freeze_support() 
                    t2 = threading.Thread(target=deploy)
                    t2.daemon=True
                    t2.start()
                elif sys.argv[2] == "serveronly":
                    from server.cron_redis import *
                    if len(sys.argv) >= 4:
                        address = str(sys.argv[3])
                    if envaddr != None:
                        address = envaddr
                    print("WILL CONNECT "+address)
                    t2 = threading.Thread(target=deploy,kwargs={'redis_addr':address})
                    t2.daemon=True
                    t2.start()
                elif sys.argv[2] == "serverclient":
                    from server.cron_redis import *
                    if len(sys.argv) >= 4:
                        address = str(sys.argv[3])
                    if envaddr != None:
                        address = envaddr
                    print("WILL CONNECT "+address)
                    t3 = threading.Thread(target=deploy,kwargs={'redis_addr':address,'standalone':True})
                    t3.daemon=True
                    t3.start()
            app.run(debug=False,host="0.0.0.0")
        elif sys.argv[1] == "client":
            if len(sys.argv) > 2:
                address = str(sys.argv[2])
            else:
                address = "127.0.0.1"
            if envaddr != None:
                address = envaddr
            print("CLIENT WILL CONNECT "+address)
            from server.cron_redis import *
            multiprocessing.freeze_support() 
            pool = clientDeploy(address)
            pool.close()
            pool.join()
        else:
            # app.run(debug=True,host="0.0.0.0")
            # deploy()
            pass
    else:
        app.run(debug=True,host="0.0.0.0")

"""
  server 
      serverclient [host]
      onlyserver [host]
      standalone 
  client [host]
"""