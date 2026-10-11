from pathlib import Path
p=Path(r'E:\RProject\_np_stage\geo_analysis.R')
s=p.read_text()
s=s.replace('  keep <- group_fun(pd)\n  pd <- pd[keep,,drop=FALSE]; ex <- ex[,keep,drop=FALSE]', '  sel <- group_fun(pd)\n  keep <- sel$keep\n  pd <- pd[keep,,drop=FALSE]; ex <- ex[,keep,drop=FALSE]; group_values <- sel$group[keep]')
s=s.replace(' group <- factor(pd$.group,levels=c("Control","UC"))', ' group <- factor(group_values,levels=c("Control","UC"))')
s=s.replace(' pd$.group <- g; !is.na(g)\n})', ' list(keep=!is.na(g),group=g)\n})')
p.write_text(s)
print('patched')
