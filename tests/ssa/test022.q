export function $main() {
@START
  %.t2 =w copy 3
  %.t3 =w copy 2
  %.t4 =w csgtw %.t2, %.t3
  jnz %.t4, @L3, @L1
@L3
  %.t5 =w copy 100
  call $printf(l $L4, w %.t5)
@L5
  jmp @L2
@L1
  %.t6 =w copy 200
  call $printf(l $L4, w %.t6)
@L2
  %.t7 =w copy 23
  %.t8 =w copy 23
  %.t9 =w csltw %.t7, %.t8
  jnz %.t9, @L7, @L6
@L7
  %.t10 =w copy 3142
  call $printf(l $L4, w %.t10)
@L6
  %.t11 =w copy 23
  %.t12 =w copy 23
  %.t13 =w csgew %.t11, %.t12
  jnz %.t13, @L9, @L8
@L9
  %.t14 =w copy 9999
  call $printf(l $L4, w %.t14)
@L8
@END
  ret
}
data $L4 = { b "%d\n", b 0 }
