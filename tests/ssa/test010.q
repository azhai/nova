export function $main() {
@START
  %a =l alloc4 1
  %.t2 =w copy -12
  storeb %.t2, %a
  %b =l alloc4 1
  %.t3 =w copy 0
  storeh %.t3, %b
  %c =l alloc4 1
  %.t4 =w copy 0
  storew %.t4, %c
  %d =l alloc8 1
  %.t5 =l copy 0
  storel %.t5, %d
  %f =l alloc4 1
  %.t6 =s copy s_3.141500
  stores %.t6, %f
  %g =l alloc8 1
  %.t7 =w copy 0
  %.t8 =d swtof %.t7
  stored %.t8, %g
  %w =l alloc4 1
  %.t9 =w copy 100
  storeb %.t9, %w
  %x =l alloc4 1
  %.t10 =w copy 0
  storeh %.t10, %x
  %y =l alloc4 1
  %.t11 =w copy 0
  storew %.t11, %y
  %z =l alloc8 1
  %.t12 =l copy 0
  storel %.t12, %z
  %.t13 =w loadsb %a
  call $printf(l $L1, w %.t13)
  %.t14 =w loadsb %a
  storeh %.t14, %b
  %.t16 =w loadsh %b
  call $printf(l $L1, w %.t16)
  %.t17 =w loadsh %b
  storew %.t17, %c
  %.t19 =w loadsw %c
  call $printf(l $L1, w %.t19)
  %.t20 =w loadsw %c
  %.t21 =l extsw %.t20
  storel %.t21, %d
  %.t22 =l loadl %d
  call $printf(l $L1, l %.t22)
  %.t23 =s loads %f
  %.t24 =d exts %.t23
  call $printf(l $L2, d %.t24)
  %.t25 =s loads %f
  %.t26 =d exts %.t25
  stored %.t26, %g
  %.t27 =d loadd %g
  call $printf(l $L2, d %.t27)
  %.t28 =w loadub %w
  call $printf(l $L1, w %.t28)
  %.t29 =w loadub %w
  storeh %.t29, %x
  %.t31 =w loaduh %x
  call $printf(l $L1, w %.t31)
  %.t32 =w loaduh %x
  storew %.t32, %y
  %.t34 =w loaduw %y
  call $printf(l $L1, w %.t34)
  %.t35 =w loaduw %y
  %.t36 =l extuw %.t35
  storel %.t36, %z
  %.t37 =l loadl %z
  call $printf(l $L1, l %.t37)
  %.t38 =w loadsb %a
  %.t39 =s swtof %.t38
  stores %.t39, %f
  %.t40 =s loads %f
  %.t41 =d exts %.t40
  call $printf(l $L2, d %.t41)
  %.t42 =w loadsh %b
  %.t43 =s swtof %.t42
  stores %.t43, %f
  %.t44 =s loads %f
  %.t45 =d exts %.t44
  call $printf(l $L2, d %.t45)
  %.t46 =w loadsw %c
  %.t47 =s swtof %.t46
  stores %.t47, %f
  %.t48 =s loads %f
  %.t49 =d exts %.t48
  call $printf(l $L2, d %.t49)
  %.t50 =l loadl %d
  %.t51 =s sltof %.t50
  stores %.t51, %f
  %.t52 =s loads %f
  %.t53 =d exts %.t52
  call $printf(l $L2, d %.t53)
  %.t54 =w loadub %w
  %.t55 =s uwtof %.t54
  stores %.t55, %f
  %.t56 =s loads %f
  %.t57 =d exts %.t56
  call $printf(l $L2, d %.t57)
  %.t58 =w loaduh %x
  %.t59 =s uwtof %.t58
  stores %.t59, %f
  %.t60 =s loads %f
  %.t61 =d exts %.t60
  call $printf(l $L2, d %.t61)
  %.t62 =w loaduw %y
  %.t63 =s uwtof %.t62
  stores %.t63, %f
  %.t64 =s loads %f
  %.t65 =d exts %.t64
  call $printf(l $L2, d %.t65)
  %.t66 =l loadl %z
  %.t67 =s ultof %.t66
  stores %.t67, %f
  %.t68 =s loads %f
  %.t69 =d exts %.t68
  call $printf(l $L2, d %.t69)
  %.t70 =w loadsb %a
  %.t71 =d swtof %.t70
  stored %.t71, %g
  %.t72 =d loadd %g
  call $printf(l $L2, d %.t72)
  %.t73 =w loadsh %b
  %.t74 =d swtof %.t73
  stored %.t74, %g
  %.t75 =d loadd %g
  call $printf(l $L2, d %.t75)
  %.t76 =w loadsw %c
  %.t77 =d swtof %.t76
  stored %.t77, %g
  %.t78 =d loadd %g
  call $printf(l $L2, d %.t78)
  %.t79 =l loadl %d
  %.t80 =d sltof %.t79
  stored %.t80, %g
  %.t81 =d loadd %g
  call $printf(l $L2, d %.t81)
  %.t82 =w loadub %w
  %.t83 =d uwtof %.t82
  stored %.t83, %g
  %.t84 =d loadd %g
  call $printf(l $L2, d %.t84)
  %.t85 =w loaduh %x
  %.t86 =d uwtof %.t85
  stored %.t86, %g
  %.t87 =d loadd %g
  call $printf(l $L2, d %.t87)
  %.t88 =w loaduw %y
  %.t89 =d uwtof %.t88
  stored %.t89, %g
  %.t90 =d loadd %g
  call $printf(l $L2, d %.t90)
  %.t91 =l loadl %z
  %.t92 =d ultof %.t91
  stored %.t92, %g
  %.t93 =d loadd %g
  call $printf(l $L2, d %.t93)
@END
  ret
}
data $L2 = { b "%f\n", b 0 }
data $L1 = { b "%d\n", b 0 }
