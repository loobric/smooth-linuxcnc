import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import requests
import configparser
import os

class HandlerClass:
    def __init__(self, halcomp, builder):
        self.hal = halcomp
        self.builder = builder
        self.led_on = False
        
        # Get the LED label
        self.led = self.builder.get_object('led')
        
        # Read configuration from axis.ini
        self.config = configparser.ConfigParser(strict=False)
        config_path = os.path.join(os.path.dirname(__file__), 'axis.ini')
        self.config.read(config_path)
        
        self.server_url = self.config.get('SMOOTH', 'SERVER_URL', fallback='')
        self.token = self.config.get('SMOOTH', 'TOKEN', fallback='')
        
        # Set initial LED state
        self.update_led()
    
    def check_server_connectivity(self):
        """Check server connectivity by making a health request"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
            response = requests.get(f'{self.server_url}/api/health', headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def update_led(self):
        print(f"[DEBUG] update_led called, led_on={self.led_on}")
        if self.led_on:
            self.led.set_text("ON")
            color = Gdk.RGBA()
            color.parse('green')
            self.led.override_background_color(Gtk.StateFlags.NORMAL, color)
        else:
            self.led.set_text("OFF")
            color = Gdk.RGBA()
            color.parse('red')
            self.led.override_background_color(Gtk.StateFlags.NORMAL, color)
    
    def on_button_press(self, widget, data=None):
        print("[DEBUG] Button pressed!")
        print(f"[DEBUG] Checking server connectivity to {self.server_url}")
        # Check server connectivity and toggle LED based on result
        if self.check_server_connectivity():
            print("[DEBUG] Server is reachable, toggling LED")
            self.led_on = not self.led_on
        else:
            print("[DEBUG] Server is NOT reachable, turning LED off")
            # If server is down, turn LED off
            self.led_on = False
        self.update_led()
    
    def on_button_release(self, widget, data=None):
        pass

def get_handlers(halcomp, builder, useropts=None):
    return [HandlerClass(halcomp, builder)]
