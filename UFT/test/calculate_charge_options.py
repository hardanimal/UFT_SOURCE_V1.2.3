#!/usr/bin/env python
# encoding: utf-8
"""
tool for calculate the charge IC bq24707 charge options.
"""

def cal_charge_current(curr):
    """
    calculate the register value of 0x14H for given current value.
    :param curr: given value of charge current
    :return: register value
    """
    #register = [0, 0, 0, 4096, 2048, 1024, 512, 256, 128, 64, 0, 0, 0, 0, 0, 0]
    register = [0, 0, 0, 0, 0, 0, 64, 128, 256, 512, 1024, 2048, 4096, 0, 0, 0]

    diff = 8128     # maximum output
    real_output = 0

    for val in range(0, 0xFFFF, 1):
        curr_value = 0
        bit_list = reversed(bin(val)[2:])
        for i, bit in enumerate(bit_list):
            curr_value += register[i] * int(bit)
            #print i, bit, register[i]

        # compare result
        curr_diff = abs(curr_value - curr)
        if curr_diff < diff:
            diff = curr_diff
            final_value = val
            real_output = curr_value

    return hex(final_value), real_output


def cal_charge_voltage(volt):
    """
    calculate the register value of 0x15H for given voltage value.
    :param volt: given value of charge voltage
    :return: register value
    """
    #register = [0, 0, 0, 4096, 2048, 1024, 512, 256, 128, 64, 0, 0, 0, 0, 0, 0]
    register = [0, 0, 0, 0, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192,
                16384, 0]

    diff = 32752     # maximum output
    real_output = 0

    for val in range(0, 0xFFFF, 1):
        curr_value = 0
        bit_list = reversed(bin(val)[2:])
        for i, bit in enumerate(bit_list):
            curr_value += register[i] * int(bit)
            #print i, bit, register[i]

        # compare result
        curr_diff = abs(curr_value - volt)
        if curr_diff < diff:
            diff = curr_diff
            final_value = val
            real_output = curr_value

    return hex(final_value), real_output


def cal_input_current(curr):
    """
    calculate the register value of 0x3FH for given current value.
    :param curr: given value of input current
    :return: register value
    """
    #register = [0, 0, 0, 4096, 2048, 1024, 512, 256, 128, 64, 0, 0, 0, 0, 0, 0]
    register = [0, 0, 0, 0, 0, 0, 0, 128, 256, 512, 1024, 2048, 4096, 0, 0, 0]

    diff = 8064     # maximum output
    real_output = 0

    for val in range(0, 0xFFFF, 1):
        curr_value = 0
        bit_list = reversed(bin(val)[2:])
        for i, bit in enumerate(bit_list):
            curr_value += register[i] * int(bit)
            #print i, bit, register[i]

        # compare result
        curr_diff = abs(curr_value - curr)
        if curr_diff < diff:
            diff = curr_diff
            final_value = val
            real_output = curr_value

    return hex(final_value), real_output


if __name__ == "__main__":
    current = 960   # mA
    print current, cal_charge_current(current)

    voltage = 4605  # mV
    print voltage, cal_charge_voltage(voltage)

    input_current = 1000   # mA
    print input_current, cal_input_current(input_current)
