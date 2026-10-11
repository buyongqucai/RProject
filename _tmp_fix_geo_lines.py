from pathlib import Path
p=Path(r'E:\RProject\_np_stage\geo_analysis.R')
lines=p.read_text().splitlines()
lines=[x for x in lines if 'DEBUG2' not in x and 'DEBUG3' not in x and not x.strip().startswith('ann_idx <-') and not x.strip().startswith('sym <- toupper(trimws(as.character(ann_table')]
idx=next(i for i,x in enumerate(lines) if x.strip().startswith('pd <- pd[keep,,drop=FALSE]'))
lines[idx+1:idx+1]=['  ann_idx <- match(rownames(ex), ann_table[["ID"]])','  sym <- toupper(trimws(as.character(ann_table[["Gene symbol"]][ann_idx])))']
p.write_text('\n'.join(lines)+'\n')
