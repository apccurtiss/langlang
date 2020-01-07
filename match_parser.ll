abstract BinaryOperator(ops, next) :: next:left match {
    pop ops:op => times:right
    default => return left
};

Atom :: WORD:value;
new Times :: BinaryOperator("*" | "/", Atom);
new Plus :: BinaryOperator("+" | "-", Times);