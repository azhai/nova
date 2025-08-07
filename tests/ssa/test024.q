export function $main() {
@START
  %i =l alloc4 1
  %.t2 =w copy 0
  storew %.t2, %i
  %.t3 =w loadsw %i
  call $printf(l $L1, w %.t3)
  %.t4 =w copy 1
  storew %.t4, %i
@L2
  %.t5 =w loadsw %i
  %.t6 =w copy 30
  %.t7 =w csltw %.t5, %.t6
  jnz %.t7, @L4, @L3
@L4
  %.t8 =w loadsw %i
  call $printf(l $L1, w %.t8)
  %.t9 =w loadsw %i
  %.t10 =w copy 2
  %.t9 =w add %.t9, %.t10
  storew %.t9, %i
  jmp @L2
@L3
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
