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


Requirements
==============================

* Python (2.7 or later, 3.3 or later)

* Pyverilog (Python-based Verilog HDL Design Processing Toolkit)
    - Install from pip: 'pip install pyverilog' for Python2.7 or 'pip3 install pyverilog' for Python3
    - Install from github into this package: 'cd Pycoram; git clone https://github.com/shtaxxx/Pyverilog.git; cd pycoram; ln -s ../Pyverilog/pyverilog'
* Jinja2 (2.7 or later)
   - The code generator uses Jinja2 template engine.
   - 'pip install jinja2' (for Python 2.x) or 'pip3 install jinja2' (for Python 3.x)


Installation
==============================

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
        ).els(
            count(count + 1)
        ))
    
    m.Always(Posedge(clk))(
        If(rst)(
            led(0)
        ).els(
            If(count == 1024 - 1)(
                led(led + 1)
            )
        ))
    
    return m

led = mkLed()
verilog = led.toVerilog()
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
  count <= (count + 1);
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


Class and method
==============================

Module(name)
--------------------

is corresponding to 'module' in Verilog HDL.
The Module class has several class methods to describe signals and assignments.

Module.Input(name, width=None, length=None, signed=False, value=None)
--------------------

is a class method to add a input port to the module.

Module.Output(name, width=None, length=None, signed=False, value=None)
--------------------

is a class method to add a output port to the module.

Module.Inout(name, width=None, length=None, signed=False, value=None)
--------------------

is a class method to add a inout port to the module.

Module.Reg(name, width=None, length=None, signed=False, value=None)
--------------------

Module.Wire(name, width=None, length=None, signed=False, value=None)
--------------------

Module.Parameter(name, value, width=None, length=None, signed=False)
--------------------

Module.Localparam(name, value, width=None, length=None, signed=False)
--------------------

Module.Always(sensitivity, statement)
--------------------

Module.Assign(left, right)
--------------------

Module.Instance(module, instname, params, ports)
--------------------


Publication
==============================

Not yet.


Related Project
==============================

[Pyverilog](http://shtaxxx.github.io/Pyverilog/)
- Python-based Hardware Design Processing Toolkit for Verilog HDL

[PyCoRAM](http://shtaxxx.github.io/PyCoRAM/)
- Python-based Portable IP-core Synthesis Framework for FPGA-based Computing
