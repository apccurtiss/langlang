atom :: WORD:value;
times :: atom:left match {
    pop "*" => times:right
    default => return left
}
plus :: times:left ["+" plus:right];