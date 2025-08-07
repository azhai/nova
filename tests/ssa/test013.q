export function $main() {
@START
  %a =l alloc4 1
  %.t2 =w copy 12
  storew %.t2, %a
  %b =l alloc4 1
  %.t3 =w copy 10
  storew %.t3, %b
  %c =l alloc4 1
  %.t4 =w copy 0
  storeb %.t4, %c
  %d =l alloc4 1
  %.t5 =w loadsw %a
  %.t6 =w loadsw %b
  %.t5 =w add %.t5, %.t6
  %.t7 =w loadsw %a
  %.t8 =w loadsw %b
  %.t7 =w sub %.t7, %.t8
  %.t9 =w csltw %.t5, %.t7
  storeb %.t9, %d
  %.t10 =w loadsw %a
  %.t11 =w loadsw %b
  %.t10 =w add %.t10, %.t11
  %.t12 =w loadsw %a
  %.t13 =w loadsw %b
  %.t12 =w sub %.t12, %.t13
  %.t14 =w csgtw %.t10, %.t12
  storeb %.t14, %c
  %.t15 =w loadsb %c
  call $printf(l $L1, w %.t15)
  %.t16 =w loadsb %d
  call $printf(l $L1, w %.t16)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
