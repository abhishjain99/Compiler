# Implement a static type checker for Gee language. The type rules of Gee are the following:
#  1. Gee programs do not need explicit variable declarations.
#  2. The values in the test programs contain only number and boolean types of values. No need to consider string or other types.
#  3. No test case or assignment will contain the boolean constants True, False. For example, the following kinds of statements won't appear in the test files: v = True; if (x==False). But the following could: v = (x> 0); if (x>y).
#  4. No implicit type convertions are allowed. So the types of the operands of a binary operator (including the assignment operator) must match with each other.
# Use tipe as the name of the type function of each class.
# The type map described in class can be modeled using a Python dictionary (associative array). This dictionary, named tm, should be explicitly passed as an argument to each tipe function.

import re, sys, string

dict = { }
tokens = [ ]


# # ----- Expression class and its subclasses ---- # #
class Expression( object ):
    def __str__(self):
        return ""

# improved class - tipe
class BinaryExpr( Expression ):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __str__(self):
        return str(self.op) + " " + str(self.left) + " " + str(self.right)

    def value(self, state):
        o_val = self.op
        l_val = self.left.value(state)
        r_val = self.right.value(state)
        if o_val == "+":
            ans = l_val + r_val
        elif o_val == "-":
            ans = l_val - r_val
        elif o_val == "*":
            ans = l_val * r_val
        elif o_val == "/":
            ans = l_val / r_val
        elif o_val == ">":
            ans = l_val > r_val
        elif o_val == ">=":
            ans = l_val >= r_val
        elif o_val == "<":
            ans = l_val < r_val
        elif o_val == "<=":
            ans = l_val <= r_val
        elif o_val == "==":
            ans = l_val == r_val
        elif o_val == "!=":
            ans = l_val != r_val
        elif o_val == "and":
            ans = l_val and r_val
        elif o_val == "or":
            ans = l_val or r_val
        return ans

    def tipe(self, tm):
        l_typ = self.left.tipe(tm)
        r_typ = self.right.tipe(tm)
        if l_typ != r_typ:
            error("Type Error: " + l_typ + " = " + r_typ + "!\n")
        elif l_typ == "number" and re.match(Lexer.arithmetic, self.op):
            return l_typ
        elif re.match(Lexer.relational, self.op) or self.op in ("<", ">", "and", "or"):
            return "boolean"

# improved class - tipe
class Number( Expression ):
    def __init__(self, vallue):
        self.vallue = vallue

    def __str__(self):
        return str(self.vallue)

    def value(self, state):
        return int(self.vallue)

    def tipe(self, tm):
        return "number"

# improved class - tipe
class String( Expression ):
    def __init__(self, vallue):
        self.vallue = vallue

    def __str__(self):
        return str(self.vallue)

    def value(self, state):
        return self.vallue

    def tipe(self, tm):
        error("Warning: String is not considered!\n")

# improved class - tipe
class VarRef( Expression ):
    def __init__(self, vallue):
        self.vallue = vallue

    def __str__(self):
        return str(self.vallue)

    def value(self, state):
        return state[self.vallue]

    def tipe(self, tm):
        if self.vallue not in tm:
            error("Type Error: "+ str(self.vallue) +" is referenced before being defined!\n")
        else:
            return tm[self.vallue]


# # ----- Statement class and its subclasses ---- # #
class Statement( object ):
    def __str__(self):
        return ""

# improved class - tipe
class StmtList( object ):
    def __init__(self):
        self.stmtList = []

    def nextStmt(self, stmt):
        self.stmtList.append(stmt) # need to append all the statements in list as suggested below

    def __str__(self):
        finalStmt = ''
        for stmt in self.stmtList:
            finalStmt += str(stmt)
        return finalStmt

    def meaning(self, state):
        for stmt in self.stmtList:
            stmt.meaning(state)
        return state

    def tipe(self, tm):
        for stmt in self.stmtList:
            stmt.tipe(tm)

# improved class - tipe
class CLABlk( Statement ):
    def __init__(self, expr, typ, blk1, blk2=""):
        self.expr = expr
        self.typ = typ # type = if / while / assign
        self.blk1 = blk1 # ifBlk / whileBlk / assignBlk
        self.blk2 = blk2 # elseBlk / "" / ""

    def __str__(self):
        if self.typ.lower() == "if":
            return "if " + str(self.expr) + "\n" + str(self.blk1) + "else\n" + str(self.blk2) + "endif\n"

        elif self.typ.lower() == "while":
            return "while " + str(self.expr) + "\n" + str(self.blk1) + "endwhile\n"

        elif self.typ.lower() == "assign":
            return "= " + str(self.blk1) + " " + str(self.expr) + "\n"

        else:
            return error("Error parsing statements...\n")

    def meaning(self, state):
        if self.typ.lower() == "if":
            if self.expr.value(state):
                self.blk1.meaning(state)
            else:
                if self.blk2 != "":
                    self.blk2.meaning(state)

        elif self.typ.lower() == "while":
            while self.expr.value(state):
                self.blk1.meaning(state)

        elif self.typ.lower() == "assign":
            state[self.blk1] = self.expr.value(state)

        else:
            return error("_semantic Error...")
        return state

    def tipe(self, tm):
        if self.typ.lower() == "if" or self.typ.lower() == "while":
            if self.expr.tipe(tm) != "boolean":
                print("\n")
                error("\n")
            self.blk1.tipe(tm) # blk1 = if block / while block

            if self.blk2 != "": # blk2 = else block
                self.blk2.tipe(tm)

        elif self.typ.lower() == "assign":
            if self.expr.tipe(tm) == "":
                error("error: No variable is defined yet!\n")

            elif self.blk1 not in tm:
                tm[self.blk1] = self.expr.tipe(tm)
                print(self.blk1, self.expr.tipe(tm))

            elif tm[self.blk1] != self.expr.tipe(tm): # blk1 = identifier
                error("Type Error: " + tm[self.blk1] + " = " + self.expr.tipe(tm) + "!\n")

        else:
            return error("tipe error...\n")




# # ----- expressions ----- # #
def expression( ):
    """ expression = andExpr { "or" andExpr } """
    tok = tokens.peek( )
    if debug: print("expression:", tok)
    left = andExpr( )
    tok = tokens.peek( )
    while tok == "or":
        tokens.next( )
        right = andExpr( )
        left = BinaryExpr(tok, left, right)
        tok = tokens.peek( )
    return left

def andExpr( ):
    """ andExpr    = relationalExpr { "and" relationalExpr } """
    tok = tokens.peek( )
    if debug: print("andExpr: ", tok)
    left = relationalExpr( )
    tok = tokens.peek( )
    while tok == "and":
        tokens.next( )
        right = relationalExpr( )
        left = BinaryExpr(tok, left, right)
        tok = tokens.peek( )
    return left

def relationalExpr( ):
    """ relationalExpr = addExpr [ relation addExpr ] """
    tok = tokens.peek( )
    if debug: print("relationalExpr: ", tok)
    left = addExpr( )
    tok = tokens.peek( )
    while re.match(Lexer.relational, tok):
        tokens.next()
        right = addExpr( )
        left = BinaryExpr(tok, left, right)
        tok = tokens.peek()
    return left

def addExpr( ):
    """ addExpr    = term { ('+' | '-') term } """
    tok = tokens.peek( )
    if debug: print("addExpr: ", tok)
    left = term( )
    tok = tokens.peek( )
    while tok == "+" or tok == "-":
        tokens.next()
        right = term( )
        left = BinaryExpr(tok, left, right)
        tok = tokens.peek( )
    return left

def term( ):
    """ term    = factor { ('*' | '/') factor } """
    tok = tokens.peek( )
    if debug: print("Term: ", tok)
    left = factor( )
    tok = tokens.peek( )
    while tok == "*" or tok == "/":
        tokens.next()
        right = factor( )
        left = BinaryExpr(tok, left, right)
        tok = tokens.peek( )
    return left

def factor( ):
    """ factor     = number | string | ident |  "(" expression ")" """
    tok = tokens.peek( )
    if debug: print("Factor: ", tok)
    if re.match(Lexer.number, tok):
        expr = Number(tok)
        tokens.next( )
        return expr
    elif re.match(Lexer.string, tok):
        expr = String(tok)
        tokens.next( )
        return expr
    elif re.match(Lexer.identifier, tok):
        expr = VarRef(tok)
        tokens.next( )
        return expr
    if tok == "(":
        # tokens.next( )
        # or
        match( tok )
        expr = expression( )
        tokens.peek( )
        tok = match(")")
        return expr
    error("Error: Invalid operand")
    return


# # ----- statements ----- # #
def parseStmtList(  ):
    """ stmtList =  {  statement  } """
    tok = tokens.peek( )
    stmtList = StmtList( )
    while tok is not None and tok != "~":
    #     # need to store each statement in a list
        statement = parseStatement( )
        stmtList.nextStmt(statement)
        tok = tokens.peek( )
    return stmtList

def parseStatement(  ):
    """ statement = ifStatement |  whileStatement  |  assign """
    tok = tokens.peek( )
    if debug: print("Statement: ", tok)
    if tok == "if":
        return parseIfStatement( )
    elif tok == "while":
        return parseWhileStatement( )
    elif re.match(Lexer.identifier, tok):
        return parseAssign( )
    error("Error: Statement needs if, while or identifier at start .")

def parseAssign(  ):
    """ assign = ident "=" expression  eoln """
    tok = tokens.peek( )
    assignBlk = tok # identifier
    if debug: print("Assign: ", tok)
    tok = tokens.next( )
    if tok == "=":
        tokens.next( )
        expr = expression( )
        tok = tokens.peek( )
        if tok == ";":
            tokens.next( )
            left = CLABlk(expr, typ="assign", blk1=assignBlk, blk2="")
            return left
        else:
            error("Error: Assignment missing ';' .")
    else:
        error("Error: Assignment missing '=' sign .")

def parseIfStatement(  ):
    """ ifStatement = "if" expression block   [ "else" block ] """
    tok = tokens.next( )
    if debug: print("If Statement: ", tok)
    expr = expression( )
    ifBlk = parseBlk( )
    elseBlk = ""
    tok = tokens.peek( )
    if tok == "else":
        tok = tokens.next( )
        if debug: print("Else Statement: ", tok)
        elseBlk = parseBlk()
    left = CLABlk(expr, typ="if", blk1=ifBlk, blk2=elseBlk)
    tok = tokens.peek( )
    return left

def parseWhileStatement(  ):
    """ whileStatement = "while"  expression  block """
    tok = tokens.next( )
    if debug: print("While Statement: ", tok)
    expr = expression( )
    whileBlk = parseBlk( )
    tok = tokens.peek( )
    left = CLABlk(expr, typ="while", blk1=whileBlk, blk2="")
    tok = tokens.peek( )
    return left

def parseBlk(  ):
    """ block = ":" eoln indent stmtList undent """
    tok = tokens.peek( )
    if debug: print("Block: ", tok)
    if tok == ":":
        tok = tokens.next( )
        if tok == ";":
            tok = tokens.next( )
            if tok == "@":
                tok = tokens.next( )
                stmtList = parseStmtList( )
                tok = tokens.peek( )
                if tok == "~":
                    tokens.next( )
                    return stmtList
                else:
                    error("Error: Block missing '~' i.e. undent after eol .")
            else:
                error("Error: Block missing '@' i.e. indent after eol .")
        else:
            error("Error: Block missing ';' at eol .")
    else:
        error("Error: Block missing ':' before eol .")


# # ----- to find error, match, parse, _semantics_t1 ----- # #
def error( msg ):
    #print msg
    sys.exit(msg)

def match( matchtok ):
    tok = tokens.peek( )
    if (tok != matchtok): error("Error: Expecting "+ matchtok)
    tokens.next( )
    return tok

# The "parse" function. This builds a list of tokens from the input string,
# and then hands it to a recursive descent parser for the PAL grammar.
def parse( text ) :
    global tokens
    tokens = Lexer( text )
    # expr = addExpr( )
    # print('Polish prefix:', str(expr))
    #     Or:
    stmtlist = parseStmtList( )
    return stmtlist

def _semantics_t1( stmtList ):
    state = {}
    state = stmtList.meaning(state)
    out = "\n{"
    for var, val in state.items():
        out += "<" + str(var) + ", " + str(val) + ">, "
    print(out.rstrip(", ") + "}\n")

def _tipe_t2( stmtList ):
    tm = {}
    stmtList.tipe(tm)


# Lexer, a private class that represents lists of tokens from a Gee
# statement. This class provides the following to its clients:
#
#   o A constructor that takes a string representing a statement
#       as its only parameter, and that initializes a sequence with
#       the tokens from that string.
#
#   o peek, a parameterless message that returns the next token
#       from a token sequence. This returns the token as a string.
#       If there are no more tokens in the sequence, this message
#       returns None.
#
#   o removeToken, a parameterless message that removes the next
#       token from a token sequence.
#
#   o __str__, a parameterless message that returns a string representation
#       of a token sequence, so that token sequences can print nicely

class Lexer :


    # The constructor with some regular expressions that define Gee's lexical rules.
    # The constructor uses these expressions to split the input expression into
    # a list of substrings that match Gee tokens, and saves that list to be
    # doled out in response to future "peek" messages. The position in the
    # list at which to dole next is also saved for "nextToken" to use.

    special = r"\(|\)|\[|\]|,|:|;|@|~|;|\$"
    relational = "<=?|>=?|==?|!="
    arithmetic = "\+|\-|\*|/"
    #char = r"'."
    string = r"'[^']*'" + "|" + r'"[^"]*"'
    number = r"\-?\d+(?:\.\d+)?"
    literal = string + "|" + number
    #idStart = r"a-zA-Z"
    #idChar = idStart + r"0-9"
    #identifier = "[" + idStart + "][" + idChar + "]*"
    identifier = "[a-zA-Z]\w*"
    lexRules = literal + "|" + special + "|" + relational + "|" + arithmetic + "|" + identifier

    def __init__( self, text ) :
        self.tokens = re.findall( Lexer.lexRules, text )
        self.position = 0
        self.indent = [ 0 ]


    # The peek method. This just returns the token at the current position in the
    # list, or None if the current position is past the end of the list.

    def peek( self ) :
        if self.position < len(self.tokens) :
            return self.tokens[ self.position ]
        else :
            return None


    # The removeToken method. All this has to do is increment the token sequence's
    # position counter.

    def next( self ) :
        self.position = self.position + 1
        return self.peek( )


    # An "__str__" method, so that token sequences print in a useful form.

    def __str__( self ) :
        return "<Lexer at " + str(self.position) + " in " + str(self.tokens) + ">"


def chkIndent(line):
    ct = 0
    for ch in line:
        if ch != " ": return ct
        ct += 1
    return ct

def delComment(line):
    pos = line.find("#")
    if pos > -1:
        line = line[0:pos]
        line = line.rstrip()
    return line

# improved function - to print the output in needed format
def mklines(filename):
    inn = open(filename, "r")
    lines = [ ]
    pos = [0]
    ct = 0
    for line in inn:
        ct += 1
        line = delComment(line)
        line = line.rstrip( )+";" # shifting this line after delComment() as we will first remove comment and then apply eol.
        if len(line) == 0 or line == ";": continue
        indent = chkIndent(line)
        line = line.lstrip( )
        if indent > pos[-1]:
            pos.append(indent)
            line = '@' + line
        elif indent < pos[-1]:
            while indent < pos[-1]:
                del(pos[-1])
                line = '~' + line
        lines.append(line)
    # print len(pos)
    undent = "" # consider this in parseStatementList else code won't run
    for i in pos[1:]:
        undent += "~"
    lines.append(undent)
    # print undent
    return lines

def main():
    """main program for testing"""
    global debug
    debug = False # False at beginning, True only for -d
    ct = 0
    for opt in sys.argv[1:]:
        if opt[0] != "-": break
        ct = ct + 1
        if opt == "-d": debug = True
    if len(sys.argv) < 2+ct:
        print("Usage:  %s filename" % sys.argv[0])
        return
    stmt = parse("".join(mklines(sys.argv[1+ct])))
    # _semantics_t1(stmt)
    _tipe_t2( stmt )
    return

main()