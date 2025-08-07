export function $main() {
@START
  %mary =l alloc4 1
  %.t2 =w copy 23
  storew %.t2, %mary
  %fred =l alloc4 1
  %.t3 =w copy 7
  storeh %.t3, %fred
  %foo =l alloc4 1
  %.t4 =w copy 33
  storew %.t4, %foo
  %bar =l alloc4 1
  %.t5 =w copy 7
  storeh %.t5, %bar
  %.t6 =w loaduw %mary
  %.t7 =w loaduh %fred
  %.t6 =w add %.t6, %.t7
  storew %.t6, %mary
  %.t9 =w loaduw %mary
  call $printf(l $L1, w %.t9)
  %.t10 =w loadsh %bar
  %.t12 =w loadsw %foo
  %.t10 =w add %.t10, %.t12
  storew %.t10, %foo
  %.t13 =w loadsw %foo
  call $printf(l $L1, w %.t13)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
