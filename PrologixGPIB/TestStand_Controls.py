from plx_gpib_ethernet import PrologixGPIBEthernet
from time import sleep

GPIBAddresses={46:6,
              48:8,
              }

class psControl:
    def __init__(self, *args, **kwargs):
        self.gpib = PrologixGPIBEthernet(*args, **kwargs)
        self.gpib.connect()
        self.board=None

    def close(self):
        self.gpib.close()

    def disconnect(self):
        self.gpib.disconnect()

    def select(self,board):
        self.gpib.select(GPIBAddresses[board])
        self.board=board

    def ASICOn(self,board=None):
        if not board is None:
            self.gpib.select(GPIBAddresses[board])
            self.board=board
        else:
            print(f'Turning on ASIC for board {board}')

        self.gpib.write("VOLT 1.2")
        self.gpib.write("CURR 0.6")
        self.gpib.write("OUTP ON")

    def ASICOff(self,board=None):
        if not board is None:
            self.gpib.select(GPIBAddresses[board])
            self.board=board
        else:
            print(f'Turning off ASIC for board {board}')

        self.gpib.select(GPIBAddresses[board])
        self.gpib.write("OUTP OFF")

    def Read_Power(self,board=None):
        if not board is None:
            self.gpib.select(GPIBAddresses[board])
            self.board=board
        else:
            print(f'Reading from board {board}')

        v=self.gpib.query("MEAS:VOLT?")[:-2]
        i=self.gpib.query("MEAS:CURR?")[:-2]
        return v,i

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--On', default=False, action='store_true', help='Turn on ECON-T ASIC')
    parser.add_argument('--Off', default=False, action='store_true', help='Turn off ECON-T ASIC')
    parser.add_argument('--disconnect', default=False, action='store_true', help='Disconnect gpib (set back to local mode')
    parser.add_argument('--read', default=False, action='store_true', help='Read power')
    parser.add_argument('--logging', default=False, action='store_true', help='Start power monitoring')
    parser.add_argument('--logName', default='logFile.log', help='log name')
    parser.add_argument('--time', default=15, type=float,help='Frequency (in seconds) of how often to read the power')
    parser.add_argument('--ip', default='192.168.0.50', help='IP Address of the gpib controller')
    parser.add_argument('--board', default=46, type=int, help='Board number of hexacontroller (used to determing which power supply to control)')

    args = parser.parse_args()

    ps=psControl(host=args.ip)

    if args.On:
        ps.ASICOn(args.board)
    if args.Off:
        ps.ASICOff(args.board)
    if args.read:
        v,i=ps.Read_Power(args.board)
        print(v,i)
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
                v_ASIC,i_ASIC=ps.Read_Power(args.board)
                logging.info(f'ASIC Voltage: {v_ASIC}, ASIC Current:{i_ASIC}')
                sleep(args.time)
        except KeyboardInterrupt:
            logging.info(f'Closing')

    if args.disconnect:
        ps.select(args.board)
        ps.disconnect()
        
    ps.close()
