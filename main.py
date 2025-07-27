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

def read_temperatures(instrument):
    try:
        values = instrument.read_registers(0, 4, functioncode=3)
        temperatures = []
        
        for i in range(4):
            temp = values[i]/10.0
            temperatures.append(temp)
                
        return temperatures
    except Exception as e:
        print(f"Error reading temperatures: {e}")
        return None

def main():
    try:
        duration_minutes = 1
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        instrument = setup_sensor()
        print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"预计结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 40)
        
        while datetime.now() < end_time:
            temps = read_temperatures(instrument)
            if temps is not None:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"时间: {current_time}")
                for i, temp in enumerate(temps):
                    print(f"Channel {i+1} Temperature: {temp}°C")
                print("-" * 40)
            time.sleep(1)
            
        print("采集完成！")
            
    except Exception as e:
        print(f"Connection error: {e}")
        print("Please check if device is connected and COM3 port is correct")

if __name__ == "__main__":
    main()