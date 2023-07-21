import asyncio
import websockets
import serial
import threading
import logging
import json



# const for translating @ABC... to 0123...
line_locations = [
    '0x40',
    '0x41',
    '0x42', 
    '0x43', 
    '0x44', 
    '0x45', 
    '0x46', 
    '0x47', 
    '0x48', 
    '0x49', 
    '0x4a', 
    '0x4b', 
    '0x4a', 
    '0x4d', 
    '0x4e', 
    '0x4f', 
    '0x50', 
    '0x51', 
    '0x52', 
    '0x53'
]

# Main buffer for the LCD display
LCD_display = ["","","",""] 


class SerialConnection:
    def __init__(self, serial_port='/dev/ttyUSB0', serial_baud=9600):
        self.ser = serial.Serial(
            port=serial_port,\
            baudrate=serial_baud,\
            parity=serial.PARITY_NONE,\
            stopbits=serial.STOPBITS_ONE,\
            bytesize=serial.EIGHTBITS,\
                timeout=0)
        print("Connected to: " + self.ser.portstr)



    def clear_lcd_line(self, lcd_line:str):
        if(lcd_line == "@"):   LCD_display[0] = " "
        elif(lcd_line == "A"): LCD_display[1] = " "
        elif(lcd_line == "B"): LCD_display[2] = " "
        elif(lcd_line == "C"): LCD_display[3] = " "
        else: logs.error("LCD line to be cleared could not be found!")



    def update_soft_lcd(self, lcd_line:str, data:str):
        if(lcd_line == "@"): LCD_display[0] = data
        elif(lcd_line == "A"): LCD_display[1] = data
        elif(lcd_line == "B"): LCD_display[2] = data
        elif(lcd_line == "C"): LCD_display[3] = data
        else: logs.error("LCD line to be updated could not be found!")


        logs.debug(LCD_display)



    def set_lcd_char(self, lcd_line:str,line_index:int,character:str):
        l = len(character)

        if(lcd_line == "@"):   LCD_display[0] = f"{LCD_display[0][:line_index]}{character}{LCD_display[0][line_index + l:]}"
        elif(lcd_line == "A"): LCD_display[1] = f"{LCD_display[1][:line_index]}{character}{LCD_display[1][line_index + l:]}"
        elif(lcd_line == "B"): LCD_display[2] = f"{LCD_display[2][:line_index]}{character}{LCD_display[2][line_index + l:]}"
        elif(lcd_line == "C"): LCD_display[3] = f"{LCD_display[3][:line_index]}{character}{LCD_display[3][line_index + l:]}"
        else: logs.error("LCD character to be updated could not be found!")

        logs.debug(LCD_display)



    def bttn_cmd(self,btn:str):
        mesg = b""

        if(btn == "bt0"):   mesg = b"\x03\x61"
        elif(btn == "bt1"): mesg = b"\x03\x62"
        elif(btn == "bt2"): mesg = b"\x03\x63"
        elif(btn == "bt3"): mesg = b"\x03\x64"
        else:
            logs.error("Bad button command")
            return
        
        self.ser.write(mesg)
        


    def read_serial_statemachine(self):
        buff = ""
        to_update_buff = ""
        state = 0
        location = None
        to_update = None

        while True:
            for line in self.ser.read():
                if(state == 0 and line == 0x1b):
                    logs.debug(state)
                    logs.debug("found 0x1b")
                    buff = ""
                    to_update_buff = ""
                    location = None
                    state = 1
                    continue

                if(state == 1 and line == 0x49):
                    logs.debug("instruction found")
                    state = 2
                    continue

                if(state == 2 and location == None):
                    location = chr(line)
                    logs.debug(f"LCD Location={location}")
                    state = 3
                    continue



                if(state == 3 and line == 0x40):
                    state = 4
                    logs.debug("setting the root of the line")
                    continue
                elif(state == 3):
                    if(hex(line) in line_locations):
                        to_update = line_locations.index(hex(line))
                        logs.debug(f"Setting to a custom location... [{to_update}]")
                        state = 200
                        continue
                    else:
                        state = 0
                        logs.debug(f"something weird happened when , restarting... [{chr(line)}] [{hex(line)}]")
                        continue



                if(state == 4 and line == 0x1b):
                    logs.debug("Inner-ESC (0x1b) found!")
                    state = 5
                    continue
                elif(state == 4):
                    logs.debug("Possible Data found! Grabbing it...")
                    buff += chr(line)
                    state = 100
                    continue



                # ====== Inner-ESC state machine ======

                if(state == 5 and line == 0x4B):
                    logs.debug("K(c)lear line command")
                    self.clear_lcd_line(location)
                    state = 0
                    continue

                # ====== Grabbing data state machine ======

                if (state == 100):
                    if(line == 0x1b):
                        logs.warning("ESC character found in while grabbing screen data...")
                        state = 0
                        continue
                    
                    buff += str(chr(line))

                    if(len(buff) >= 20):
                        # print("end of line, should send to soft_lcd_display")
                        self.update_soft_lcd(location, buff)
                        state = 0
                        continue

                # ====== Update a specific line state machine ======
                if(state == 200):
                    if(line == 0x1b):
                        self.set_lcd_char(location, to_update, to_update_buff)
                        logs.debug(to_update_buff)
                        logs.debug("insert command done")
                        buff = ""
                        to_update_buff = ""
                        location = None
                        state = 1
                        continue
                    else:
                        logs.debug("CHaracter added to buffer")
                        to_update_buff += chr(line)
                        self.set_lcd_char(location, to_update, to_update_buff)
                        continue



                    
CONNECTIONS = set()

async def register(websocket, ser_class):
    CONNECTIONS.add(websocket)
    try:
        await asyncio.gather(send_data(), receive_data(websocket, ser_class))
    finally:
        CONNECTIONS.remove(websocket)

async def send_data():
    last_message = ""
    while True:
        message = f'"0":"{LCD_display[0]}","1":"{LCD_display[1]}","2":"{LCD_display[2]}","3":"{LCD_display[3]}"'
        message = "{"+message+"}"
        if(last_message != message):
            last_message = message
            websockets.broadcast(CONNECTIONS, message)
        await asyncio.sleep(0.3)


async def receive_data(websocket, ser_class):
    try:
        while True:
            data = await websocket.recv()
            ser_class.bttn_cmd(str(data))
    except websockets.exceptions.ConnectionClosedOK:
        logs.debug("Client disconnected")

        
async def main(ser_class, ws_ip="localhost", ws_port=8333):
    async with websockets.serve(lambda websocket, path: register(websocket, ser_class), ws_ip, ws_port):
        await asyncio.Future()




if __name__ == "__main__":
    
    logs = logging.getLogger(__name__)
    logs.setLevel(level=logging.WARNING)
    sh = logging.StreamHandler()
    fm_formatter = logging.Formatter('%(levelname)s:%(lineno)d:  %(message)s')
    sh.setFormatter(fm_formatter)
    logs.addHandler(sh)

    try:
        with open("./config.json", "r") as configfile:
            jsonconfig = json.loads(configfile.read())
            configfile.close()
    except:
        # bruh moment
        logs.critical("Could not process JSON config. Please check it's formatting")
        exit()
        

    if(jsonconfig["debug_mode"]):
        logs.setLevel(logging.DEBUG)
        logs.debug(f"Debugging Enabled")


    logs.debug(f"Loaded Json Config:  {jsonconfig}")


    Serialclass = SerialConnection(
        serial_port=jsonconfig["serial_port"],
        serial_baud=jsonconfig["serial_port_baud"]
    )
    SerialThread = threading.Thread(target=Serialclass.read_serial_statemachine)
    SerialThread.start()

    asyncio.run(
        main(ser_class=Serialclass,
            ws_ip=jsonconfig["websocket_ip"],
            ws_port=jsonconfig["websocket_port"]
        )
    )
