grammar lc;

root : (Macro|Infix) ('≡'|'=') terme                # macroDef
     | terme                                        # term
     ;

terme : Macro                                       # macro
      | terme Infix terme                           # infix
      | Lletra                                      # letter
      | '(' terme ')'                               # parentheses
      | terme terme                                 # application
      | ('λ'|'\\') lletres '.' terme                # abstraction     
      ;

Lletra : [a-z];
lletres : Lletra+;
Macro : [A-Z\u0080-\u00FF][0-9A-Z\u0080-\u00FF]+;
Infix : ~[a-zA-Z \t\r\n] ;
WS : [ \t\n\r]+ -> skip ;
