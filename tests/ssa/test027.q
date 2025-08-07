export function $fred(w %x) {
@START
  %.t2 =w copy %x
  call $printf(l $L1, w %.t2)
@END
  ret
}
export function $main() {
@START
  %a =l alloc4 1
  %.t3 =w copy 3
  storew %.t3, %a
  %b =l alloc4 1
  %.t4 =w copy 4
  storew %.t4, %b
  %.t5 =w loadsw %a
  %.t6 =w loadsw %b
  %.t5 =w add %.t5, %.t6
  call $printf(l $L2, w %.t5)
  %.t7 =w loadsw %a
  %.t8 =w loadsw %b
  %.t7 =w add %.t7, %.t8
  call $fred(w %.t7)
@END
  ret
}
data $L2 = { b "main %d\n", b 0 }
data $L1 = { b "fred has argument x=%d\n", b 0 }
