"""
AST (abstract syntax tree) nodes for the c3 language.
The tree is build by the parser.
Then it is checked
Finally code is generated from it.
"""


class Node:
    """ Base class of all nodes in a AST """
    pass


# Variables, parameters, local variables, constants and named types:
class Symbol(Node):
    """ Symbol is the base class for all named things like variables,
        functions, constants and types and modules """
    def __init__(self, name):
        self.name = name
        self.refs = []

    def addRef(self, r):
        self.refs.append(r)

    @property
    def References(self):
        return self.refs


# Modules
class Package(Symbol):
    def __init__(self, name, loc):
        super().__init__(name)
        self.loc = loc
        self.declarations = []
        self.imports = []

    def add_declaration(self, decl):
        self.declarations.append(decl)
        if isinstance(decl, Function):
            decl.package = self

    @property
    def Types(self):
        return self.innerScope.Types

    @property
    def Functions(self):
        return self.innerScope.Functions

    def __repr__(self):
        return 'MODULE {}'.format(self.name)


class Type(Node):
    """ Base class of all types """
    pass


class NamedType(Type, Symbol):
    """ Some types are named, for example a user defined type (typedef)
        and built in types. That is why this class derives from both Type
        and Symbol. """
    def __init__(self, name):
        Symbol.__init__(self, name)


class BaseType(NamedType):
    """ Built in type """
    def __init__(self, name, byte_size):
        super().__init__(name)
        self.byte_size = byte_size

    def __repr__(self):
        return '{}'.format(self.name)


class FunctionType(Type):
    """ Function blueprint, defines argument types and return type """
    def __init__(self, parametertypes, returntype):
        self.parametertypes = parametertypes
        self.returntype = returntype

    def __repr__(self):
        params = ', '.join([str(v) for v in self.parametertypes])
        return '{1} f({0})'.format(params, self.returntype)


class PointerType(Type):
    """ A type that points to data of some other type """
    def __init__(self, ptype):
        assert isinstance(ptype, Type) or isinstance(ptype, Expression)
        self.ptype = ptype

    def __repr__(self):
        return '({}*)'.format(self.ptype)


class StructField:
    """ Field of a struct type """
    def __init__(self, name, typ):
        assert type(name) is str
        self.name = name
        self.typ = typ

    def __repr__(self):
        return 'Member {}'.format(self.name)


class StructureType(Type):
    """ Struct type consisting of several named members """
    def __init__(self, mems):
        self.mems = mems
        assert all(type(mem) is StructField for mem in mems)

    def hasField(self, name):
        for mem in self.mems:
            if name == mem.name:
                return True
        return False

    def fieldType(self, name):
        return self.findField(name).typ

    def fieldOffset(self, name):
        return self.findField(name).offset

    def findField(self, name):
        for mem in self.mems:
            if name == mem.name:
                return mem
        raise KeyError(name)

    def __repr__(self):
        return 'STRUCT'


class ArrayType(Type):
    """ Array type """
    def __init__(self, element_type, size):
        self.element_type = element_type
        self.size = size

    def __repr__(self):
        return 'ARRAY {}'.format(self.size)


class DefinedType(NamedType):
    """ A named type indicating another type """
    def __init__(self, name, typ, loc):
        assert isinstance(name, str)
        super().__init__(name)
        self.typ = typ
        self.loc = loc

    def __repr__(self):
        return 'Named type {0} of type {1}'.format(self.name, self.typ)


class Constant(Symbol):
    """ Constant definition """
    def __init__(self, name, typ, value):
        super().__init__(name)
        self.typ = typ
        self.value = value

    def __repr__(self):
        return 'CONSTANT {0} = {1}'.format(self.name, self.value)


class Variable(Symbol):
    def __init__(self, name, typ):
        super().__init__(name)
        self.typ = typ
        self.isLocal = False
        self.isParameter = False

    def __repr__(self):
        return 'Var {} [{}]'.format(self.name, self.typ)


class LocalVariable(Variable):
    def __init__(self, name, typ):
        super().__init__(name, typ)
        self.isLocal = True


class FormalParameter(Variable):
    def __init__(self, name, typ):
        super().__init__(name, typ)
        self.isParameter = True


# Procedure types
class Function(Symbol):
    """ Actual implementation of a function """
    def __init__(self, name, loc):
        super().__init__(name)
        self.loc = loc
        self.declarations = []

    def add_declaration(self, decl):
        self.declarations.append(decl)

    def __repr__(self):
        return 'Func {}'.format(self.name)


# Operations / Expressions:
class Expression(Node):
    def __init__(self, loc):
        self.loc = loc


class Sizeof(Expression):
    def __init__(self, typ, loc):
        super().__init__(loc)
        self.query_typ = typ


class Deref(Expression):
    def __init__(self, ptr, loc):
        super().__init__(loc)
        assert isinstance(ptr, Expression)
        self.ptr = ptr

    def __repr__(self):
        return 'DEREF {}'.format(self.ptr)


class TypeCast(Expression):
    def __init__(self, to_type, x, loc):
        super().__init__(loc)
        self.to_type = to_type
        self.a = x

    def __repr__(self):
        return 'TYPECAST {}'.format(self.to_type)


class Member(Expression):
    """ Field reference of some object, can also be package selection """
    def __init__(self, base, field, loc):
        super().__init__(loc)
        assert isinstance(base, Expression)
        assert isinstance(field, str)
        self.base = base
        self.field = field

    def __repr__(self):
        return 'MEMBER {}.{}'.format(self.base, self.field)


class Index(Expression):
    """ Index something, for example an array """
    def __init__(self, base, i, loc):
        super().__init__(loc)
        self.base = base
        self.i = i

    def __repr__(self):
        return 'Index {}'.format(self.i)


class Unop(Expression):
    """ Operation on one operand """
    def __init__(self, op, a, loc):
        super().__init__(loc)
        assert isinstance(a, Expression)
        assert isinstance(op, str)
        self.a = a
        self.op = op

    def __repr__(self):
        return 'UNOP {}'.format(self.op)


class Binop(Expression):
    """ Expression taking two operands and one operator """
    def __init__(self, a, op, b, loc):
        super().__init__(loc)
        assert isinstance(a, Expression), type(a)
        assert isinstance(b, Expression)
        assert isinstance(op, str)
        self.a = a
        self.b = b
        self.op = op   # Operation: '+', '-', '*', '/', 'mod'

    def __repr__(self):
        return 'BINOP {}'.format(self.op)


class Identifier(Expression):
    """ Reference to some identifier, can be anything from package, variable
        function or type, any named thing! """
    def __init__(self, target, loc):
        super().__init__(loc)
        self.target = target

    def __repr__(self):
        return 'ID {}'.format(self.target)


class Literal(Expression):
    """ Constant value or string """
    def __init__(self, val, loc):
        super().__init__(loc)
        self.val = val

    def __repr__(self):
        return 'LITERAL {}'.format(self.val)


class FunctionCall(Expression):
    """ Call to a some function """
    def __init__(self, proc, args, loc):
        super().__init__(loc)
        self.proc = proc
        self.args = args

    def __repr__(self):
        return 'CALL {0} '.format(self.proc)


# Statements
class Statement(Node):
    """ Base class of all statements """
    def __init__(self, loc):
        self.loc = loc


class Empty(Statement):
    """ Empty statement which does nothing! """
    def __init__(self):
        super().__init__(None)

    def __repr__(self):
        return 'NOP'


class Compound(Statement):
    """ Statement consisting of a sequence of other statements """
    def __init__(self, statements):
        super().__init__(None)
        self.statements = statements
        for s in self.statements:
            assert isinstance(s, Statement)

    def __repr__(self):
        return 'COMPOUND STATEMENT'


class Return(Statement):
    def __init__(self, expr, loc):
        super().__init__(loc)
        self.expr = expr

    def __repr__(self):
        return 'RETURN STATEMENT'


class Assignment(Statement):
    def __init__(self, lval, rval, loc):
        super().__init__(loc)
        assert isinstance(lval, Expression)
        assert isinstance(rval, Expression)
        self.lval = lval
        self.rval = rval

    def __repr__(self):
        return 'ASSIGNMENT'


class ExpressionStatement(Statement):
    def __init__(self, ex, loc):
        super().__init__(loc)
        self.ex = ex

    def __repr__(self):
        return 'Epression'


class If(Statement):
    def __init__(self, condition, truestatement, falsestatement, loc):
        super().__init__(loc)
        self.condition = condition
        self.truestatement = truestatement
        self.falsestatement = falsestatement

    def __repr__(self):
        return 'IF-statement'


class Switch(Statement):
    def __init__(self, condition, loc):
        super().__init__(loc)
        self.condition = condition

    def __repr__(self):
        return 'Switch on {}'.format(self.condition)


class While(Statement):
    """ While statement """
    def __init__(self, condition, statement, loc):
        super().__init__(loc)
        self.condition = condition
        self.statement = statement

    def __repr__(self):
        return 'WHILE-statement'


class For(Statement):
    """ For statement with a start, condition and final statement """
    def __init__(self, init, condition, final, statement, loc):
        super().__init__(loc)
        self.init = init
        self.condition = condition
        self.final = final
        self.statement = statement

    def __repr__(self):
        return 'FOR-statement'
