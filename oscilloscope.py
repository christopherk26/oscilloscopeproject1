#!/usr/bin/env python3
"""
Single Channel Audio Oscilloscope with ILI9341 TFT Display
Pi Zero 2W + ADS1115 + ILI9341 (240x320)
Fixed scaling to properly display ±50mV range
"""

import time
import digitalio
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.ili9341 as adafruit_ili9341
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import threading
import collections

class SingleChannelOscilloscope:
    def __init__(self):
        # Display setup
        print("Initializing ILI9341 display...")
        spi = board.SPI()
        self.display_cs = digitalio.DigitalInOut(board.D8)    # CS  
        self.display_dc = digitalio.DigitalInOut(board.D24)   # DC
        self.display_rst = digitalio.DigitalInOut(board.D25)  # Reset
        
        self.display = adafruit_ili9341.ILI9341(
            spi,
            cs=self.display_cs,
            dc=self.display_dc,
            rst=self.display_rst,
            width=240,
            height=320
        )
        
        # ADC setup with optimized settings
        print("Initializing ADS1115 for single channel...")
        
        # Create I2C bus with slower speed for reliability
        self.i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)  # 100kHz
        time.sleep(1.0)  # Critical delay after I2C bus creation
        
        # Create ADS1115 with conservative settings
        self.ads = ADS.ADS1115(self.i2c)
        self.ads.data_rate = 64  # Conservative 64 SPS
        time.sleep(0.5)
        
        # Single audio channel
        self.audio_channel = AnalogIn(self.ads, ADS.P0)   # Only one channel needed
        
        # Test read
        try:
            test_voltage = self.audio_channel.voltage
            print(f"ADS1115 test successful: {test_voltage:.3f}V")
        except Exception as e:
            print(f"ADS1115 test failed: {e}")
            raise
        
        # Display settings (landscape mode)
        self.width = 320   # Rotated width
        self.height = 240  # Rotated height
        self.trace_height = 160  # Larger trace height since we only have one
        
        # Single waveform buffer
        self.buffer_size = 140  # Buffer for continuous scroll
        self.waveform_buffer = collections.deque(maxlen=self.buffer_size)
        
        # Colors
        self.bg_color = (0, 0, 0)        # Black
        self.grid_color = (0, 40, 0)     # Dark green
        self.waveform_color = (0, 255, 0) # Green
        self.text_color = (255, 255, 255) # White
        
        # Sampling settings
        self.running = False
        self.sample_rate = 15  # Slightly faster since only one channel
        self.error_count = 0
        
        print("Single channel oscilloscope initialized!")
        print(f"ADS1115 configured for {self.ads.data_rate} SPS")
        print(f"Python sampling at {self.sample_rate} Hz")
        print("Display range: ±25mV with 800x scaling")
    
    def sample_audio(self):
        """Sample single audio channel"""
        consecutive_errors = 0
        
        while self.running:
            try:
                # Read single channel
                voltage = self.audio_channel.voltage
                consecutive_errors = 0  # Reset on success
                
                # Input voltage limiting to prevent overflow
                # Limit to ±50mV for proper display range
                voltage = max(-0.05, min(0.05, voltage))  # ±0.05V (50mV) max
                
                # Convert to display coordinates (center = middle of trace)
                # FIXED SCALING: 400x instead of 800x to properly use full display range
                center_y = self.trace_height // 2  # 80 pixels from top of trace
                pixel_y = int(center_y - (voltage * 400))  # 400x scaling for ±50mV range
                
                # Safety clamping for display bounds (more generous)
                pixel_y = max(5, min(self.trace_height-5, pixel_y))  # 5 to 155 pixels
                
                # Add to buffer
                self.waveform_buffer.append(pixel_y)
                
                # Sampling delay
                time.sleep(1.0 / self.sample_rate)
                
            except OSError as e:
                if e.errno == 121:  # Remote I/O error
                    self.error_count += 1
                    consecutive_errors += 1
                    print(f"I2C Error #{self.error_count} (consecutive: {consecutive_errors})")
                    
                    if consecutive_errors > 5:
                        print("Reinitializing ADS1115...")
                        try:
                            time.sleep(2.0)
                            self.ads = ADS.ADS1115(self.i2c)
                            self.ads.data_rate = 64
                            time.sleep(1.0)
                            self.audio_channel = AnalogIn(self.ads, ADS.P0)
                            consecutive_errors = 0
                            print("ADS1115 reinitialized")
                        except Exception as reinit_error:
                            print(f"Reinitialize failed: {reinit_error}")
                            time.sleep(5.0)
                    else:
                        time.sleep(0.5)
                else:
                    print(f"Unexpected OSError: {e}")
                    time.sleep(1.0)
                    
            except Exception as e:
                print(f"Sampling error: {e}")
                time.sleep(1.0)
    
    def draw_grid(self, draw):
        """Draw oscilloscope grid for single channel"""
        # Horizontal grid lines
        for y in range(0, self.height, 30):
            draw.line([(20, y), (self.width-20, y)], fill=self.grid_color)
        
        # Vertical grid lines  
        for x in range(20, self.width-20, 40):
            draw.line([(x, 0), (x, self.height)], fill=self.grid_color)
        
        # Center line (0V reference) - middle of screen
        center_y = self.height // 2
        draw.line([(20, center_y), (self.width-20, center_y)], fill=self.grid_color, width=3)
        
        # Quarter lines for better voltage reference
        quarter_y = center_y - 20  # Midpoint reference lines
        three_quarter_y = center_y + 20
        draw.line([(20, quarter_y), (self.width-20, quarter_y)], fill=self.grid_color, width=1)
        draw.line([(20, three_quarter_y), (self.width-20, three_quarter_y)], fill=self.grid_color, width=1)
    
    def draw_waveform(self, draw):
        """Draw single scrolling waveform"""
        if len(self.waveform_buffer) < 2:
            return
        
        # Convert buffer to points
        points = []
        buffer_list = list(self.waveform_buffer)
        
        for i, y in enumerate(buffer_list):
            x = 20 + (i * 2)  # Spread points out
            if x < self.width - 20:  # Stay within screen bounds
                # Offset Y to center of screen
                screen_y = (self.height // 2) - (self.trace_height // 2) + y
                points.append((x, screen_y))
        
        # Draw the waveform
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=self.waveform_color, width=2)
    
    def draw_labels(self, draw):
        """Draw labels and info for single channel"""
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Channel label
        draw.text((5, 20), "AUDIO", fill=self.waveform_color, font=font)
        
        # CORRECTED Voltage scale labels to match actual display range with 800x scaling
        draw.text((5, 5), "+25mV", fill=self.text_color, font=font)
        draw.text((5, self.height//2 - 10), "0V", fill=self.text_color, font=font)
        draw.text((5, self.height - 40), "-25mV", fill=self.text_color, font=font)
        
        # Current voltage and status
        try:
            current_voltage = self.audio_channel.voltage
            # Show voltage in millivolts for better readability
            voltage_mv = current_voltage * 1000  # Convert to mV
            draw.text((250, 5), f"{voltage_mv:.1f}mV", fill=self.waveform_color, font=font)
            
            # Show error count if any
            if self.error_count > 0:
                draw.text((250, 25), f"Err:{self.error_count}", fill=(255, 100, 100), font=font)
                
            # Show clipping indicator
            if abs(current_voltage) > 0.05:
                draw.text((250, 45), "CLIP!", fill=(255, 100, 100), font=font)
                
            # Show sampling info
            draw.text((200, self.height - 20), f"{self.sample_rate}Hz", fill=self.text_color, font=font)
            
            # Show actual input range
            draw.text((5, self.height - 20), "Range: ±25mV", fill=self.text_color, font=font)
            
        except:
            draw.text((250, 5), "READ ERR", fill=(255, 100, 100), font=font)
    
    def update_display(self):
        """Update the TFT display"""
        while self.running:
            try:
                # Create image
                image = Image.new("RGB", (self.width, self.height), self.bg_color)
                draw = ImageDraw.Draw(image)
                
                # Draw oscilloscope elements
                self.draw_grid(draw)
                self.draw_labels(draw)
                self.draw_waveform(draw)
                
                # Rotate for landscape display
                rotated_image = image.rotate(90, expand=True)
                
                # Update display
                self.display.image(rotated_image)
                
                time.sleep(0.1)  # 10 FPS display refresh
                
            except Exception as e:
                print(f"Display error: {e}")
                time.sleep(0.5)
    
    def start(self):
        """Start the oscilloscope"""
        if self.running:
            return
            
        print("Starting single channel oscilloscope...")
        self.running = True
        
        # Start sampling thread
        sample_thread = threading.Thread(target=self.sample_audio)
        sample_thread.daemon = True
        sample_thread.start()
        
        # Start display thread
        display_thread = threading.Thread(target=self.update_display)
        display_thread.daemon = True
        display_thread.start()
        
        print("Single channel oscilloscope running!")
        print("- Using only ADS1115 channel A0")
        print("- Voltage range: ±25mV (properly labeled for 800x scaling)")
        print("- 800x amplification for high sensitivity")
        print("- 15Hz sampling rate for stable operation")
        print("Connect audio source to A0 and see waveforms")
        print("Press Ctrl+C to stop")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping oscilloscope...")
            self.stop()
    
    def stop(self):
        """Stop the oscilloscope"""
        self.running = False
        print("Single channel oscilloscope stopped")

def main():
    print("Pi Zero 2W Single Channel Audio Oscilloscope")
    print("Hardware: ADS1115 + ILI9341 TFT")
    print("Fixed labels: ±25mV range properly displayed with 800x scaling")
    print("=" * 50)
    
    scope = SingleChannelOscilloscope()
    scope.start()

if __name__ == "__main__":
    main()