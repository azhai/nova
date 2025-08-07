export function $main() {
@START
  %x =l alloc4 1
  %.t2 =s copy s_23.500000
  stores %.t2, %x
  %y =l alloc8 1
  %.t3 =d copy d_300.220000
  stored %.t3, %y
  %.t4 =d copy d_3.141500
  call $printf(l $L1, d %.t4)
  %.t5 =s loads %x
  %.t6 =d exts %.t5
  call $printf(l $L1, d %.t6)
  %.t7 =d loadd %y
  call $printf(l $L1, d %.t7)
@END
  ret
}
data $L1 = { b "%f\n", b 0 }
