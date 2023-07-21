# SAGE-WRM (Web Remote)
 Control a SAGE Endec from a simple webpage

<br />

# Developer Notes
 This is one of my side projects, meaning it might not be updated frequently. SAGE-WRM is just a software tool for hobbyists using SAGE Equipment. NEVER should you ever port forward or open this software to the internet. There is NO password protection or user control… yet.
\
\
**I am not responsible for any miss-activations or damages caused by this software.**

## Release Notes
- 6/21/2023 - Initial release.

<br />

## How Does it work?
 SAGE-WRM uses one of the COM ports on the SAGE Endec, set to Hand Control, to emulate some of the functions of an official RC-1 Remote and display it to a webpage using a websocket.

<br />

# Installation 

## Hardware Requirements
 Obviously you will need a SAGE EAS Endec either a 1822 (tested) or 3644 (not tested yet) and method to receive and send the serial data from the SAGE, preferably a USB to serial adapter.

## Software Requirements
 SAGE-WRM was developed with Python 3.10.6 on Linux but any version higher than 3.9 and also Windows should work. Two libraries will need to be installed via PIP for SAGE-WRM to work.
\
\
 Linux:
 ```bash
 pip3 install pyserial websockets
 ```

 Windows:
 ```bash
 pip install pyserial websockets
 ```

## Setup
 After downloading the repository and saving it to a location you will need to edit the `config.json` file.
\
In the config file both `serial_port` and `serial_port_baud` should be set to the device connected to the correct COM port on the SAGE Endec that is set to Hand Control. Depending on the application, `websocket_ip` and `websocket_port` most likely can stay at their default values as the same with `debug_mode`.

## Starting SAGE-WRM
 Linux:
 ```bash
 python3 main.py
 ```

 Windows:
 ```bash
 py main.py
 ```
 or
  ```bash
 python main.py
 ```
\
  To view the webpage you can use the built in python module `http.server`. This will have to be running in a separate process because SAGE-WRM does not come with an HTTP server. 
  \
  \
  **Make sure the below command is ran in the root directory of this repository!!**
  \
  \
  Linux:
 ```bash
 python3 -m http.server 8888
 ```

 Windows:
 ```bash
 py -m http.server 8888
 ```
 or
  ```bash
 python -m http.server 8888
 ```
\
\
To Access the Webpage go to:
```
http://localhost:8888/
```
