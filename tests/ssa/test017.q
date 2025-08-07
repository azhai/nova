export function $main() {
@START
  %a =l alloc4 1
  %.t2 =w copy 0
  storew %.t2, %a
  %b =l alloc4 1
  %.t3 =w copy 0
  storew %.t3, %b
  %.t4 =w copy 1
  %.t5 =w copy 4
  %.t4 =w shl %.t4, %.t5
  storew %.t4, %a
  %.t7 =w loadsw %a
  call $printf(l $L1, w %.t7)
  %.t8 =w copy 64
  %.t9 =w copy 3
  %.t8 =w shr %.t8, %.t9
  storew %.t8, %a
  %.t11 =w loadsw %a
  call $printf(l $L1, w %.t11)
  %.t12 =w copy 64
  storew %.t12, %a
  %.t13 =w copy 3
  storew %.t13, %b
  %.t14 =w loadsw %a
  %.t15 =w loadsw %b
  %.t14 =w shr %.t14, %.t15
  storew %.t14, %a
  %.t16 =w loadsw %a
  call $printf(l $L1, w %.t16)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
