export function $main() {
@START
  %i =l alloc4 1
  %.t2 =w copy 0
  storew %.t2, %i
  %.t3 =w copy 1
  storew %.t3, %i
@L1
  %.t4 =w loadsw %i
  %.t5 =w copy 10
  %.t6 =w cslew %.t4, %.t5
  jnz %.t6, @L3, @L2
@L3
  %.t7 =w loadsw %i
  call $printf(l $L4, w %.t7)
  %.t8 =w loadsw %i
  %.t9 =w copy 1
  %.t8 =w add %.t8, %.t9
  storew %.t8, %i
  jmp @L1
@L2
@END
  ret
}
export function $fred(l %x) {
@START
  %.t10 =w copy 5
  call $printf(l $L5, w %.t10)
@END
  ret
}
data $L5 = { b "This function doesn't get called yet\n", b 0 }
data $L4 = { b "Counting from one to ten: %d\n", b 0 }
