import minimalmodbus
import time
from datetime import datetime, timedelta

def setup_sensor():
    # Initialize Modbus RTU instrument
    instrument = minimalmodbus.Instrument('COM3', 1)  # slave address=1
    
    # Serial settings
    instrument.serial.baudrate = 9600
    instrument.serial.bytesize = 8
    instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = 1
    
    # Modbus RTU mode
    instrument.mode = minimalmodbus.MODE_RTU
    instrument.clear_buffers_before_each_transaction = True
    
    return instrument

def read_temperatures(instrument, valid_channels=None):
    try:
        if valid_channels is None:
            valid_channels = set(range(4))  # All channels initially valid
        
        if not valid_channels:  # If no valid channels left
            return None
            
        values = instrument.read_registers(0, 4, functioncode=3)
        temperatures = []
        new_valid_channels = valid_channels.copy()
        
        for i in range(4):
            if i in valid_channels:
                temp = values[i]/10.0
                if temp > 1000:
                    new_valid_channels.remove(i)
                    temperatures.append(None)
                else:
                    temperatures.append(temp)
            else:
                temperatures.append(None)
                
        return temperatures, new_valid_channels
    except Exception as e:
        print(f"Error reading temperatures: {e}")
        return None, valid_channels

def main():
    try:
        duration_minutes = 1
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        instrument = setup_sensor()
        print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"预计结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 40)
        
        valid_channels = set(range(4))  # Track valid channels
        
        while datetime.now() < end_time:
            result = read_temperatures(instrument, valid_channels)
            if result is not None:
                temps, valid_channels = result
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"时间: {current_time}")
                for i, temp in enumerate(temps):
                    if temp is not None:
                        print(f"Channel {i+1} Temperature: {temp}°C")
                print("-" * 40)
            time.sleep(10)
            
        print("采集完成！")
            
    except Exception as e:
        print(f"Connection error: {e}")
        print("Please check if device is connected and COM3 port is correct")

if __name__ == "__main__":
    main()