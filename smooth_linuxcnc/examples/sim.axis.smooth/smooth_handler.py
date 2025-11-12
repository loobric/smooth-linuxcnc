import gtk

class HandlerClass:
    def __init__(self, halcomp, builder):
        self.hal = halcomp
        self.builder = builder
        self.led_on = False
        
        # Get the LED label
        self.led = self.builder.get_object('led')
        
        # Set initial LED state
        self.update_led()
    
    def update_led(self):
        if self.led_on:
            self.led.set_text("ON")
            self.led.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('green'))
        else:
            self.led.set_text("OFF")
            self.led.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('red'))
    
    def on_button_press(self, widget, data=None):
        self.led_on = not self.led_on
        self.update_led()
    
    def on_button_release(self, widget, data=None):
        pass

def get_handlers(halcomp, builder):
    return [HandlerClass(halcomp, builder)]
