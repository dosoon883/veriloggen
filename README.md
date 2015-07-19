Veriloggen
==============================

A library for constructing a Verilog HDL source code in Python

Copyright (C) 2015, Shinya Takamaeda-Yamazaki

E-mail: shinya\_at\_is.naist.jp


License
==============================

Apache License 2.0
(http://www.apache.org/licenses/LICENSE-2.0)


What's Veriloggen?
==============================

Veriloggen is an open-sourced library for constructing a Verilog HDL source code in Python.

Veriloggen is not a behavior synthesis (or high level synthesis). Veriloggen provides a lightweight abstraction of Verilog HDL AST. You can build up a hardware design written in Verilog HDL very easily by using the AST abstraction and the entire functionality of Python.
 
Veriloggen is not designed for designing a hardware by programmer directly, but is for providing an efficient abstraction to develop a more efficient domain specific language and tools.


Requirements
==============================

* Python (2.7 or later, 3.3 or later)
* Pyverilog (Python-based Verilog HDL Design Processing Toolkit)
    - Install from pip: 'pip install pyverilog' for Python2.7 or 'pip3 install pyverilog' for Python3
    - Otherwise, install from github into this package: 'cd Pycoram; git clone https://github.com/shtaxxx/Pyverilog.git; cd pycoram; ln -s ../Pyverilog/pyverilog'
* Jinja2 (2.7 or later)
   - The code generator (in Pyverilog) uses Jinja2 template engine.
   - 'pip install jinja2' (for Python 2.x) or 'pip3 install jinja2' (for Python 3.x)
* pytest (2.7.2 or later)
   - Examples in Veriloggen use pytest. Install pytest if you check the correctness of the example by yourself.
   - 'pip install -U pytest' (for Python 2.x) or 'pip3 install -U pytest' (for Python 3.x)
* Icarus Verilog (0.9.6 or later)
    - 'iverilog -E' command is used for preprocessing Verilog source code in Pyverilog.


Installation
==============================

On Docker
------------------------------

Dockerfile is available, so that you can try Veriloggen on Docker without any installation on your host platform.

```
cd docker
sudo docker build -t user/veriloggen .
sudo docker run --name veriloggen -i -t user/veriloggen /bin/bash
cd veriloggen/sample/led/
make
```

On your host platform
------------------------------

If you want to use Veriloggen as a general library, you can install on your environment by using setup.py.

If Python 2.7 is used,

    python setup.py install

If Python 3.x is used,

    python3 setup.py install


Getting Started
==============================

You can find some examples in 'veriloggen/sample/'.

Let's begin veriloggen by an example. Create a example Python script in Python as below. A blinking LED hardware is modeled in Python.

```python
import sys
import os
from veriloggen import *

def mkLed():
    m = Module('blinkled')
    width = m.Parameter('WIDTH', 8)
    clk = m.Input('CLK')
    rst = m.Input('RST')
    led = m.OutputReg('LED', width)
    count = m.Reg('count', 32)

    m.Always(Posedge(clk))(
        If(rst)(
            count(0)
        ).Else(
            If(count == 1023)(
                count(0)
            ).Else(
                count(count + 1)
            )
        ))
    
    m.Always(Posedge(clk))(
        If(rst)(
            led(0)
        ).Else(
            If(count == 1024 - 1)(
                led(led + 1)
            )
        ))
    
    return m

if __name__ == '__main__':
    led = mkLed()
    # led.to_verilog(filename='tmp.v')
    verilog = led.to_verilog()
    print(verilog)
```

Run the script.

```
python led.py
```

You will have a complete Verilog HDL source code that is generated by a source code generator of Pyverilog.
Currently a source code generated by Pyverilog has no good indentation. Please prettify it by using a standard text editor.

```verilog
module blinkled #
 (
  parameter WIDTH = 8

 )
 (
  input [0:0] CLK, 
input [0:0] RST, 
output reg [(WIDTH - 1):0] LED

 );
  reg [(32 - 1):0] count;
  always @(posedge CLK)
  begin        
  if(RST) begin        
  count <= 0;
end  
else begin        
  if((count == 1023)) begin        
  count <= 0;
end  
else begin        
  count <= (count + 1);
end 
end 
end 
  always @(posedge CLK)
  begin        
  if(RST) begin        
  LED <= 0;
end  
else begin        
  if((count == 1023)) begin        
  LED <= (LED + 1);
end  

end 
end 
endmodule
```


Publication
==============================

Not yet.


Related Project
==============================

[Pyverilog](https://github.com/shtaxxx/Pyverilog)
- Python-based Hardware Design Processing Toolkit for Verilog HDL
