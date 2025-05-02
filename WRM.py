from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config
from waitress import serve
import threading, logging, json, serial

_stdoutlogs = logging.getLogger("SAGE-WRM")
_stdoutlogs.setLevel(logging.INFO)
logging.basicConfig(format="%(levelname)s: %(message)s", datefmt="%d.%m.%Y-%H:%M:%S")


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
				timeout=1)
		_stdoutlogs.info("Serial Connected to: " + self.ser.portstr)



	def clear_lcd_line(self, lcd_line:str):
		if(lcd_line == "@"):   LCD_display[0] = " "
		elif(lcd_line == "A"): LCD_display[1] = " "
		elif(lcd_line == "B"): LCD_display[2] = " "
		elif(lcd_line == "C"): LCD_display[3] = " "
		else: _stdoutlogs.error("LCD line to be cleared could not be found!")



	def update_soft_lcd(self, lcd_line:str, data:str):
		if(lcd_line == "@"): LCD_display[0] = data
		elif(lcd_line == "A"): LCD_display[1] = data
		elif(lcd_line == "B"): LCD_display[2] = data
		elif(lcd_line == "C"): LCD_display[3] = data
		else: _stdoutlogs.error("LCD line to be updated could not be found!")


		_stdoutlogs.debug(LCD_display)



	def set_lcd_char(self, lcd_line:str,line_index:int,character:str):
		l = len(character)

		if(lcd_line == "@"):   LCD_display[0] = f"{LCD_display[0][:line_index]}{character}{LCD_display[0][line_index + l:]}"
		elif(lcd_line == "A"): LCD_display[1] = f"{LCD_display[1][:line_index]}{character}{LCD_display[1][line_index + l:]}"
		elif(lcd_line == "B"): LCD_display[2] = f"{LCD_display[2][:line_index]}{character}{LCD_display[2][line_index + l:]}"
		elif(lcd_line == "C"): LCD_display[3] = f"{LCD_display[3][:line_index]}{character}{LCD_display[3][line_index + l:]}"
		else: _stdoutlogs.error("LCD character to be updated could not be found!")

		_stdoutlogs.debug(LCD_display)



	def bttn_cmd(self, btn:str):
		mesg = b""

		if(btn == "bt0"):   mesg = b"\x03\x61"
		elif(btn == "bt1"): mesg = b"\x03\x62"
		elif(btn == "bt2"): mesg = b"\x03\x63"
		elif(btn == "bt3"): mesg = b"\x03\x64"
		else:
			_stdoutlogs.error("Bad button command")
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
					_stdoutlogs.debug(state)
					_stdoutlogs.debug("found 0x1b")
					buff = ""
					to_update_buff = ""
					location = None
					state = 1
					continue

				if(state == 1 and line == 0x49):
					_stdoutlogs.debug("instruction found")
					state = 2
					continue

				if(state == 2 and location == None):
					location = chr(line)
					_stdoutlogs.debug(f"LCD Location={location}")
					state = 3
					continue



				if(state == 3 and line == 0x40):
					state = 4
					_stdoutlogs.debug("setting the root of the line")
					continue
				elif(state == 3):
					if(hex(line) in line_locations):
						to_update = line_locations.index(hex(line))
						_stdoutlogs.debug(f"Setting to a custom location... [{to_update}]")
						state = 200
						continue
					else:
						state = 0
						_stdoutlogs.debug(f"something weird happened when , restarting... [{chr(line)}] [{hex(line)}]")
						continue



				if(state == 4 and line == 0x1b):
					_stdoutlogs.debug("Inner-ESC (0x1b) found!")
					state = 5
					continue
				elif(state == 4):
					_stdoutlogs.debug("Possible Data found! Grabbing it...")
					buff += chr(line)
					state = 100
					continue



				# ====== Inner-ESC state machine ======

				if(state == 5 and line == 0x4B):
					_stdoutlogs.debug("K(c)lear line command")
					self.clear_lcd_line(location)
					state = 0
					continue

				# ====== Grabbing data state machine ======

				if (state == 100):
					if(line == 0x1b):
						_stdoutlogs.warning("ESC character found in while grabbing screen data...")
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
						_stdoutlogs.debug(to_update_buff)
						_stdoutlogs.debug("insert command done")
						buff = ""
						to_update_buff = ""
						location = None
						state = 1
						continue
					else:
						_stdoutlogs.debug("CHaracter added to buffer")
						to_update_buff += chr(line)
						self.set_lcd_char(location, to_update, to_update_buff)
						continue


@view_config(route_name="get_screen", renderer="json", request_method="GET")
def APIGetScreen(request):
	return {str(i): text for i, text in enumerate(LCD_display)}


@view_config(route_name='receive_button', request_method='POST', renderer='json')
def APIReceiveButton(request):
	try:
		json_data:dict = request.json_body
		button = json_data.get("button")
		if(button):
			Serialclass.bttn_cmd(button)
	except:
		return {"error": "Invalid JSON"}
	
	return {"status": "ok"}

@view_config(route_name='webremote')
def WebHome(request):

	with open(f'./webremote.html', 'rb') as f:
		html = f.read()
	return Response(body=html, content_type='text/html')


def CreateApp():
	config = Configurator()
	config.add_route("get_screen", "/api/get_screen")
	config.add_route("receive_button", "/api/receive_button")
	config.add_route('webremote', '/')
	config.add_static_view(name="static", path="./static", cache_max_age=3600)

	config.scan()
	return config.make_wsgi_app()


if __name__ == "__main__":
	_stdoutlogs.info(f"SAGE-WRM - Created by SecludedFox :3")


	try:
		with open("./config.json", "r") as configfile:
			jsonconfig = json.load(configfile)
			configfile.close()
	except:
		_stdoutlogs.critical("Could not process JSON config. Please check it's formatting")
		exit()


	Serialclass = SerialConnection(
		serial_port=jsonconfig["serial_port"],
		serial_baud=jsonconfig["serial_port_baud"]
	)

	SerialThread = threading.Thread(target=Serialclass.read_serial_statemachine, daemon=True)
	SerialThread.start()

	app = CreateApp()
	serve(app, host=jsonconfig["webserver_host"], port=jsonconfig["webserver_port"])
