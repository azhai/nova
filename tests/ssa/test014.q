export function $main() {
@START
  %a =l alloc4 1
  %.t2 =w copy 1
  storeb %.t2, %a
  %b =l alloc4 1
  %.t3 =w copy 0
  storeb %.t3, %b
  %d =l alloc4 1
  %.t4 =w loadsb %a
  %.t5 =w loadsb %b
  %.t4 =w add %.t4, %.t5
  %.t6 =s swtof %.t4
  stores %.t6, %d
  %c =l alloc4 1
  %.t7 =w loadsb %a
  %.t8 =w loadsb %b
  %.t7 =w sub %.t7, %.t8
  storew %.t7, %c
  %.t10 =w loadsw %c
  call $printf(l $L1, w %.t10)
  %.t11 =s loads %d
  %.t12 =d exts %.t11
  call $printf(l $L2, d %.t12)
@END
  ret
}
data $L2 = { b "%f\n", b 0 }
data $L1 = { b "%d\n", b 0 }
