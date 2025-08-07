export function $main() {
@START
  %x =l alloc4 1
  %.t2 =s copy s_23.000000
  stores %.t2, %x
  %y =l alloc4 1
  %.t3 =s copy s_17.000000
  stores %.t3, %y
  %z =l alloc4 1
  %.t4 =s copy s_0.000000
  stores %.t4, %z
  %a =l alloc8 1
  %.t5 =d copy d_0.000000
  stored %.t5, %a
  %.t6 =s loads %x
  %.t7 =s loads %y
  %.t6 =s add %.t6, %.t7
  stores %.t6, %z
  %.t8 =s loads %x
  %.t9 =s loads %y
  %.t8 =s sub %.t8, %.t9
  %.t10 =d exts %.t8
  stored %.t10, %a
  %.t11 =s loads %z
  %.t12 =d exts %.t11
  call $printf(l $L1, d %.t12)
  %.t13 =d loadd %a
  call $printf(l $L1, d %.t13)
@END
  ret
}
data $L1 = { b "%f\n", b 0 }
