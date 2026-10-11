from pathlib import Path
p=Path(r'E:\RProject\_np_stage\geo_analysis.R')
s=p.read_text()
s=s.replace('prep <- function(gse, ann_map, group_fun){','prep <- function(gse, ann_table, group_fun){')
s=s.replace('  sym <- unname(ann_map[rownames(ex)])\n  cat("DEBUG",gse,class(ann_map),class(sym),length(sym),"\\n")', '  ann_idx <- match(rownames(ex), ann_table[["ID"]])\n  sym <- toupper(trimws(as.character(ann_table[["Gene symbol"]][ann_idx])))')
s=s.replace('g92 <- prep("GSE92415",map13158,','g92 <- prep("GSE92415",a13158,')
s=s.replace('g75 <- prep("GSE75214",map6244,','g75 <- prep("GSE75214",a6244,')
p.write_text(s)
