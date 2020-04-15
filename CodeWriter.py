import Parser

SP_INIT = '@256'

SYS_INIT = 'Sys.init'

RET_ADDR = '@retAddr'

SEPARATOR = '$'

FIRST_COUNT = 0

NEW_LINE = '\n'

CONSTANT = 'constant'
POINTER = 'pointer'
STATIC = 'static'
TEMP = 'temp'
LCL = 'local'
ARG = 'argument'
THIS = 'this'
THAT = 'that'

HEAP_POINTERS = [LCL, ARG, THIS, THAT]
REV_HEAP_POINTERS = [THAT, THIS, ARG, LCL]

heap_dict = {LCL: 'LCL', ARG: 'ARG', THIS: 'THIS', THAT: 'THAT'}

global_segment_dict = {TEMP: 5, POINTER: 3}


class CodeWriter:
    """
     Translates VM commands into Hack assembly code
    """

    def __init__(self, file_path):
        """
        Opens the output file/stream and gets ready to write into it.
        :param file_path: Output file / stream
        """
        self._stream = open(file_path, 'w')
        self._file_name = None
        self._eq_counter = FIRST_COUNT
        self._lt_counter = FIRST_COUNT
        self._gt_counter = FIRST_COUNT
        self._file_name = None
        self._func_scope = None
        self._call_counter = FIRST_COUNT

    def set_file_name(self, file_name):
        """
        Informs the code writer that the translation of a new VM file is
        started.
        :param file_name: string
        """
        self._file_name = file_name

    def close(self):
        """
        Closes the output file
        """
        self._stream.close()

    def write_arithmetic(self, command):
        """
        Writes the assembly code that is the translation of the given
        arithmetic command.
        :param command: string
        """
        self.get_to_cell()
        if command == Parser.ADD:
            self.write_command('D=M')
            self.write_command('A=A-1')
            self.write_command('D=D+M')
            self.write_command('M=D')
            self.update_sp_minus_1()
        elif command == Parser.SUB:
            self.sub_2_cells()
            self.write_command('M=-D')
            self.update_sp_minus_1()
        elif command == Parser.NOT:
            self.write_command('M=!M')
        elif command == Parser.OR:
            self.write_command('D=M')
            self.write_command('A=A-1')
            self.write_command('M=M|D')
            self.update_sp_minus_1()
        elif command == Parser.AND:
            self.write_command('D=M')
            self.write_command('A=A-1')
            self.write_command('M=M&D')
            self.update_sp_minus_1()
        elif command == Parser.NEG:
            self.write_command('M=-M')
        elif command == Parser.EQ:
            # docing refers to lt, eq is similar
            self.write_command('D=M')
            self.write_command('@' + 'EQ_SEC_FIRST_NON_NEGATIVE_' + str(
                self._eq_counter))
            self.write_command('D;' + 'JGE')
            # y<0
            self.go_to_upper_cell()
            self.write_command('@' + 'EQ_SUB_' + str(self._eq_counter))
            self.write_command('D;' + 'JLT')
            # y<0, x>=0
            self.update_false()
            self.write_command('@' + 'END_EQ_' + str(self._eq_counter))
            self.write_command('0;JMP')

            # y>= 0
            self.write_command('(' + 'EQ_SEC_FIRST_NON_NEGATIVE_' + str(
                self._eq_counter) + ')')
            self.go_to_upper_cell()
            self.write_command('@' + 'EQ_SUB_' + str(self._eq_counter))
            self.write_command('D;' + 'JGE')
            # y>=0, x<0
            self.update_false()
            self.write_command('@' + 'END_EQ_' + str(self._eq_counter))
            self.write_command('0;JMP')

            # y<0, x <0  |  y>=0, x>=0
            self.write_command('(' + 'EQ_SUB_' + str(self._eq_counter) + ')')
            self.get_to_cell()
            self.sub_2_cells()
            self.write_command('@' + 'EQ_TRUE_' + str(self._eq_counter))
            self.write_command('D;' + 'JEQ')
            # x >= y
            self.update_false()
            self.write_command('@' + 'END_EQ_' + str(self._eq_counter))
            self.write_command('0;JMP')

            # x < y
            self.write_command('(' + 'EQ_TRUE_' + str(self._eq_counter) + ')')
            self.update_true()
            self.write_command('(' + 'END_EQ_' + str(self._eq_counter) + ')')
            self.update_sp_minus_1()

            self._eq_counter += 1
        elif command == Parser.LT:
            self.gt_or_lt('LT_SEC_FIRST_NON_NEGATIVE_', 'LT_SUB_', 'END_LT_',
                          'LT_TRUE_', 'JGE', 'JLT', 'JGT',
                          self._lt_counter)
            self._lt_counter += 1

        else:
            self.gt_or_lt('GT_SEC_FIRST_NON_POSITIVE_', 'GT_SUB_', 'END_GT_',
                          'GT_TRUE_', 'JLE', 'JGT', 'JLT',
                          self._gt_counter)
            self._gt_counter += 1

    def write_command(self, command):
        """
        write wrapper, add new line
        :param command: line to wrap
        """
        self._stream.write(command)
        self._stream.write(NEW_LINE)

    def go_to_upper_cell(self):
        self.get_to_cell()
        self.write_command('A=A-1')
        self.write_command('D=M')

    def sub_2_cells(self):
        self.write_command('D=M')
        self.write_command('A=A-1')
        self.write_command('D=D-M')

    def update_false(self):
        self.get_to_cell()
        self.write_command('A=A-1')
        self.write_command('M=0')

    def update_true(self):
        self.get_to_cell()
        self.write_command('A=A-1')
        self.write_command('M=-1')

    def get_to_cell(self):
        self.write_command('@SP')
        self.write_command('A=M')
        self.write_command('A=A-1')

    def update_sp_minus_1(self):
        self.write_command('@SP')
        self.write_command('M=M-1')

    def gt_or_lt(self, first_string, sub_string, end_string, true_string,
                 first_choice, second_choice, sub_choice,
                 counter):
        """
        write GT or LT commands
        :param first_string: label 1
        :param sub_string: label 2
        :param end_string: label 3
        :param true_string: label 4
        :param first_choice: first jump choice
        :param second_choice: second jump choice
        :param sub_choice: third jump choice
        :param counter: label counter identifier
        """
        # docing refers to lt, gt is the exact opposite
        self.write_command('D=M')
        self.write_command('@' + first_string + str(counter))
        self.write_command('D;' + first_choice)
        # y<0
        self.go_to_upper_cell()
        self.write_command('@' + sub_string + str(counter))
        self.write_command('D;' + second_choice)
        # y<0, x>=0
        self.update_false()
        self.write_command('@' + end_string + str(counter))
        self.write_command('0;JMP')

        # y>= 0
        self.write_command('(' + first_string + str(counter) + ')')
        self.go_to_upper_cell()
        self.write_command('@' + sub_string + str(counter))
        self.write_command('D;' + first_choice)
        # y>=0, x<0
        self.update_true()
        self.write_command('@' + end_string + str(counter))
        self.write_command('0;JMP')

        # y<0, x <0  |  y>=0, x>=0
        self.write_command('(' + sub_string + str(counter) + ')')
        self.get_to_cell()
        self.sub_2_cells()
        self.write_command('@' + true_string + str(counter))
        self.write_command('D;' + sub_choice)
        # x >= y
        self.update_false()
        self.write_command('@' + end_string + str(counter))
        self.write_command('0;JMP')

        # x < y
        self.write_command('(' + true_string + str(counter) + ')')
        self.update_true()
        self.write_command('(' + end_string + str(counter) + ')')
        self.update_sp_minus_1()

    def write_push_pop(self, command, segment, index):
        """
        Writes the assembly code that is the translation of the given command,
        where command is either C_PUSH or C_POP.
        :param command: C_PUSH or C_POP
        :param segment: string
        :param index: int
        """
        if command == Parser.C_POP:
            self.write_command('@SP')
            self.write_command('A=M-1')
            self.write_command('D=M')
            self.write_command('@R13')
            self.write_command('M=D')
            self.update_sp_minus_1()
            self.reach_segment_index(index, segment)
            self.store_addr()
            self.write_command('@R13')
            self.write_command('D=M')
            self.write_command('@R14')
            self.write_command('A=M')
            self.write_command('M=D')
        else:
            self.reach_segment_index(index, segment)
            if segment != CONSTANT:
                self.write_command('D=M')
            self.asm_push_code_from_D()

    def asm_push_code_from_D(self):
        self.write_command('@SP')
        self.write_command('A=M')
        self.write_command('M=D')
        self.write_command('@SP')
        self.write_command('M=M+1')

    def reach_segment_index(self, index, segment):
        """
        reach the correct A according to segment and index
        :param index: index in memory segment
        :param segment: memory segment in RAM
        """
        if segment in global_segment_dict:
            self.write_command(
                '@' + str(global_segment_dict[segment] + int(index)))
        elif segment == STATIC:
            self.write_command('@' + self._file_name + '.' + index)
        elif segment == CONSTANT:
            self.write_command('@' + str(index))
            self.write_command('D=A')
        else:
            self.write_command('@' + str(index))
            self.write_command('D=A')
            self.write_command('@' + heap_dict[segment])
            self.write_command('A=M+D')

    def store_addr(self):
        """
        store current address in R14
        """
        self.write_command('D=A')
        self.write_command('@R14')
        self.write_command('M=D')

    def write_label(self, label):
        """
        Writes the assembly code that is the translation of the given label command.
        :param label: label (string)
        """
        label_name = self.find_label_name(label)
        self.write_command('(' + label_name + ')')

    def find_label_name(self, label):
        """
        add to the label function scope
        :param label: label(string)
        :return: func_scope$label
        """
        if self._func_scope is None:
            label_name = label
        else:
            label_name = self._func_scope + SEPARATOR + label
        return label_name

    def write_goto(self, label):
        """
        Writes the assembly code that is the translation of the given goto command.
        :param label: label (string)
        """
        self.go_to_label(label)
        self.write_command('0;JMP')

    def go_to_label(self, label):
        """
        writes @func_scope$label
        :param label: label (string)
        """
        label_name = self.find_label_name(label)
        self.write_command('@' + label_name)

    def write_if(self, label):
        """
        Writes the assembly code that is the translation of the given if-goto command.
        :param label: label (string)
        """
        self.get_to_cell()
        self.write_command('D=M')
        self.update_sp_minus_1()
        self.go_to_label(label)
        self.write_command('D;JNE')

    def write_call(self, function_name, num_args):
        """
        Writes the assembly code that is the translation of the given Call command.
        :param function_name: functionName (string)
        :param num_args: numArgs (int)
        """
        return_add_label = 'return_address_' + str(self._call_counter)
        self._call_counter += 1
        # push returnAddress
        self.write_command('@' + return_add_label)
        self.write_command('D=A')
        self.asm_push_code_from_D()
        # push LCL,ARG,THIS,THAT
        for pointer in HEAP_POINTERS:
            self.write_command('@' + heap_dict[pointer])
            self.write_command('D=M')
            self.asm_push_code_from_D()
        # ARG = SP-nArgs -5
        self.put_SP_in_D()
        self.write_command('@' + str(num_args))
        self.write_command('D=D-A')
        self.write_command('@5')
        self.write_command('D=D-A')
        self.write_command('@' + heap_dict[ARG])
        self.write_command('M=D')
        # LCL = SP
        self.put_SP_in_D()
        self.write_command('@' + heap_dict[LCL])
        self.write_command('M=D')
        # goto g
        self.write_command('@' + function_name)
        self.write_command('0;JMP')
        # returnAddress
        self.write_command('(' + return_add_label + ')')

    def write_return(self):
        """
        Writes the assembly code that is the translation of the given Return command.
        """
        # frame=LCL
        self.write_command('@' + heap_dict[LCL])
        self.write_command('D=M')
        self.write_command('@frame')
        self.write_command('M=D')
        # retAddr = *(frame-5)
        self.write_command('@5')
        self.write_command('A=D-A')
        self.write_command('D=M')
        self.write_command(RET_ADDR)
        self.write_command('M=D')
        # *ARG = pop
        self.write_push_pop(Parser.C_POP, ARG, 0)
        # SP=ARG+1
        self.write_command('@' + heap_dict[ARG])
        self.write_command('D=M')
        self.write_command('@SP')
        self.write_command('M=D+1')
        # assign LCL,ARG,THIS,THAT
        for index, pointer in enumerate(REV_HEAP_POINTERS, 1):
            self.write_command('@' + str(index))
            self.write_command('D=A')
            self.write_command('@frame')
            self.write_command('A=M-D')
            self.write_command('D=M')
            self.write_command('@' + heap_dict[pointer])
            self.write_command('M=D')
        # goto retAddr
        self.write_command(RET_ADDR)
        self.write_command('A=M')
        self.write_command('0;JMP')

    def put_SP_in_D(self):
        self.write_command('@SP')
        self.write_command('D=M')

    def write_function(self, func_name, num_locals):
        """
        Writes the assembly code that is the trans. of the given Function command.
        :param func_name: functionName (string)
        :param num_locals: numLocals (int)
        """
        self.write_command('(' + func_name + ')')
        for variable in range(int(num_locals)):
            self.write_push_pop(Parser.C_PUSH, CONSTANT, 0)
        self._func_scope = func_name

    def write_init(self):
        """
        Writes the assembly code that effects the VM initialization (also called bootstrap
        code). This code should be placed in the ROM beginning in address 0x0000.
        """
        self.write_command(SP_INIT)
        self.write_command('D=A')
        self.write_command('@SP')
        self.write_command('M=D')
        self.write_call(SYS_INIT, 0)
