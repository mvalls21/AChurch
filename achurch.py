from __future__ import annotations
from dataclasses import dataclass
from functools import reduce
from abc import ABC, abstractmethod
from antlr4 import *
from lcLexer import *
from lcParser import *
from lcVisitor import *

alphabet = set("abcdefghijklmnopqrstuvwxyz")
macrosDB = dict()

# Classes for the internal representation of the AST, 
# as well as the methods to print and evaluate them

# interface class
@dataclass
class Term(ABC):
    @abstractmethod
    def reduce(self) -> (Term, bool):
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
    def show(self):
        pass

@dataclass
class Letter(Term):
    variable: str

    def reduce(self) -> (Term, bool):
        return (self, False)
    
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

    def show(self):
        print(self.variable, end="")

@dataclass
class Application(Term):
    leftTerm: Term
    rightTerm: Term

    def reduce(self) -> (Term, bool):
        match self.leftTerm:
            case Abstraction(variable, innerTerm):
                abstraction = Abstraction(variable, innerTerm)
                linkedVarsl = innerTerm.linkedVars()
                freeVarsl = innerTerm.freeVars()
                freeVarsr = self.rightTerm.freeVars()

                needAlphaVars = linkedVarsl & freeVarsr.union(set(variable))
                availableLetters = ((((alphabet - linkedVarsl) - freeVarsl) - freeVarsr) - set(variable))
                for alphaVar in needAlphaVars:
                    newVar = list(availableLetters)[0]
                    availableLetters = availableLetters - set(newVar)

                    print("α-conversió: " + alphaVar + " →  " + newVar)
                    abstraction.show()
                    print(" →  ", end="")
                    abstraction = Abstraction(variable, innerTerm.alphaSubstitution(alphaVar, newVar))
                    abstraction.show()
                    print("")

                print("β-reducció:")
                self.show()
                print(" →  ", end="")
                result = abstraction.term.betaSubstitution(variable, self.rightTerm)
                result.show()
                print("")
                return (result, True)

            case _:
                (reducel, hasBeenReducedl) = self.leftTerm.reduce()
                if hasBeenReducedl:
                    return (Application(reducel, self.rightTerm), True)

                (reducer, hasBeenReducedr) = self.rightTerm.reduce()
                return (Application(self.leftTerm, reducer), hasBeenReducedr)

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

    def show(self):
        print("(", end="")
        self.leftTerm.show()
        self.rightTerm.show()
        print(")", end="")

@dataclass
class Abstraction(Term):
    variable: str
    term: Term

    def reduce(self) -> (Term, bool):
        (reduced, hasBeenReduced) = self.term.reduce()
        return (Abstraction(self.variable, reduced), hasBeenReduced)

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

    def show(self):
        print("(λ" + self.variable + ".", end="")
        self.term.show()
        print(")", end="")



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


# Main program

while True:
    expression = InputStream(input('? '))
    lexer = lcLexer(expression)
    tokenizedExpression = CommonTokenStream(lexer)
    parser = lcParser(tokenizedExpression)
    expressionTree = parser.root()
    internalRepTree = BuildInternalRepVisitor().visit(expressionTree)

    if (internalRepTree):
        print("Arbre:")
        internalRepTree.show()
        print("")

        i = 0
        reducedToNormalForm = False
        while i < 10 and not reducedToNormalForm:
            (internalRepTree, hasBeenReduced) = internalRepTree.reduce()
            reducedToNormalForm = not hasBeenReduced
            i += 1

        print("Resultat:")
        if reducedToNormalForm:
            internalRepTree.show()
            print("\n")
        else:
            print("Nothing\n")

    else:
        for (macroName, macroTerm) in macrosDB.items():
            print(macroName + " ≡ ", end = "")
            macroTerm.show()
            print("")