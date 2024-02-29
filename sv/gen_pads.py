#! /usr/bin/python3
''' A utility script for generating pads from system/verilog input and output lines.'''

known_substitutions = {}

def parse_line(line: str):
    ''' Read a verilog input/output line and return a tuple with data needed to construct pads.

        Returns a tuple of the following form:
            (  
                bool: True if this is an output,
                int:  Number of wires,
                str:  Name of the bus/wire
            )
        For example, the line "input logic [31:0] bus;" should get parsed to (False, 32, "bus")
    '''

    # Initial assumptions
    is_output = False
    wire_count = 1
    bus_name = "none"

    tokens = line.strip().split()
    for token in tokens:
        if any(typestr == token.strip() for typestr in ['reg', 'wire', 'integer', 'real', 'time', 'realtime', 'logic', 'bit', 'byte', 'shortint', 'int', 'longint', 'shortreal']):
            continue # skip types
        elif 'output' in token:
            is_output = True
        elif '[' in token:
            # Assume we have the whole [n:m] bit in this token
            n, m = token.strip()[1:-1].split(':')
            try:
                wire_count = int(n) + 1 - int(m)
            except ValueError:
                if token in known_substitutions.keys():
                    wire_count = known_substitutions[token]
                else:
                    wire_count = int(input(f'Could not parse "[{token}]". How many wires is that? '))
                    known_substitutions[token] = wire_count
        else:
            # If we still don't have a match, it's probably the name
            bus_name = ''.join([c for c in token if c.isalnum() or c == '_'])
    return (is_output, wire_count, bus_name)

def gen_input_pad(pin_num: int, wire_name: str, bus=0):
    ''' Generate an input pad string

        If the wire is part of a bus, specify the address with bus (e.g. bus=12 for addr[12])
    '''
    return f'PADIN  p{pin_num:03}(.DI({wire_name}_i{"["+str(bus)+"]" if bus else ""}), .PAD({wire_name}{"["+str(bus)+"]" if bus else ""}));'

def gen_output_pad(pin_num: int, wire_name: str, bus=0):
    ''' Generate an output pad string

        If the wire is part of a bus, specify the address with bus (e.g. bus=12 for addr[12])
    '''
    return f'PADOUT p{pin_num:03}(.DO({wire_name}_o{"["+str(bus)+"]" if bus else ""}), .PAD({wire_name}{"["+str(bus)+"]" if bus else ""}));'

def gen_pads(io_lines: list):
    ''' Given a list of verilog io lines, generates a list of pad strings.'''
    pad_lines = []
    for line in io_lines:
        (is_output, wire_count, name) = parse_line(line)
        pad_generator = gen_output_pad if is_output else gen_input_pad
        if wire_count == 1:
            pad_lines.append(pad_generator(len(pad_lines), name))
        else:
            for i in range(wire_count):
                pad_lines.append(pad_generator(len(pad_lines), name, i))
    return pad_lines

if __name__ == '__main__':
    io_lines = """
        input  logic                 clk;
        input  logic                 reset_ext;
        output logic                 reset;
        input  logic [P.AHBW-1:0]    HRDATAEXT;
        input  logic                 HREADYEXT;
        input  logic                 HRESPEXT;
        output logic                 HSELEXT;
        output logic                 HSELEXTSDC;
        output logic                 HCLK;
        output logic                 HRESETn;
        output logic [P.PA_BITS-1:0] HADDR;
        output logic [P.AHBW-1:0]    HWDATA;
        output logic [P.XLEN/8-1:0]  HWSTRB;
        output logic                 HWRITE;
        output logic [2:0]           HSIZE;
        output logic [2:0]           HBURST;
        output logic [3:0]           HPROT;
        output logic [1:0]           HTRANS;
        output logic                 HMASTLOCK;
        output logic                 HREADY;
        input  logic                 TIMECLK;
        input  logic [31:0]          GPIOPinsIn;
        output logic [31:0]          GPIOPinsOut;
        output logic [31:0]          GPIOPinsEn;
        input  logic                 UARTSin;
        output logic                 UARTSout;
        input  logic                 SDCIntr;
        input  logic                 SPIIn;
        output logic                 SPIOut;
        output logic [3:0]           SPICS;
        output logic                 ddr_ck_p;
        output logic                 ddr_ck_n;
        output logic                 ddr_cke;
        output logic [2:0]           ddr_ba;
        output logic [15:0]          ddr_addr;
        output logic                 ddr_cs;
        output logic                 ddr_ras;
        output logic                 ddr_cas;
        output logic                 ddr_we;
        output logic                 ddr_reset;
        output logic                 ddr_odt;
        output logic [P.XLEN/16-1:0] ddr_dm_oen;
        output logic [P.XLEN/16-1:0] ddr_dm;
        output logic [P.XLEN/16-1:0] ddr_dqs_p_oen;
        output logic [P.XLEN/16-1:0] ddr_dqs_p_ien;
        output logic [P.XLEN/16-1:0] ddr_dqs_p_out;
        input  logic [P.XLEN/16-1:0] ddr_dqs_p_in;
        output logic [P.XLEN/16-1:0] ddr_dqs_n_oen;
        output logic [P.XLEN/16-1:0] ddr_dqs_n_ien;
        output logic [P.XLEN/16-1:0] ddr_dqs_n_out;
        input  logic [P.XLEN/16-1:0] ddr_dqs_n_in;
        output logic [P.XLEN/2-1:0]  ddr_dq_oen;
        output logic [P.XLEN/2-1:0]  ddr_dq_out;
        input  logic [P.XLEN/2-1:0]  ddr_dq_in;
        input  logic                 dfi_clk_2x;
        output logic                 dfi_clk_1x;
        """
    [print(line) for line in gen_pads(io_lines.split('\n'))]
