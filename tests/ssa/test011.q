export function $main() {
@START
  %a =l alloc4 1
  %.t2 =w copy 3
  storew %.t2, %a
  %b =l alloc4 1
  %.t3 =w copy 4
  %.t4 =w loadsw %a
  %.t3 =w add %.t3, %.t4
  storew %.t3, %b
  %.t5 =w loadsw %b
  call $printf(l $L1, w %.t5)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
