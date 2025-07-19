# Pi Zero 2W Audio Oscilloscope

Real-time single-channel audio oscilloscope using Raspberry Pi Zero 2W, ADS1115 ADC, and ILI9341 TFT display.

<img width="662" height="847" alt="Screenshot 2025-07-19 at 1 31 11 PM" src="https://github.com/user-attachments/assets/122dab68-da23-4efa-9a60-0fa74a9529f9" />
<img width="662" height="480" alt="Screenshot 2025-07-19 at 1 31 25 PM" src="https://github.com/user-attachments/assets/36abc6dd-15a5-4fa7-b587-1685180cf565" />

https://www.youtube.com/watch?v=IcN3dApMLtY

## Hardware Components

- Raspberry Pi Zero 2W
- ADS1115 16-bit ADC module
- ILI9341 2.4" TFT display (240x320)
- 3.5mm audio connector (TRS jack)

- Breadboard and jumper wires
- MicroSD card (16GB minimum)
- 5V/3A power supply

## Operating System Setup

### Flash Raspberry Pi OS
1. Download Raspberry Pi Imager
2. Flash Raspberry Pi OS Lite to SD card
3. Do not eject SD card after flashing

### Pre-boot Configuration
Navigate to SD card boot partition and create these files:

**Enable SSH:**
```bash
touch ssh
```

**Set username and password:**
```bash
echo "pi:$(echo 'raspberry' | openssl passwd -6 -stdin)" > userconf.txt
```

**Configure WiFi:**
Create `wpa_supplicant.conf`:
```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YourWiFiName"
    psk="YourWiFiPassword"
}
```

### First Boot Setup
1. Insert SD card and power on Pi
2. Wait 2-3 minutes for boot
3. SSH into Pi: `ssh pi@raspberrypi.local`
4. Password: `raspberry`

**Change hostname (optional):**
```bash
sudo hostnamectl set-hostname scopepi
sudo nano /etc/hosts
# Change: 127.0.1.1 raspberrypi to 127.0.1.1 scopepi
sudo reboot
```

## Hardware Interface Configuration

### Enable I2C and SPI
```bash
sudo raspi-config
# Interface Options → I2C → Yes
# Interface Options → SPI → Yes
# Finish and reboot
sudo reboot
```

### Verify interfaces
```bash
# Check I2C
sudo i2cdetect -y 1

# Check SPI
ls /dev/spi*
```

## Hardware Wiring

### ADS1115 to Pi Zero 2W (I2C)
```
ADS1115    Pi Zero 2W
VCC     →  Pin 1 (3.3V)
GND     →  Pin 6 (Ground)
SDA     →  Pin 3 (GPIO 2)
SCL     →  Pin 5 (GPIO 3)
ADDR    →  Pin 6 (Ground)
```

### ILI9341 TFT to Pi Zero 2W (SPI)
```
ILI9341    Pi Zero 2W
VCC     →  Pin 1 (3.3V)
GND     →  Pin 6 (Ground)
CS      →  Pin 24 (GPIO 8)
RESET   →  Pin 22 (GPIO 25)
DC      →  Pin 18 (GPIO 24)
MOSI    →  Pin 19 (GPIO 10)
SDI     →  Pin 19 (GPIO 10)  # Alternative name for MOSI
SCK     →  Pin 23 (GPIO 11)
SCLK    →  Pin 23 (GPIO 11)  # Alternative name for SCK
LED     →  Pin 1 (3.3V)
MISO    →  Pin 21 (GPIO 9)   # Optional, often not connected
```

### Audio Input Connection
```
3.5mm TRS Jack    ADS1115
Tip (Left)     →  A0
Ring (Right)   →  Not connected
Sleeve (Ground)→  GND (shared with Pi ground)
```

**Note:** This project uses only the left audio channel (tip) for single-channel oscilloscope functionality.

### Complete Pin Reference
```
Pi Zero 2W GPIO Pinout:
   3.3V  1  2  5V      ← ADS1115 VCC, ILI9341 VCC+LED
GPIO2/SDA 3  4  5V     ← ADS1115 SDA
GPIO3/SCL 5  6  GND    ← All GND connections
GPIO4    7  8  GPIO14
  GND    9 10  GPIO15
GPIO17  11 12  GPIO18
GPIO27  13 14  GND
GPIO22  15 16  GPIO23
  3.3V  17 18  GPIO24  ← ILI9341 DC
GPIO10  19 20  GND     ← ILI9341 MOSI
GPIO9   21 22  GPIO25  ← ILI9341 RESET
GPIO11  23 24  GPIO8   ← ILI9341 SCK, ILI9341 CS
  GND   25 26  GPIO7
```

### Wiring Explanation

**I2C Communication (ADS1115):**
- **SDA (Serial Data):** Bidirectional data line for sending commands and receiving ADC readings
- **SCL (Serial Clock):** Clock signal that synchronizes data transmission
- **ADDR:** Address selection pin tied to ground to set I2C address to 0x48
- **VCC/GND:** Power supply connections

**SPI Communication (ILI9341):**
- **MOSI (Master Out, Slave In):** Pi sends pixel data to display
- **SCK (Serial Clock):** Synchronizes data transmission
- **CS (Chip Select):** Tells display when Pi is communicating with it
- **DC (Data/Command):** Indicates whether Pi is sending commands or pixel data
- **RESET:** Hardware reset line to restart display controller
- **LED:** Backlight power (always on when connected to 3.3V)

**Audio Input:**
- **Tip:** Left channel audio signal (typically varies between ±1V)
- **Ring:** Right channel audio signal (not used in this project)
- **Sleeve:** Audio ground reference

## Voltage Measurement and Display Flow

### True Voltage Reading
The oscilloscope displays the **actual voltage** present at the ADS1115 A0 input pin. Here's the complete signal flow:

1. **Audio Device Output** → Produces real voltage (e.g., 25mV peak from phone)
2. **3.5mm Cable** → Carries voltage through tip (signal) and sleeve (ground)
3. **ADS1115 ADC** → Measures actual voltage with 16-bit precision
4. **I2C Communication** → Transfers digital measurement to Pi
5. **Python Code** → Reads `audio_channel.voltage` (true measured value)
6. **Display** → Shows actual voltage in mV (e.g., "25.0mV")

### Visual Scaling vs. Voltage Reading
**Important:** The waveform scaling is separate from voltage measurement:

- **Voltage Reading:** Always shows true input voltage from audio device
- **Visual Scaling:** 400x amplification for display positioning only
- **Example:** 25mV input → displays "25.0mV" but waveform position uses 25mV × 400 = 10 pixels from center

### Voltage Display Range
```
Input Voltage    Display Reading    Visual Position
±100mV          "±100.0mV"         ±40 pixels from center (clipping)
±50mV           "±50.0mV"          ±20 pixels from center  
±25mV           "±25.0mV"          ±10 pixels from center
0V              "0.0mV"            Center line
```

The voltage reading shown on screen is the **unmodified, true voltage** measured by the ADS1115 ADC.

## Software Installation

### System Updates
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Dependencies
```bash
# System packages
sudo apt install python3-pip python3-numpy python3-pil libopenblas-dev -y

# Python libraries
sudo pip3 install adafruit-circuitpython-ads1x15
sudo pip3 install adafruit-circuitpython-rgb-display
```

### Python Libraries Explained

**Core System Libraries:**
- **time:** Provides delays and timing functions for sampling rates
- **threading:** Enables separate threads for audio sampling and display updates
- **collections.deque:** Efficient circular buffer for waveform data storage

**Hardware Interface Libraries:**
- **board:** CircuitPython library providing GPIO pin definitions
- **busio:** Handles I2C and SPI communication protocols
- **digitalio:** Controls individual GPIO pins for chip select and reset signals

**Display Libraries:**
- **PIL (Python Imaging Library):** Creates and manipulates images for display
- **PIL.Image:** Generates bitmap images for the oscilloscope display
- **PIL.ImageDraw:** Draws lines, text, and shapes on images
- **PIL.ImageFont:** Handles text rendering with fonts

**Hardware-Specific Libraries:**
- **adafruit_rgb_display.ili9341:** Driver for ILI9341 TFT display controller
- **adafruit_ads1x15.ads1115:** Driver for ADS1115 ADC with configuration options
- **adafruit_ads1x15.analog_in:** Simplified interface for reading analog voltages

### Library Function Breakdown

**ADS1115 ADC Control:**
```python
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create I2C bus
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

# Initialize ADC with slow I2C for reliability
ads = ADS.ADS1115(i2c)
ads.data_rate = 64  # Set to 64 samples per second

# Create analog input channel
audio_channel = AnalogIn(ads, ADS.P0)  # Use pin A0

# Read voltage (this is the TRUE voltage from audio device)
voltage = audio_channel.voltage
```

**ILI9341 Display Control:**
```python
import adafruit_rgb_display.ili9341 as ili9341
import digitalio

# Setup SPI and control pins
spi = board.SPI()
cs = digitalio.DigitalInOut(board.D8)    # Chip select
dc = digitalio.DigitalInOut(board.D24)   # Data/command
rst = digitalio.DigitalInOut(board.D25)  # Reset

# Initialize display
display = ili9341.ILI9341(spi, cs=cs, dc=dc, rst=rst, width=240, height=320)

# Create and display image
image = Image.new("RGB", (320, 240), (0, 0, 0))  # Black background
draw = ImageDraw.Draw(image)
draw.line([(0, 120), (320, 120)], fill=(0, 255, 0))  # Green line
rotated_image = image.rotate(90, expand=True)  # Landscape orientation
display.image(rotated_image)
```

**Threading Implementation:**
```python
import threading

def sample_audio(self):
    """Runs continuously in background thread"""
    while self.running:
        voltage = self.audio_channel.voltage  # TRUE voltage reading
        # Process and store data
        time.sleep(1.0 / self.sample_rate)

def update_display(self):
    """Runs continuously in separate thread"""
    while self.running:
        # Create and update display image
        time.sleep(0.1)  # 10 FPS refresh

# Start threads
sample_thread = threading.Thread(target=self.sample_audio)
sample_thread.daemon = True  # Dies when main program exits
sample_thread.start()
```

### Software Architecture Explanation

**Multi-threaded Design:**
- **Main thread:** Handles user input and program control
- **Sampling thread:** Continuously reads audio data from ADS1115
- **Display thread:** Updates TFT screen with waveform visualization

**Data Flow:**
1. **Audio signal** enters through 3.5mm jack tip
2. **ADS1115** converts analog voltage to 16-bit digital value
3. **I2C communication** transfers data to Pi at 64 samples/second
4. **Python processing** reads true voltage and scales for display coordinates
5. **Circular buffer** stores recent waveform points
6. **PIL graphics** creates oscilloscope display image
7. **SPI communication** sends pixel data to ILI9341 at 10 FPS

**Voltage Processing Flow:**
```python
# Step 1: Read true voltage from ADC
voltage = self.audio_channel.voltage  # Example: 0.025V (25mV)

# Step 2: Display true voltage in mV
voltage_mv = voltage * 1000          # 25.0mV shown on screen

# Step 3: Scale for visual positioning only
pixel_y = int(center_y - (voltage * 400))  # 25mV × 400 = 10 pixels offset
```

**Error Handling:**
- **I2C timeout detection** with automatic ADS1115 reinitialization
- **Display error recovery** with fallback error screens
- **Graceful shutdown** on Ctrl+C or system signals

## Verify Hardware Detection
```bash
# ADS1115 should appear at address 0x48
sudo i2cdetect -y 1

# SPI devices should be present
ls /dev/spi*
```

## Oscilloscope Software

### Create Application File
```bash
nano oscilloscope.py
```

Copy the single-channel oscilloscope code into this file.

### Code Structure Overview
```python
class SingleChannelOscilloscope:
    def __init__(self):
        # Initialize hardware interfaces
        # Setup display and ADC
        # Configure buffers and parameters
    
    def sample_audio(self):
        # Background thread for audio sampling
        # Reads ADS1115 continuously
        # Handles I2C errors gracefully
        # voltage = self.audio_channel.voltage  # TRUE voltage reading
    
    def draw_grid(self, draw):
        # Draws oscilloscope grid lines
        # Voltage and time references
    
    def draw_waveform(self, draw):
        # Renders scrolling waveform
        # Connects data points with lines
        # Uses 400x scaling for visual positioning
    
    def draw_labels(self, draw):
        # Shows voltage labels at correct positions
        # Displays true voltage reading in mV
        # Labels positioned at ±40 pixels (400x scaling)
    
    def update_display(self):
        # Background thread for display
        # Creates images and updates TFT
    
    def start(self):
        # Main program loop
        # Starts threads and handles shutdown
```

### Test Manual Execution
```bash
python3 oscilloscope.py
```

Expected output:
- Display initialization messages
- ADS1115 configuration confirmation
- Real-time waveform display on TFT

## Automatic Startup Configuration

### Create Systemd Service
```bash
sudo nano /etc/systemd/system/oscilloscope.service
```

Add this configuration:
```ini
[Unit]
Description=Audio Oscilloscope Display
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi
Environment=DISPLAY=:0
ExecStart=/usr/bin/python3 /home/pi/oscilloscope.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Systemd Service Explanation
- **After=network.target:** Waits for basic system initialization
- **User=pi:** Runs with pi user privileges (access to GPIO)
- **Restart=always:** Automatically restarts if program crashes
- **RestartSec=5:** Waits 5 seconds between restart attempts
- **StandardOutput=journal:** Captures program output to system logs

### Enable Automatic Startup
```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service for auto-start
sudo systemctl enable oscilloscope.service

# Start service immediately
sudo systemctl start oscilloscope.service

# Check service status
sudo systemctl status oscilloscope.service
```

### Service Management Commands
```bash
# Stop the service
sudo systemctl stop oscilloscope.service

# Restart the service
sudo systemctl restart oscilloscope.service

# View live logs
sudo journalctl -u oscilloscope.service -f

# Disable auto-start
sudo systemctl disable oscilloscope.service
```

## Technical Specifications

### Audio Input
- **Channels:** Single (left channel only)
- **Input range:** ±100mV (software limited for optimal display)
- **True voltage reading:** Unlimited within ADS1115 range (±4.096V)
- **Sampling rate:** 15 Hz (limited by I2C communication overhead)
- **Resolution:** 16-bit ADC (theoretical, ~12-bit effective due to noise)
- **Input impedance:** High (>1MΩ typical for ADS1115)

### Display
- **Resolution:** 240x320 pixels (landscape mode: 320x240)
- **Refresh rate:** 10 FPS
- **Waveform scaling:** 400x voltage amplification (visual positioning only)
- **Voltage display:** True measured voltage in mV
- **Trace height:** 160 pixels
- **Buffer size:** 140 samples (scrolling window)
- **Clipping indication:** Visual clipping at ±40 pixels (±100mV with 400x scaling)

### Performance
- **ADC data rate:** 64 SPS (hardware sampling rate)
- **Python sampling:** 15 Hz (effective rate after I2C overhead)
- **I2C frequency:** 100kHz (reduced from 400kHz for stability)
- **Display update:** Non-blocking threaded operation
- **Memory usage:** ~50MB typical

### Communication Protocols
- **I2C:** ADS1115 communication at 100kHz
- **SPI:** ILI9341 display at default Pi SPI speed (~125MHz)
- **Threading:** Cooperative multitasking with Python threading

## Usage Instructions

### Normal Operation
1. Power on Pi (auto-starts oscilloscope if service enabled)
2. Wait 30-60 seconds for complete boot and initialization
3. Connect audio source to 3.5mm input (tip = signal, sleeve = ground)
4. Observe real-time waveforms on display
5. Volume changes will be reflected in waveform amplitude
6. True voltage reading displayed in mV (upper right corner)
7. Visual clipping occurs at ±40 pixels (±100mV with 400x scaling)

### Understanding the Display
- **Voltage Reading:** Shows true input voltage from audio device
- **Waveform Position:** Uses 400x scaling for visual clarity
- **Grid Lines:** Provide voltage and time references
- **Labels:** ±100mV labels positioned where visual clipping occurs
- **CLIP! Indicator:** Appears when input exceeds ±100mV

### Manual Operation
```bash
# Stop automatic service
sudo systemctl stop oscilloscope.service

# Run manually for debugging
python3 oscilloscope.py

# Stop with Ctrl+C
```

### Safe Shutdown
```bash
# Proper shutdown command
sudo shutdown -h now

# Wait for green LED to stop flashing before unplugging power
```

## Troubleshooting

### Common Issues

**No waveform display:**
- Verify audio source is connected to tip (left channel)
- Check ADS1115 I2C connection with `sudo i2cdetect -y 1`
- Confirm audio source is producing signal
- Test with known audio source (phone playing music)

**Voltage reading shows but no waveform movement:**
- Audio signal may be too weak (try increasing volume)
- Check if signal is DC (oscilloscope optimized for AC signals)
- Verify 400x scaling is appropriate for signal level

**I2C errors (Remote I/O error):**
- Verify all wiring connections are secure
- Check power supply adequacy (use 3A adapter minimum)
- Reduce audio input volume
- Check for loose breadboard connections

**Display not working:**
- Verify SPI connections, especially CS, DC, and RESET pins
- Check display power (3.3V between VCC and GND)
- Confirm LED backlight connection
- Test display isolation by running simple display test

**Service won't start:**
```bash
# Check service logs for specific errors
sudo journalctl -u oscilloscope.service

# Verify Python script runs manually
python3 oscilloscope.py

# Check file permissions
ls -la oscilloscope.py
```

**Poor waveform quality:**
- Ensure good ground connection between audio source and Pi
- Use shielded audio cable if possible
- Keep audio input wires short
- Check for electrical interference sources

### Hardware Verification Tests

**Test ADS1115 basic communication:**
```bash
python3 -c "
import board, busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)
print(f'Voltage: {chan.voltage:.3f}V')
"
```

**Test ILI9341 display:**
```bash
python3 -c "
import board, digitalio
from PIL import Image
import adafruit_rgb_display.ili9341 as ili9341

spi = board.SPI()
cs = digitalio.DigitalInOut(board.D8)
dc = digitalio.DigitalInOut(board.D24)
rst = digitalio.DigitalInOut(board.D25)

display = ili9341.ILI9341(spi, cs=cs, dc=dc, rst=rst, width=240, height=320)
image = Image.new('RGB', (240, 320), (255, 0, 0))  # Red screen
display.image(image)
print('Red screen should appear on display')
"
```

## File Structure
```
/home/pi/
├── oscilloscope.py          # Main application
└── README.md               # This documentation

/etc/systemd/system/
└── oscilloscope.service    # Auto-start service configuration

System locations:
/dev/i2c-1                  # I2C device file
/dev/spidev0.0              # SPI device file
```

## Signal Input Considerations

### Input Voltage Limits
- **Display optimization:** ±100mV (visual clipping for best waveform visibility)
- **True voltage reading:** Shows actual input voltage regardless of display clipping
- **Hardware safe range:** ±4.096V (ADS1115 maximum with gain=1)
- **Absolute maximum:** ±5V (damage threshold)
- **Clipping indication:** "CLIP!" displayed when signal exceeds ±100mV

### Audio Source Compatibility
- **Phone/computer headphone output:** Compatible (may need volume adjustment)
- **Line level signals:** Compatible, may require volume reduction for optimal display
- **Microphone signals:** Usually too weak, may need preamplification
- **Musical instruments:** Electric guitar/bass output compatible

### Signal Quality Optimization
- **Use quality audio cables:** Reduces noise and interference
- **Minimize cable length:** Shorter connections reduce pickup
- **Proper grounding:** Ensure sleeve connection to Pi ground
- **Avoid power supply interference:** Keep audio cables away from power adapters

## Performance Optimization

### For Better Stability
- Use quality 3A power supply with stable 5V output
- Keep all wiring connections secure and short
- Use breadboard with good contact reliability
- Avoid electrical interference sources (WiFi routers, motors)
- Ensure adequate ventilation for continuous operation

### For Higher Sensitivity
- Adjust software voltage scaling in oscilloscope.py code
- Use low-noise audio sources
- Shield input connections if operating in noisy environment
- Consider external amplification for very weak signals

### Memory and CPU Optimization
- Current configuration optimized for Pi Zero 2W capabilities
- Reducing display refresh rate saves CPU cycles
- Smaller waveform buffers reduce memory usage
- Conservative I2C timing prevents communication errors

## Advanced Configuration

### Modifying Sampling Parameters
Edit oscilloscope.py to adjust:
```python
self.sample_rate = 15        # Python sampling frequency
self.ads.data_rate = 64     # ADS1115 hardware sampling rate
time.sleep(0.1)             # Display refresh interval
self.buffer_size = 140      # Waveform buffer length
```

### Voltage Scaling Adjustment
```python
# Increase sensitivity (higher scaling factor)
pixel_y = int(center_y - (voltage * 800))   # Was 400

# Decrease sensitivity (lower scaling factor)  
pixel_y = int(center_y - (voltage * 200))   # Was 400

# Note: Also update label positioning to match:
# top_clip_y = center_display_y - (100mV * scaling_factor / 1000)
```

### Display Customization
```python
# Change colors
self.waveform_color = (255, 0, 0)    # Red waveform
self.grid_color = (0, 0, 100)        # Blue grid
self.bg_color = (50, 50, 50)         # Dark gray background
```

## Safety Notes

- **Maximum input voltage:** ±4V (ADS1115 absolute maximum rating)
- **Power supply requirements:** 5V/3A minimum for stable operation
- **Proper shutdown:** Always use `sudo shutdown -h now` to prevent corruption
- **Heat dissipation:** Ensure adequate ventilation for continuous operation
- **ESD protection:** Handle components with proper anti-static precautions

## Theoretical Background

### Nyquist Sampling Theorem
With 15 Hz sampling rate, the maximum accurately representable frequency is 7.5 Hz. This oscilloscope is optimized for very low frequency signals like:
- DC voltage monitoring
- Slow audio frequency changes
- Power supply ripple analysis
- Environmental sensor variations

### ADC Resolution and Noise
- **16-bit ADC** provides 65,536 discrete levels
- **Effective resolution** reduced by noise to approximately 12-14 bits
- **LSB (Least Significant Bit)** represents ~125µV at ±4.096V range
- **Noise floor** typically 2-3 LSBs, or ~250-375µV

### Voltage Measurement Accuracy
- **ADS1115 accuracy:** ±0.3% typical at room temperature
- **True voltage display:** Shows actual measured voltage within ADC specifications
- **Display scaling:** Separate from voltage measurement, affects only visual positioning
- **Resolution:** Theoretical 125µV per bit, practical ~250-500µV due to noise

### Display Refresh and Persistence
- **10 FPS refresh** provides smooth visual experience
- **Waveform persistence** achieved through circular buffer
- **Scrolling display** shows temporal evolution of signal
- **Real-time voltage** updated with each sample for accurate monitoring
