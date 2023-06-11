from __future__ import annotations
from dataclasses import dataclass
from functools import reduce
from abc import ABC, abstractmethod
from antlr4 import *
from lcLexer import *
from lcParser import *
from lcVisitor import *

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

import pydot


alphabet = set("abcdefghijklmnopqrstuvwxyz")
macrosDB = dict()

# Classes for the internal representation of the AST, 
# as well as the methods to print and evaluate them

# interface class
@dataclass
class Term(ABC):
    @abstractmethod
    def reduce(self) -> (Term, bool, str):
        pass

    @abstractmethod
    def freeVars(self) -> set(str):
        pass

    @abstractmethod
    def linkedVars(self) -> set(str):
        pass
    
    @abstractmethod
    def alphaSubstitution(self, oldVar, newVar) -> Term:
        pass

    @abstractmethod
    def varSubstitution(self, oldVar, newVar) -> Term:
        pass

    @abstractmethod
    def betaSubstitution(self, var, term) -> Term:
        pass

    @abstractmethod
    def show(self) -> str:
        pass

@dataclass
class Letter(Term):
    variable: str

    def reduce(self) -> (Term, bool, str):
        return (self, False, "")
    
    def freeVars(self) -> set(str):
        return set(self.variable)

    def linkedVars(self) -> set(str):
        return set()

    def alphaSubstitution(self, oldVar, newVar) -> Term:
        return self

    def varSubstitution(self, oldVar, newVar) -> Term:
        return self if self.variable != oldVar else Letter(newVar)

    def betaSubstitution(self, var, term) -> Term:
        return self if var != self.variable else term

    def show(self) -> str:
        return self.variable

@dataclass
class Application(Term):
    leftTerm: Term
    rightTerm: Term

    def reduce(self) -> (Term, bool, str):
        match self.leftTerm:
            case Abstraction(variable, innerTerm):
                log = ""

                abstraction = Abstraction(variable, innerTerm)
                linkedVarsl = innerTerm.linkedVars()
                freeVarsl = innerTerm.freeVars()
                freeVarsr = self.rightTerm.freeVars()

                needAlphaVars = linkedVarsl & freeVarsr.union(set(variable))
                availableLetters = ((((alphabet - linkedVarsl) - freeVarsl) - freeVarsr) - set(variable))
                for alphaVar in needAlphaVars:
                    newVar = list(availableLetters)[0]
                    availableLetters = availableLetters - set(newVar)

                    log += "α-conversió: " + alphaVar + " →  " + newVar + "\n"
                    log += abstraction.show() + " →  "
                    abstraction = Abstraction(variable, innerTerm.alphaSubstitution(alphaVar, newVar))
                    log += abstraction.show() + "\n"

                log += "β-reducció:\n"
                log += self.show() + " →  "
                result = abstraction.term.betaSubstitution(variable, self.rightTerm)
                log += result.show()
                return (result, True, log)

            case _:
                (reducel, hasBeenReducedl, logl) = self.leftTerm.reduce()
                if hasBeenReducedl:
                    return (Application(reducel, self.rightTerm), True, logl)

                (reducer, hasBeenReducedr, logr) = self.rightTerm.reduce()
                return (Application(self.leftTerm, reducer), hasBeenReducedr, logr)

    def freeVars(self) -> set(str):
        varsl = self.leftTerm.freeVars()
        varsr = self.rightTerm.freeVars()
        return varsl.union(varsr)

    def linkedVars(self) -> set(str):
        varsl = self.leftTerm.linkedVars()
        varsr = self.rightTerm.linkedVars()
        return varsl.union(varsr)

    def alphaSubstitution(self, oldVar, newVar) -> Term:
        return Application(self.leftTerm.alphaSubstitution(oldVar, newVar), self.rightTerm.alphaSubstitution(oldVar, newVar))

    def varSubstitution(self, oldVar, newVar) -> Term:
        return Application(self.leftTerm.varSubstitution(oldVar, newVar), self.rightTerm.varSubstitution(oldVar, newVar))

    def betaSubstitution(self, var, term) -> Term:
        return Application(self.leftTerm.betaSubstitution(var, term), self.rightTerm.betaSubstitution(var, term))

    def show(self) -> str:
        return "(" + self.leftTerm.show() + self.rightTerm.show() + ")"

@dataclass
class Abstraction(Term):
    variable: str
    term: Term

    def reduce(self) -> (Term, bool, str):
        (reduced, hasBeenReduced, log) = self.term.reduce()
        return (Abstraction(self.variable, reduced), hasBeenReduced, log)

    def freeVars(self) -> set(str):
        return self.term.freeVars() - set(self.variable)

    def linkedVars(self) -> set(str):
        vars = self.term.linkedVars()
        vars.add(self.variable)
        return vars

    def alphaSubstitution(self, oldVar, newVar) -> Term:
        return Abstraction(self.variable, self.term.alphaSubstitution(oldVar, newVar)) if self.variable != oldVar else self.varSubstitution(oldVar, newVar)

    def varSubstitution(self, oldVar, newVar) -> Term:
        return Abstraction(self.variable if self.variable != oldVar else newVar, self.term.varSubstitution(oldVar, newVar))

    def betaSubstitution(self, var, term) -> Term:
        return Abstraction(self.variable, self.term.betaSubstitution(var, term))

    def show(self) -> str:
        return "(λ" + self.variable + "." + self.term.show() + ")"



# Builder visitor translating from the AST to the internal representation

class BuildInternalRepVisitor(lcVisitor):
    def visitLetter(self, ctx):
        variable = next(ctx.getChildren())
        return Letter(variable.getText())

    def visitParentheses(self, ctx):
        [openParentheses, term, closeParentheses] = list(ctx.getChildren())
        return self.visit(term)

    def visitApplication(self, ctx):
        [leftTerm, rightTerm] = list(ctx.getChildren())
        return Application(self.visit(leftTerm), self.visit(rightTerm))

    def visitAbstraction(self, ctx):
        [lambdaSymbol, variables, dot, term] = list(ctx.getChildren())
        return reduce((lambda term, variable: Abstraction(variable, term)), reversed(variables.getText()), self.visit(term))

    def visitMacroDef(self, ctx):
        [macro, eqSymbol, term] = list(ctx.getChildren())
        macrosDB[macro.getText()] = self.visit(term)
        return None

    def visitMacro(self, ctx):
        macro = next(ctx.getChildren())
        return macrosDB[macro.getText()]

    def visitInfix(self, ctx):
        [leftTerm, macro, rightTerm] = list(ctx.getChildren())
        return Application(Application(macrosDB[macro.getText()], self.visit(leftTerm)), self.visit(rightTerm))


# Commented main program, used for testing before the bot was created
# Uncomment it if needed for debugging purposes

#while True:
#    expression = InputStream(input('? '))
#    lexer = lcLexer(expression)
#    tokenizedExpression = CommonTokenStream(lexer)
#    parser = lcParser(tokenizedExpression)
#    expressionTree = parser.root()
#    internalRepTree = BuildInternalRepVisitor().visit(expressionTree)
#
#    if (internalRepTree):
#        print("Arbre:\n" + internalRepTree.show())
#
#        i = 0
#        reducedToNormalForm = False
#        while i < 10 and not reducedToNormalForm:
#            (internalRepTree, hasBeenReduced, log) = internalRepTree.reduce()
#            print(log, end="")
#            reducedToNormalForm = not hasBeenReduced
#            i += 1
#
#        print("Resultat:")
#        if reducedToNormalForm:
#            print(internalRepTree.show() + "\n")
#        else:
#            print("Nothing\n")
#
#    else:
#        for (macroName, macroTerm) in macrosDB.items():
#            print(macroName + " ≡ " + macroTerm.show())
#        print("")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'AChurch - MValls Bot!\nBenvingut {update.effective_user.first_name}!')

async def author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("AChurch - MValls Bot!\n@ Marc Valls Camps, 2023")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("/start\n/author\n/help\n/macros\nExpressió λ-càlcul")

async def macros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    output = ""
    for (macroName, macroTerm) in macrosDB.items():
        output += macroName + " ≡ " + macroTerm.show() + "\n"

    await update.message.reply_text(output if bool(macrosDB) else "No has definit cap macro!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for line in update.message.text.split("\n"):
        expression = InputStream(line)
        lexer = lcLexer(expression)
        tokenizedExpression = CommonTokenStream(lexer)
        parser = lcParser(tokenizedExpression)
        expressionTree = parser.root()
        internalRepTree = BuildInternalRepVisitor().visit(expressionTree)
    
        if (internalRepTree):
            await update.message.reply_text("Arbre:\n" + internalRepTree.show())
    
            i = 0
            reducedToNormalForm = False
            while i < 10 and not reducedToNormalForm:
                (internalRepTree, hasBeenReduced, log) = internalRepTree.reduce()
                reducedToNormalForm = not hasBeenReduced
                if hasBeenReduced:
                    await update.message.reply_text(log)
    
                i += 1
    
            await update.message.reply_text("Resultat:\n" + internalRepTree.show() if reducedToNormalForm else "Nothing")

if __name__ == '__main__':
    app = ApplicationBuilder().token(str(open('token.txt', 'r').read().strip())).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("author", author))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("macros", macros))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    app.run_polling()