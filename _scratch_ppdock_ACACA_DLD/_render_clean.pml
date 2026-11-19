reinitialize
bg_color white
set ray_opaque_background, on
set antialias, 2
set ray_shadows, 0
set cartoon_fancy_helices, 1

load E:/RProject/_scratch_ppdock_ACACA_DLD/ACACA_6G2D_chainC_clean.pdb, ACACA
load E:/RProject/_scratch_ppdock_ACACA_DLD/DLD_6I4Q_chainA_clean.pdb, DLD

hide everything
show cartoon, ACACA or DLD
color marine, ACACA
color tv_orange, DLD
util.cnc ACACA or DLD

# place DLD to the right of ACACA for inspection (NOT a docking result)
center ACACA
translate [180,0,0], DLD

orient ACACA or DLD
zoom ACACA or DLD, buffer=20

png E:/RProject/_scratch_ppdock_ACACA_DLD/fig01_cleaned_ACACA_DLD_side_by_side.png, width=1800, height=1200, dpi=300, ray=1

disable DLD
orient ACACA
zoom ACACA, buffer=8
png E:/RProject/_scratch_ppdock_ACACA_DLD/fig02_ACACA_chainC_clean.png, width=1400, height=1200, dpi=300, ray=1

enable DLD
disable ACACA
orient DLD
zoom DLD, buffer=8
png E:/RProject/_scratch_ppdock_ACACA_DLD/fig03_DLD_chainA_clean.png, width=1400, height=1200, dpi=300, ray=1

save E:/RProject/_scratch_ppdock_ACACA_DLD/cleaned_ACACA_DLD_inspection.pse
quit
