from pathlib import Path
p=Path(r'E:\RProject\_np_stage\geo_analysis.R')
s=p.read_text().replace('keep <- sel$keep','keep <- as.logical(unlist(sel$keep))').replace('group_values <- sel$group[keep]','group_values <- as.character(unlist(sel$group))[keep]')
p.write_text(s)
