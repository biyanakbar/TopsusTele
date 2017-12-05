# Simple demo of reading each analog input from the ADS1x15 and printing it to
# the screen.
# Author: Tony DiCola
# License: Public Domain
import time

# Import the ADS1x15 module.
import Adafruit_ADS1x15

import io  # used to create file streams
import fcntl  # used to access I2C parameters like addresses

import time  # used for sleep delay and timestamps

import os
from time import sleep  # Import sleep module for timing




class atlas_i2c:
    long_timeout = 1.5  # the timeout needed to query readings and
                        #calibrations
    short_timeout = .5  # timeout for regular commands
    default_bus = 1  # the default bus for I2C on the newer Raspberry Pis,
                     # certain older boards use bus 0
    default_address = 97  # the default address for the DO sensor

    def __init__(self, address=default_address, bus=default_bus):
        # open two file streams, one for reading and one for writing
        # the specific I2C channel is selected with bus
        # it is usually 1, except for older revisions where its 0
        # wb and rb indicate binary read and write
        self.file_read = io.open("/dev/i2c-" + str(bus), "rb", buffering=0)
        self.file_write = io.open("/dev/i2c-" + str(bus), "wb", buffering=0)

        # initializes I2C to either a user specified or default address
        self.set_i2c_address(address)

    def set_i2c_address(self, addr):
        # set the I2C communications to the slave specified by the address
        # The commands for I2C dev using the ioctl functions are specified in
        # the i2c-dev.h file from i2c-tools
        I2C_SLAVE = 0x703
        fcntl.ioctl(self.file_read, I2C_SLAVE, addr)
        fcntl.ioctl(self.file_write, I2C_SLAVE, addr)

    def write(self, string):
        # appends the null character and sends the string over I2C
        string += "\00"
        self.file_write.write(bytes(string, 'UTF-8'))

    def read(self, num_of_bytes=31):
        # reads a specified number of bytes from I2C,
        # then parses and displays the result
        res = self.file_read.read(num_of_bytes)  # read from the board
        # remove the null characters to get the response
        response = [x for x in res if x != '\x00']
        if response[0] == 1:  # if the response isnt an error
            # change MSB to 0 for all received characters except the first
            # and get a list of characters
            char_list = [chr(x & ~0x80) for x in list(response[1:])]
            # NOTE: having to change the MSB to 0 is a glitch in the
            # raspberry pi, and you shouldn't have to do this!
            # convert the char list to a string and returns it
            return "Command succeeded " + ''.join(char_list)
        else:
            return "Error " + str(response[0])

    def query(self, string):
        # write a command to the board, wait the correct timeout,
        # and read the response
        self.write(string)

        # the read and calibration commands require a longer timeout
        if((string.upper().startswith("R")) or
           (string.upper().startswith("CAL"))):
            time.sleep(self.long_timeout)
        elif((string.upper().startswith("SLEEP"))):
            return "sleep mode"
        else:
            time.sleep(self.short_timeout)

        return self.read()

    def close(self):
        self.file_read.close()
        self.file_write.close()


    def read_temp_raw(temp_sensor):
    #Read the 2 raw lines of data from the temperature sensor
        f = open(temp_sensor, 'r')
        lines = f.readlines()
        f.close()
        return lines


    def read_temp(temp_sensor):
    # Check the Temp Sensor file for errors and convert to Celcius or Fahrenheit
        lines = read_temp_raw(temp_sensor)
        while lines[0].strip()[-3:] != 'YES':
            sleep(0.2)
            lines = read_temp_raw(temp_sensor)
        temp_result = lines[1].find('t=')
        if temp_result != -1:
            temp_string = lines[1][temp_result + 2:]
            # Use line below for Celsius
            temp = float(temp_string) / 1000.0
            #Uncomment line below for Fahrenheit
            #temp = ((float(temp_string) / 1000.0) * (9.0 / 5.0)) + 32
            return temp

    # Load Raspberry Pi Drivers
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

    # Define data file for temperature sensors
    temp_sensor_1 = '/sys/bus/w1/devices/28-01157127dfff/w1_slave'
    temp_sensor_2 = '/sys/bus/w1/devices/28-xxxxxxxxxxxx/w1_slave'


def main():
    device = atlas_i2c()  # creates the I2C port object,
                          #specify the address or bus if necessary
    print(">> Atlas Scientific sample code")
    print(">> Any commands entered are passed to the board via I2C except:")
    print(">> Address,xx changes the I2C address the Raspberry Pi "
         "communicates with.")
    print(">> Poll,xx.x command continuously polls the board every "
          "xx.x seconds")
    print(" where xx.x is longer than the {} second timeout.".
              format(atlas_i2c.long_timeout))
    print(" Pressing ctrl-c will stop the polling")

    # Create an ADS1115 ADC (16-bit) instance.
    adc = Adafruit_ADS1x15.ADS1115()

    # Or create an ADS1015 ADC (12-bit) instance.
    #adc = Adafruit_ADS1x15.ADS1015()

    # Note you can change the I2C address from its default (0x48), and/or the I2C
    # bus by passing in these optional parameters:
    #adc = Adafruit_ADS1x15.ADS1015(address=0x49, busnum=1)

    # Choose a gain of 1 for reading voltages from 0 to 4.09V.
    # Or pick a different gain to change the range of voltages that are read:
    #  - 2/3 = +/-6.144V
    #  -   1 = +/-4.096V
    #  -   2 = +/-2.048V
    #  -   4 = +/-1.024V
    #  -   8 = +/-0.512V
    #  -  16 = +/-0.256V
    # See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
    GAIN = 1

    # main loop
    while True:
        delaytime = float(60.0)

        print('==============Sensor pH==============')
        # check for polling time being too short,
        # change it to the minimum timeout if too short
        if(delaytime < atlas_i2c.long_timeout):
            print("Polling time is shorter than timeout, "
                  "setting polling time to {}".
                      format(atlas_i2c.long_timeout))
            delaytime = atlas_i2c.long_timeout

        # get the information of the board you're polling
        info = device.query("I").split(",")[1]
        print("Polling {} sensor every {} seconds, press ctrl-c "
              "to stop polling".
                  format(info, delaytime))

        try:
            while True:
                print(device.query("R"))
                time.sleep(delaytime - atlas_i2c.long_timeout)
        except KeyboardInterrupt:
            # catches the ctrl-c command, which breaks the loop above
            print("Continuous polling stopped")


        # Read all the ADC channel values in a list.
        values = [0]*4
        for i in range(4):
            # Read the specified ADC channel using the previously set gain value.
            values[i] = adc.read_adc(i, gain=GAIN)
            # Note you can also pass in an optional data_rate parameter that controls
            # the ADC conversion time (in samples/second). Each chip has a different
            # set of allowed data rate values, see datasheet Table 9 config register
            # DR bit values.
            #values[i] = adc.read_adc(i, gain=GAIN, data_rate=128)
            # Each value will be a 12 or 16 bit signed integer value depending on the
            # ADC (ADS1015 = 12-bit, ADS1115 = 16-bit).
        # Print the ADC values.
        print('')
        print('==============Sensor DO==============')
        print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*values))
        # Pause for half a second.
        time.sleep(delaytime)

        print('')
        print('==============Sensor Suhu==============')
        print("Temperature Sensor 1 = ", read_temp(temp_sensor_1))
        print("Temperature Sensor 2 = ", read_temp(temp_sensor_2))
        sleep(2)   # Read every 2 seconds
        


if __name__ == '__main__':
    main()
