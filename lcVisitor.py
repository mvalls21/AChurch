# Generated from lc.g4 by ANTLR 4.13.0
from antlr4 import *
if "." in __name__:
    from .lcParser import lcParser
else:
    from lcParser import lcParser

# This class defines a complete generic visitor for a parse tree produced by lcParser.

class lcVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by lcParser#macroDef.
    def visitMacroDef(self, ctx:lcParser.MacroDefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by lcParser#term.
    def visitTerm(self, ctx:lcParser.TermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by lcParser#macro.
    def visitMacro(self, ctx:lcParser.MacroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by lcParser#parentheses.
    def visitParentheses(self, ctx:lcParser.ParenthesesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by lcParser#application.
    def visitApplication(self, ctx:lcParser.ApplicationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by lcParser#letter.
    def visitLetter(self, ctx:lcParser.LetterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by lcParser#abstraction.
    def visitAbstraction(self, ctx:lcParser.AbstractionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by lcParser#infix.
    def visitInfix(self, ctx:lcParser.InfixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by lcParser#lletres.
    def visitLletres(self, ctx:lcParser.LletresContext):
        return self.visitChildren(ctx)



del lcParser