import pyvisa
from time import sleep

class AgilentSupply():
    def __init__(self, addr='GPIB0::5::INSTR'):
        self.inst = pyvisa.ResourceManager().open_resource(addr)

    def id(self):
        return self.inst.query('*IDN?')
    def setLimits(self, range1='P20V', range2='P8V', v1=12.0, c1=1.0, v2=1.2, c2=0.6):
        self.inst.write(f'INST:SEL OUT1\nVOLT:RANG {range1}\nVOLT {v1}\nCURR {c1}')
        self.inst.write(f'INST:SEL OUT2\nVOLT:RANG {range2}\nVOLT {v2}\nCURR {c2}')

    def asicOff(self):
        self.inst.write(f'INST:SEL OUT2\nVOLT:RANG P8V\nVOLT {0}')

    def asicOn(self):
        self.inst.write(f'INST:SEL OUT2\nVOLT:RANG P8V\nVOLT {1.2}')

    def turnOn(self):
        #check Limits before turning on
        vEm,cEm,vAsic,cAsic=self.readLimits()
        if (vEm==12) and (cEm==1) and (vAsic==1.2) and (cAsic==0.6):
            self.inst.write('OUTP ON')
        else:
            print('ERROR, WRONG LIMITS')
            e_vem="" if vEm==12 else "SHOULD BE 12"
            e_cem="" if cEm==1 else "SHOULD BE 1"
            e_vas="" if vAsic==1.2 else "SHOULD BE 1.2"
            e_cas="" if cAsic==0.6 else "SHOULD BE 0.6"
            print(f'V_Emulator = {vEm} {e_vem}')
            print(f'I_Emulator = {cEm} {e_cem}')
            print(f'V_ASIC     = {vAsic} {e_vas}')
            print(f'I_ASIC     = {cAsic} {e_cas}')
    def turnOff(self):
        self.inst.write('OUTP OFF')

    def read(self, verbose=False):
        curr1=float(self.inst.query('INST:SEL OUT1\nMEAS:CURR:DC?')[:-1])
        curr2=float(self.inst.query('INST:SEL OUT2\nMEAS:CURR:DC?')[:-1])

        volt1=float(self.inst.query('INST:SEL OUT1\nMEAS:VOLT:DC?')[:-1])
        volt2=float(self.inst.query('INST:SEL OUT2\nMEAS:VOLT:DC?')[:-1])
        if verbose:
            print(f'V1={volt1}, C1={curr1}')
            print(f'V2={volt2}, C2={curr2}')
        return volt1,curr1,volt2,curr2

    def readLimits(self, verbose=False):
        curr1=float(self.inst.query('INST:SEL OUT1\nCURR?')[:-1])
        curr2=float(self.inst.query('INST:SEL OUT2\nCURR?')[:-1])

        volt1=float(self.inst.query('INST:SEL OUT1\nVOLT?')[:-1])
        volt2=float(self.inst.query('INST:SEL OUT2\nVOLT?')[:-1])
        if verbose:
            print('Limits')
            print(f'V1={volt1}, C1={curr1}')
            print(f'V2={volt2}, C2={curr2}')
        return volt1,curr1,volt2,curr2


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--on', default=False, action='store_true', help='Turn on outputs')
    parser.add_argument('--off', default=False, action='store_true', help='Turn off outputs')
    parser.add_argument('--cycle', default=False, action='store_true', help='Cycle power supply')
    parser.add_argument('--set', default=False, action='store_true', help='Set current and voltages')
    parser.add_argument('--read', default=False, action='store_true', help='Read current and voltages')
    parser.add_argument('--limits', default=False, action='store_true', help='Read back current and voltage limit setting')
    parser.add_argument('--id', default=False, action='store_true', help='Get device ID')
    parser.add_argument('--v1', type=str, default="12", help="Output 1 Voltage")
    parser.add_argument('--c1', type=str, default="1", help="Output 1 Current Limit")
    parser.add_argument('--r1', type=str, default="P20V", help="Output 1 Voltage Range")
    parser.add_argument('--v2', type=str, default="1.2", help="Output 2 Voltage")
    parser.add_argument('--c2', type=str, default="0.6", help="Output 2 Current Limit")
    parser.add_argument('--r2', type=str, default="P8V", help="Output 2 Voltage Range")
    args = parser.parse_args()

    agilent=AgilentSupply()

    if args.id:
        print(agilent.id())
    if args.on:
        agilent.turnOn()
    if args.off:
        agilent.turnOff()
    if args.cycle:
        agilent.turnOff()
        sleep(5)
        agilent.turnOn()
    if args.read:
        agilent.read(verbose=True)
    if args.limits:
        agilent.readLimits(verbose=True)
    if args.set:
        agilent.setLimits(args.r1, args.r2, args.v1, args.c1, args.v2, args.c2)


