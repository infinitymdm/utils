#! /usr/bin/python3
''' A utility script for generating pads from system/verilog input and output lines.'''

known_substitutions = {}

def parse_line(line: str):
    ''' Read a verilog input/output line and return a tuple with data needed to construct pads.

        Returns a tuple of the following form:
            (  
                str:  Port direction ('inout', 'output', or 'input'),
                int:  Number of wires,
                str:  Name of the bus/wire
            )
        For example, the line "input logic [31:0] bus;" should get parsed to ('input', 32, "bus")
    '''

    # Initial assumptions
    direction = 'inout'
    wire_count = 1
    bus_name = 'none'

    tokens = line.strip().split()
    for token in tokens:
        if any(typestr == token.strip() for typestr in ['reg', 'wire', 'integer', 'real', 'time', 'realtime', 'logic', 'bit', 'byte', 'shortint', 'int', 'longint', 'shortreal']):
            continue # skip types
        elif 'output' in token:
            direction = 'output'
        elif 'input' in token:
            direction = 'input'
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
    return (direction, wire_count, bus_name)

def gen_inout_pad(pin_num: int, wire_name: str, is_bus=False, bus_addr=0, has_ien=False):
    ''' Generate an inout pad string'''
    _ = "'"
    bus_str = "["+str(bus_addr)+"]" if is_bus else ""
    return f'PADINOUT p{pin_num:03}(.PAD({wire_name}{bus_str}), .OEN({wire_name}_oen_o{bus_str}), .DO({wire_name}_o{bus_str}), .IEN({f"{wire_name}_ien_o{bus_str}" if has_ien else f"1{_}b1"}), .DI({wire_name}_i{bus_str}));'

def gen_input_pad(pin_num: int, wire_name: str, is_bus=False, bus_addr=0, has_ien=False):
    ''' Generate an input pad string

        If the wire is part of a bus, specify the address with is_bus and bus_addr (e.g. is_bus=True, bus_addr=12 for addr[12])
    '''
    bus_str = "["+str(bus_addr)+"]" if is_bus else ""
    return f'PADIN    p{pin_num:03}(.PAD({wire_name}{bus_str}), .DI({wire_name}_i{bus_str}));'

def gen_output_pad(pin_num: int, wire_name: str, is_bus=False, bus_addr=0, has_ien=False):
    ''' Generate an output pad string

        If the wire is part of a bus, specify the address with is_bus and bus_addr (e.g. is_bus=True, bus_addr=12 for addr[12])
    '''
    bus_str = "["+str(bus_addr)+"]" if is_bus else ""
    return f'PADOUT   p{pin_num:03}(.PAD({wire_name}{bus_str}), .DO({wire_name}_o{bus_str}));'

def gen_pads(io_lines: list):
    ''' Given a list of verilog io lines, generates a list of pad strings.'''
    pad_lines = []
    for line in io_lines:
        if not len(line.strip()):
            continue # Skip empty lines
        (direction, wire_count, name) = parse_line(line)
        pad_generator = gen_inout_pad
        has_ien=False
        if direction == 'output':
            pad_generator = gen_output_pad
        elif direction == 'input':
            pad_generator = gen_input_pad
        else:
            has_ien = input(f'Does {name} have an input enable [y/N]? ').lower().startswith('y')
        if wire_count == 1:
            pad_lines.append(pad_generator(len(pad_lines), name, has_ien=has_ien))
        else:
            for i in range(wire_count):
                pad_lines.append(pad_generator(len(pad_lines), name, is_bus=True, bus_addr=i, has_ien=has_ien))
    return pad_lines

if __name__ == '__main__':
    io_lines = ''
    with open('io.txt', 'r', encoding='utf-8') as file:
        io_lines = file.read()
    pad_lines = gen_pads(io_lines.split('\n'))
    with open('pads.txt', 'w', encoding='utf-8') as file:
        for line in pad_lines:
            file.write(line + '\n')
        file.close()
