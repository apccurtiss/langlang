abstract BinaryOperator(op, next) :: next:left op next:right

Atom :: WORD:value;
instance Times :: BinaryOperator("*" | "/", Atom);
instance Plus :: BinaryOperator("+" | "-", Times);