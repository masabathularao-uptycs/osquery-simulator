# Setup osquery simulator in a machine

1. Git clone this repository.

    Clone in all the similator nodes using a for loop similar as below in case if you want to setup osquery simulators in multiple machines.
    Modify below command accordingly:
    ```
    for i in machine1 machine2 machine3 ; do ssh abacus@$i "echo $i;git clone REPO-LINK"; done
    ```

<br>
NOTE : Make sure to Install all the python dependency packages if missing on your machines. (pip3 install -r requirements.txt)

2. Start the simulator server.

    ```
    nohup python ~/osquery-simulator/app.py &> simulator_server.out &
    ```

    Start the server in multiple machines (incase of multiple simulator machines):
    ```
    for i in machine1 machine2 machine3 ; do ssh abacus@$i "echo $i; nohup python3 ~/osquery-simulator/app.py &> simulator_server.out &";done
    ```
<br>

# Pull latest code from github to simulator machines

    ```
    for i in machine1 machine2 machine3 ; do ssh abacus@$i "cd ~/osquery-simulator && git pull origin main && echo \"Git pull on $i successful\"";done
    ```

---
