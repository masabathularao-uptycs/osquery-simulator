# Setup osquery simulator in a machine

1. Git clone this repository.

    Clone in all the similator nodes using a for loop similar as below in case if you want to setup osquery simulators in multiple machines.
    Modify below command accordingly:
    ```
    for i in machine1 machine2 machine3 ; do ssh abacus@$i "echo $i;git clone REPO-LINK"; done
    ```

<br>

2. Intall Python3 on all the simulator machines

    verify version by running:  
    ```
    for i in machine1 machine2 machine3 ; do ssh abacus@$i "python3 -V";done
    ```

<br>

3. Install the following python3 dependencies on all the machines.
    ```
    for i in machine1 machine2 machine3 ; do ssh abacus@$i "pip3 install -r requirements.txt";done
    ```

<br>

4. Start the simulator server on all machines.

    ```
    for i in machine1 machine2 machine3; do
        ssh abacus@$i "cd ~/osquery-simulator && nohup python3 app.py > simulator_server.out 2>&1 & disown && echo 'Started server on $i'"
    done
    ```
<br>


<!-- # Pull latest code from github to simulator machines
```
for i in machine1 machine2 machine3 ; do ssh abacus@$i "cd ~/osquery-simulator && git pull origin main && echo \"Git pull on $i successful\"";done
``` -->
