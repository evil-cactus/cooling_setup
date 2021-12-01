ser=serial.Serial('/dev/ttyACM0', baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=2.0)
ser.reset_output_buffer()
ser.reset_input_buffer()
ser.write("VSET:1.0\n".encode())
ser.write("VSET:1\n".encode())
ser.write("VSET:2\n".encode())
ser.write("VSET:2.2\n".encode())


