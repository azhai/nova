export function $main() {
@START
  %fred =l alloc4 1
  %.t2 =w copy 1
  storeb %.t2, %fred
  %jim =l alloc4 1
  %.t3 =w copy 0
  storeb %.t3, %jim
  %mary =l alloc4 1
  %.t4 =w copy 17
  %.t5 =w copy 14
  %.t6 =w cnew %.t4, %.t5
  storeb %.t6, %mary
  %x =l alloc4 1
  %.t7 =w loadsb %mary
  storew %.t7, %x
  %y =l alloc4 1
  %.t9 =w copy 0
  storew %.t9, %y
  %dave =l alloc4 1
  %.t10 =w loadsb %fred
  storeb %.t10, %dave
  %.t11 =w loadsb %fred
  call $printf(l $L1, w %.t11)
  %.t12 =w loadsb %jim
  call $printf(l $L1, w %.t12)
  %.t13 =w copy 3
  %.t14 =w copy 2
  %.t15 =w csgtw %.t13, %.t14
  storeb %.t15, %jim
  %.t16 =w loadsb %jim
  call $printf(l $L1, w %.t16)
  %.t17 =w loadsb %mary
  call $printf(l $L1, w %.t17)
  %.t18 =w loadsw %x
  call $printf(l $L1, w %.t18)
  %.t19 =w loadsw %y
  call $printf(l $L1, w %.t19)
  %.t20 =w loadsb %dave
  call $printf(l $L1, w %.t20)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
