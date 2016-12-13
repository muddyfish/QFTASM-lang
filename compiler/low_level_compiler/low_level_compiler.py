from typing import List

from high_level_compiler.variables import VariableStore, Variable


class FileInterpreter:
    opcodes = ["__MNZ__", "__MLZ__", "__ADD__", "__SUB__", "__AND__",
               "__OR__", "__XOR__", "__ANT__", "__SL__", "__SRL__", "__SRA__"]

    def __init__(self, instruction_list, global_store: VariableStore):
        self.compilers = {
            "sub": self.sub_compiler,
            "call_sub": self.call_sub_compiler,
            "return": self.return_compiler,
            "assign": self.assign_interpreter,
            "if": self.if_interpreter,
            "while": self.while_interpreter,
        }
        self.global_store = global_store
        self.current_sub = None
        self.current_result = None
        compiled = []
        for instruction in instruction_list:
            #print(instruction)
            assert instruction[0] in self.compilers
            compiled.extend(self.compilers[instruction[0]](*instruction[1:]))
        print("\n".join(compiled))

    def sub_compiler(self, status: str, name: str, result: Variable):
        self.current_sub = name
        self.current_result = result
        if status == "start":
            return ["#Start {}".format(name)]
        else:
            return ["#End {}".format(name)]

    def call_sub_compiler(self, sub_name: str, args: List[Variable], result: Variable):
        if sub_name in FileInterpreter.opcodes:
            return ["{} {} {} {}".format(sub_name[2:-2], *map(self.parse_variable, args), self.parse_result(result))]
        rtn = []
        variables = self.global_store.filter_subroutine(self.current_sub)
        for var in variables:
            rtn.extend(self.push_stack(self.parse_variable(var)))
        rtn.extend(self.push_stack("{}; +2"))
        rtn.append("MLZ -1 {} 0; {}".format("{}", sub_name))
        for var in reversed(variables):
            rtn.extend(self.pop_stack(self.parse_result(var)))
        rtn.append("MLZ -1 {} {}".format(self.parse_variable(self.global_store["result"]),
                                         self.parse_result(result)))
        return rtn

    def return_compiler(self, result):
        rtn = ["MLZ -1 {} {}".format(self.parse_variable(result),
                                     self.parse_result(self.global_store["result"]))]
        rtn.extend(self.pop_stack("0"))
        return rtn

    def assign_interpreter(self, variable, value):
        return ["MLZ -1 {} {}".format(self.parse_variable(value),
                                      self.parse_result(variable))]

    def if_interpreter(self, status, if_id, condition):
        if status == "end":
            return ["#End if_%s" % if_id]
        condition = self.parse_variable(condition)
        rtn = ["#Start if_%s" % if_id,
               "MNZ %s {} 0; End if_%s" % (condition, if_id),
               "MLZ 0 0 0"]
        return rtn

    def while_interpreter(self, status, while_id, condition):
        if status == "end":
            condition = self.parse_variable(condition)
            rtn = ["#End while_%s" % while_id,
                   "MNZ %s {} 0; Start while_%s" % (condition, while_id),
                   "MLZ 0 0 0"]
            return rtn
        rtn = ["MLZ -1 {} 0; End while_%s" % while_id,
               "MLZ 0 0 0",
               "#Start while_%s" % while_id]
        return rtn

    def pop_stack(self, address: str):
        return ["POP {}".format(address)]

    def push_stack(self, address: str):
        return ["PUSH {}".format(address)]

    def parse_variable(self, variable: Variable) -> str:
        if not isinstance(variable, Variable):
            return str(variable)
        pointer = "AB"[variable.is_pointer]
        return pointer+str(variable.offset)

    def parse_result(self, variable: Variable) -> str:
        pointer = "A"*variable.is_pointer
        return pointer+str(variable.offset)


