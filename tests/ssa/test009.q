export function $main() {
@START
  %x =l alloc4 1
  %.t2 =w copy 2
  %.t3 =w copy 3
  %.t4 =w copy 5
  %.t3 =w mul %.t3, %.t4
  %.t2 =w add %.t2, %.t3
  storew %.t2, %x
  %f =l alloc4 1
  %.t6 =s copy s_3.200000
  %.t7 =s copy s_2.300000
  %.t6 =s add %.t6, %.t7
  stores %.t6, %f
  %g =l alloc4 1
  %.t8 =w copy 23
  %.t9 =s swtof %.t8
  stores %.t9, %g
  %.t10 =w loadsw %x
  call $printf(l $L1, w %.t10)
  %.t11 =s loads %f
  %.t12 =d exts %.t11
  call $printf(l $L2, d %.t12)
  %.t13 =s loads %g
  %.t14 =d exts %.t13
  call $printf(l $L2, d %.t14)
  %.t15 =w copy 23
  %.t16 =w copy 37
  %.t15 =w add %.t15, %.t16
  %.t17 =s swtof %.t15
  stores %.t17, %g
  %.t18 =s loads %g
  %.t19 =d exts %.t18
  call $printf(l $L2, d %.t19)
@END
  ret
}
data $L2 = { b "%f\n", b 0 }
data $L1 = { b "%d\n", b 0 }
