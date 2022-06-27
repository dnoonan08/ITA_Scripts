from plx_gpib_ethernet import PrologixGPIBEthernet
from time import sleep
class psControl:
    def __init__(self, Addr=5, *args, **kwargs):
        self.gpib = PrologixGPIBEthernet(*args, **kwargs)
        self.gpib.connect()
        self.gpib.select(Addr)

    def close(self):
        self.gpib.close()

    def disconnect(self):
        self.gpib.disconnect()

    def hexacontrollerOn(self):
        self.gpib.write("INST:SEL OUT1\nVOLT 12.0")
        self.gpib.write("INST:SEL OUT1\nCURR 1.0")
        self.gpib.write("INST:SEL OUT1\nOUTP ON")

    def hexacontrollerOff(self):
        self.gpib.write("INST:SEL OUT1\nOUTP OFF")

    def ECONT_On(self):
        self.gpib.write("INST:SEL OUT2\nVOLT 1.20")
        self.gpib.write("INST:SEL OUT2\nCURR 0.60")
        self.gpib.write("INST:SEL OUT2\nOUTP ON")

    def ECONT_Off(self):
        self.gpib.write("INST:SEL OUT2\nOUTP OFF")

    def ID(self):
        print(self.gpib.query("*IDN?")[:-1])

    def Read_Power_Hexacontroller(self):
        v=self.gpib.query("INST:SEL OUT1\nMEAS:VOLT?")[:-1]
        i=self.gpib.query("INST:SEL OUT1\nMEAS:CURR?")[:-1]
        return float(v),float(i)

    def Read_Power_ECON(self):
        v=self.gpib.query("INST:SEL OUT2\nMEAS:VOLT?")[:-1]
        i=self.gpib.query("INST:SEL OUT2\nMEAS:CURR?")[:-1]
        return float(v),float(i)

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--HexOn', default=False, action='store_true', help='Turn on hexacontroller')
    parser.add_argument('--HexOff', default=False, action='store_true', help='Turn off hexacontroller')
    parser.add_argument('--ECONOn', default=False, action='store_true', help='Turn on ECON-T ASIC')
    parser.add_argument('--ECONOff', default=False, action='store_true', help='Turn off ECON-T ASIC')
    parser.add_argument('--logging', default=False, action='store_true', help='Start power monitoring')
    parser.add_argument('--read', default=False, action='store_true', help='Read power')
    parser.add_argument('--ID', default=False, action='store_true', help='Read id numbers')
    parser.add_argument('--disconnect', default=False, action='store_true', help='Disconnect gpib')
    parser.add_argument('--logName', default='logFile.log', help='log name')
    parser.add_argument('--time', default=15, type=float, help='Frequency (in seconds) of how often to read the power')
    parser.add_argument('--ip', default='192.168.206.50', help='IP Address of the gpib controller')
    args = parser.parse_args()

    ps=psControl(host=args.ip)

    if args.ID:
        ps.ID()
    if args.HexOn:
        ps.hexacontrollerOn()
    if args.HexOff:
        ps.hexacontrollerOff()
    if args.ECONOn:
        ps.ECONT_On()
    if args.ECONOff:
        ps.ECONT_Off()
    if args.read:
        v_ASIC,i_ASIC=ps.Read_Power_ECON()
        v_FPGA,i_FPGA=ps.Read_Power_Hexacontroller()
        print(f'FPGA Voltage: {v_FPGA}, FPGA Current: {i_FPGA}, ASIC Voltage: {v_ASIC}, ASIC Current:{i_ASIC}')
    if args.logging:
        import logging
        import time

        logging.basicConfig(filename=args.logName,
                            level=logging.INFO,
                            format='%(asctime)4s %(message)s',
                            )
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)4s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)

        try:
            while True:
                v_ASIC,i_ASIC=ps.Read_Power_ECON()
                v_FPGA,i_FPGA=ps.Read_Power_Hexacontroller()
                logging.info(f'FPGA Voltage: {v_FPGA:.03f}, FPGA Current: {i_FPGA:.03f}, ASIC Voltage: {v_ASIC:.03f}, ASIC Current:{i_ASIC:.03f}')
                sleep(args.time)
        except KeyboardInterrupt:
            logging.info(f'Closing')

    if args.disconnect:
        ps.disconnect()
    ps.close()
