import minimalmodbus
import time

def setup_sensor():
    """初始化Modbus RTU设备"""
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

def read_current_temperatures(instrument):
    """读取当前温度值"""
    try:
        values = instrument.read_registers(0, 4, functioncode=3)
        temperatures = [value/10.0 for value in values]
        return temperatures
    except Exception as e:
        print(f"Error reading temperatures: {e}")
        return None

def write_temperature_correction(instrument, channel, correction_value):
    """写入温度校正值到0x0040-0x0043寄存器
    
    Args:
        instrument: Modbus设备对象
        channel: 通道号 (0-3 对应 CH0-CH3)
        correction_value: 校正值 (°C)
    """
    try:
        # 根据PDF文档，校正寄存器地址: 0x0040-0x0043 (CH0-CH3)
        correction_register = 0x0040 + channel
        
        # 将校正值转换为设备格式 (乘以10)
        correction_int = int(correction_value * 10)
        
        # 处理负值 - 转换为16位有符号数的无符号表示
        if correction_int < 0:
            correction_int = 65536 + correction_int
        
        # 确保值在16位范围内
        correction_int = correction_int & 0xFFFF
        
        # 写入校正值寄存器 (使用功能码06 - Write Single Register)
        instrument.write_register(correction_register, correction_int, functioncode=6)
        print(f"✓ Channel {channel+1} (CH{channel}) 校正值 {correction_value:+.1f}°C 写入成功")
        print(f"  寄存器: 0x{correction_register:04X}, 值: 0x{correction_int:04X}")
        return True
        
    except Exception as e:
        print(f"✗ Channel {channel+1} 校正失败: {e}")
        return False

def input_calibration_values():
    """获取用户输入的校准值"""
    calibration_values = {}
    
    print("PT100 温度校正程序")
    print("=" * 50)
    print("校正值说明:")
    print("• 正值: 当前读数偏低，需要增加显示值")
    print("• 负值: 当前读数偏高，需要减少显示值")
    print("• 范围: -327.0°C 到 +327.0°C (精度: 0.1°C)")
    print("• 寄存器: 0x0040-0x0043 (只写)")
    print("-" * 50)
    print("请输入各通道的温度校正值 (直接按Enter跳过该通道):")
    print()
    
    for channel in range(4):
        while True:
            try:
                user_input = input(f"CH{channel} (Channel {channel+1}) 校正值 (°C): ").strip()
                
                if user_input == "":
                    print(f"跳过 Channel {channel+1}")
                    break
                
                correction_value = float(user_input)
                
                # 限制校正值范围
                if -327.0 <= correction_value <= 327.0:
                    calibration_values[channel] = correction_value
                    print(f"✓ Channel {channel+1} 校正值: {correction_value:+.1f}°C")
                    break
                else:
                    print("❌ 校正值必须在 -327.0°C 到 +327.0°C 之间")
                    
            except ValueError:
                print("❌ 请输入有效数值或按Enter跳过")
    
    return calibration_values

def main():
    try:
        # 初始化设备
        instrument = setup_sensor()
        
        # 读取当前温度值
        print("📊 正在读取当前温度值...")
        current_temps = read_current_temperatures(instrument)
        
        if current_temps:
            print("\n当前温度读数:")
            for i, temp in enumerate(current_temps):
                print(f"  CH{i} (Channel {i+1}): {temp}°C")
        else:
            print("❌ 无法读取温度值，请检查设备连接")
            return
        
        print("\n" + "=" * 50)
        
        # 获取校正值输入
        calibration_values = input_calibration_values()
        
        if not calibration_values:
            print("ℹ️ 未输入任何校正值，程序退出")
            return
        
        # 确认校正操作
        print("\n" + "=" * 50)
        print("📝 即将写入以下温度校正值:")
        for channel, correction in calibration_values.items():
            register_addr = 0x0040 + channel
            print(f"  CH{channel}: {correction:+.1f}°C → 寄存器 0x{register_addr:04X}")
        
        print("\n⚠️  注意: 校正寄存器是只写的，写入后无法读取验证!")
        confirm = input("\n确认执行校正? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("❌ 校正操作已取消")
            return
        
        # 执行校正写入
        print("\n📤 正在写入校正值...")
        print("-" * 30)
        success_count = 0
        
        for channel, correction in calibration_values.items():
            if write_temperature_correction(instrument, channel, correction):
                success_count += 1
            time.sleep(0.2)  # 给设备处理时间
        
        print("-" * 30)
        print(f"✅ 校正完成! 成功: {success_count}/{len(calibration_values)} 个通道")
        
        # 等待设备处理
        print("\n⏳ 等待设备处理校正值 (3秒)...")
        time.sleep(3)
        
        # 读取校正后的温度值
        print("📊 读取校正后的温度值...")
        new_temps = read_current_temperatures(instrument)
        
        if new_temps and current_temps:
            print("\n温度对比:")
            print("通道   校正前    校正后    变化")
            print("-" * 35)
            for i, (old_temp, new_temp) in enumerate(zip(current_temps, new_temps)):
                if i in calibration_values:
                    change = new_temp - old_temp
                    expected = calibration_values[i]
                    print(f"CH{i}   {old_temp:6.1f}°C  {new_temp:6.1f}°C  {change:+5.1f}°C (期望:{expected:+.1f}°C)")
                else:
                    print(f"CH{i}   {old_temp:6.1f}°C  {new_temp:6.1f}°C   未校正")
        
        print("\n🎉 校正程序执行完毕!")
        
    except Exception as e:
        print(f"❌ 程序执行错误: {e}")
        print("请检查设备连接和通信设置")

if __name__ == "__main__":
    main()