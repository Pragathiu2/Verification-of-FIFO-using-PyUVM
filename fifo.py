import cocotb
import random
import logging
from cocotb.triggers import Timer, RisingEdge, ClockCycles, Event, FallingEdge
from cocotb.clock import Clock
from cocotb_coverage.crv import Randomized
from cocotb.queue import Queue
from cocotb.utils import get_sim_time


# transaction : data members for each input and output port


class transaction(Randomized):
    def __init__(self, wr = 1, rd = 0, din = 0,dout = 0, empty = 0, full = 0):
        Randomized.__init__(self)
        self.wr    = wr
        self.rd    = rd 
        self.din   = din 
        self.dout  = dout
        self.empty = empty
        self.full  = full
        
        
        
        self.add_rand("wr", list(range(2)))
        self.add_rand("rd", list(range(2)))
        self.add_rand("din", list(range(16)))
        
        self.add_constraint(lambda rd,wr: rd != wr)
        
    def print_in(self, tag = ""):
        print(tag,'wr:',self.wr,'rd:',self.rd,'din:',int(self.din))
    
    def print_out(self, tag = ""):
        print(tag,'wr:',self.wr,'rd:',self.rd,'din:',int(self.din),'dout:',int(self.dout),'e:',self.empty,'f:',self.full)    

        
#generator : Generate random transactions for DUT
        
class generator():
    def __init__(self, queue, event, count):
        self.queue = queue
        self.event = event
        self.count = count
        self.event.clear()

    async def gen_data(self):
            for i in range(self.count):
                t = transaction()
                t.randomize()
                t.print_in("[GEN]")
                #print('[GEN]: din:', t.din, '@ : ',str(get_sim_time(units = 'ns')))
                await self.queue.put(t)
                await self.event.wait()
                self.event.clear()
                
   
   
   
                
# Apply random transactions to DUT                

class driver():
    def __init__(self, queue, dut):
        self.queue = queue
        self.dut = dut
        
    async def reset_dut(self):
        self.dut.rst.value = 1
        self.dut.wr.value  = 0
        self.dut.rd.value  = 0
        self.dut.din.value = 0
        print('--------Reset Applied','@ : ',str(get_sim_time(units = 'ns')),'----------------')
        await ClockCycles(self.dut.clk,5)
        print('--------Reset Removed','@ : ',str(get_sim_time(units = 'ns')),'----------------')
        print('-------------------------------------------------------------------------------')
        self.dut.rst.value = 0

    async def recv_data(self):
        while True:
            temp = transaction()
            temp = await self.queue.get()
            #print('[DRV]: din:', temp.din,'@ : ',str(get_sim_time(units = 'ns')))
            temp.print_in('[DRV]')  
            self.dut.din.value = temp.din
            self.dut.wr.value = temp.wr
            self.dut.rd.value = temp.rd
            
            
            await RisingEdge(self.dut.clk)
            self.dut.wr.value = 0
            self.dut.rd.value = 0
            await RisingEdge(self.dut.clk)






# collect response of DUT

class monitor():
    def __init__(self, dut,queue):
        self.dut   = dut
        self.queue = queue

    async def sample_data(self):
        while True:
            temp = transaction()
            await RisingEdge(self.dut.clk)

            temp.din = self.dut.din.value
            temp.wr = self.dut.wr.value
            temp.rd = self.dut.rd.value

            await RisingEdge(self.dut.clk)
            temp.dout = self.dut.dout.value
            temp.full = self.dut.full.value
            temp.empty = self.dut.empty.value
            
            await self.queue.put(temp)
            #print('[MON]','din:',temp.din,'dout:',temp.dout,'@ :', str(get_sim_time(units = 'ns')))
            temp.print_out("[MON]")




#compare with expected data

class scoreboard():
    def __init__(self,queue,event):
        self.queue = queue
        self.event = event
        self.arr = list()

    async def compare_data(self):
        while True:
            temp = await self.queue.get()
            temp.print_out('[SCO]')           
            #print('[SCO]','din:',temp.din,'dout:',temp.dout,'@ :', str(get_sim_time(units = 'ns')))
            if(temp.wr == 1):
                print('Data Stored in FIFO')
                self.arr.append(temp.din)
                print('Updated List->',self.arr)
            elif(temp.rd == 1):
                if len(self.arr) == 0 :
                    print('FIFO is empty')
                elif (temp.dout == self.arr.pop(0)):
                    print('Test Passed')
                    print('Updated List->',self.arr)
                else:
                    print('Test Failed : Read Data Mismatch')
            else:
                print('Test Failed : Unexpected input stimulus')
                
            print('-------------------------------------------')
   
            self.event.set()
            
  
       

@cocotb.test()
async def test(dut):
    queue1 = Queue()
    queue2 = Queue()
    event = Event()
    gen = generator(queue1, event, 30)
    drv = driver(queue1, dut)
    
    mon = monitor(dut,queue2)
    sco = scoreboard(queue2,event)
    
    cocotb.start_soon(Clock(dut.clk, 10, 'ns').start())
    
    await drv.reset_dut()
    
    cocotb.start_soon(gen.gen_data())
    cocotb.start_soon(drv.recv_data())
    cocotb.start_soon(mon.sample_data())
    cocotb.start_soon(sco.compare_data())

    await Timer(620, 'ns')
