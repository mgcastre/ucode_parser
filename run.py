#!/usr/bin/python3
import subprocess as sb
from UCODE_Parser import UCODEParser as Parser

def run_ucode(input_file, name='out'):
	sb.call(['./ucode_2014', input_file, name])

p = Parser()
name = 'model.in'
p.write(name)
run_ucode(name)
