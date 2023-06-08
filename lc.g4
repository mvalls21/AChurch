grammar lc;

root : terme                                        # term
     ;

terme : Lletra                                      # letter
      | '('terme')'                                 # parentheses
      | terme terme                                 # application
      | ('λ'|'\\')Lletres'.'terme                   # abstraction     
      ;

Lletra : [a-z];
Lletres : Lletra+;