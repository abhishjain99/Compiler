# https://github.com/newOnahtaN/CS312-PrinciplesOfProgrammingLanguages/blob/master/Type%20System/gee.py


# #  expression operators
# relation    = "==" | "!=" | "<" | "<=" | ">" | ">="

# #  expressions # need function for each expression
# expression = andExpr { "or" andExpr }
# andExpr    = relationalExpr { "and" relationalExpr }
# relationalExpr = addExpr [ relation addExpr ]
# addExpr    = term { ("+" | "-") term } #
# term       = factor { ("*" | "/") factor } #
# factor     = number | string | ident |  "(" expression ")" #

# # statements # need function and class for each statement
# stmtList =  {  statement  } #
# statement = ifStatement |  whileStatement  |  assign
# assign = ident "=" expression  eoln
# ifStatement = "if" expression block   [ "else" block ] 
# whileStatement = "while"  expression  block
# block = ":" eoln indent stmtList undent

# #  goal or start symbol
# script = stmtList

import re, sys, string

dict = { }
tokens = [ ]


# # ----- Expression class and its subclasses ---- # #
class Expression( object ):
    def __str__(self):
        return ""

class BinaryExpr( Expression ):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
        
    def __str__(self):
        return str(self.op) + " " + str(self.left) + " " + str(self.right)

class Number( Expression ):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return str(self.value)

# new class
class String( Expression ):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return str(self.value)

# new class
class VarRef( Expression ):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return str(self.value)


# # ----- Statement class and its subclasses ---- # #
# refer to Expression to know this structure
# new class
class Statement( object ):
    def __str__(self):
        return ""

# new class
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

# refer to BinaryExpr to know how to use this structure
# new class
class AssignStmt( Statement ):
    def __init__(self, expr, assignBlk):
        self.expr = expr
        self.assignBlk = assignBlk # identifier

    def __str__(self):
        return "= " + str(self.assignBlk) + " " + str(self.expr) + "\n"

# new class
class IfStmt( Statement ):
    def __init__(self, expr, ifBlk, elseBlk):
        self.expr = expr
        self.ifBlk = ifBlk
        self.elseBlk = elseBlk
    # Q1: Why does the test case test.gee print an else 3 times when only 2 of the Ifs have an else?
    # I chose an abstract syntax which stores an if-then as an if-then-else with an empty Block.
    # For me it simplifies the next assignment.
    def __str__(self):
        # if self.elseBlk != "":
        return "if " + str(self.expr) + "\n" + str(self.ifBlk) + "else\n" + str(self.elseBlk) + "endif\n"
        # else:
        #     return "if " + str(self.expr) + " then\n" + str(self.ifBlk) + " endif\n"

# new class
class WhileStmt( Statement ):
    def __init__(self, expr, whileBlk):
        self.expr = expr
        self.whileBlk = whileBlk

    def __str__(self):
        return "while " + str(self.expr) + "\n" + str(self.whileBlk) + "endwhile\n"

# new class
class claBlk( Statement ):
    def __init__(self, expr, typ, blk1, blk2):
        self.expr = expr
        self.typ = typ # type = if / while / ident
        self.blk1 = blk1 # ifBlk / whileBlk / assignBlk
        self.blk2 = blk2 # elseBlk

    def __str__(self):
        if self.typ.lower() == "if":
            return "if " + str(self.expr) + "\n" + str(self.blk1) + "else\n" + str(self.blk2) + "endif\n"
        elif self.typ.lower() == "while":
            return "while " + str(self.expr) + "\n" + str(self.blk1) + "endwhile\n"
        elif self.typ.lower() == "ident":
            return "= " + str(self.blk1) + " " + str(self.expr) + "\n"
        else:
            return error("Error parsing statements...")
            


# # ----- expressions ----- # #
# refer to addExpr/term/factor for this structure
# new function
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

# new function
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

# new function
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
# improved function
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

# new function
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

# new function
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
            # left = AssignStmt(expr, assignBlk)
            left = claBlk(expr, typ="Ident", blk1=assignBlk, blk2=None)
            return left
        else:
            error("Error: Assignment missing ';' .")
    else:
        error("Error: Assignment missing '=' sign .")

# new function
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
    left = claBlk(expr, typ="if", blk1=ifBlk, blk2=elseBlk)
    # left = IfStmt(expr, ifBlk, elseBlk)
    tok = tokens.peek( )
    return left

# new function
def parseWhileStatement(  ):
    """ whileStatement = "while"  expression  block """
    tok = tokens.next( )
    if debug: print("While Statement: ", tok)
    expr = expression( )
    whileBlk = parseBlk( )
    tok = tokens.peek( )
    left = claBlk(expr, typ="while", blk1=whileBlk, blk2=None)
    # left = WhileStmt(expr, whileBlk)
    tok = tokens.peek( )
    return left

# new function
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


# # ----- to find error, match, parse ----- # #
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
    print(str(stmtlist))
    return stmtlist


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

# improved function
def mklines(filename):
    inn = open(filename, "r")
    lines = [ ]
    pos = [0]
    ct = 0
    for line in inn:
        # print(line, end = "") # c
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
        print(ct, "\t", line) # u
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
    debug = False
    ct = 0
    for opt in sys.argv[1:]:
        if opt[0] != "-": break
        ct = ct + 1
        if opt == "-d": debug = True
    if len(sys.argv) < 2+ct:
        print("Usage:  %s filename" % sys.argv[0])
        return
    parse("".join(mklines(sys.argv[1+ct])))
    return

main()