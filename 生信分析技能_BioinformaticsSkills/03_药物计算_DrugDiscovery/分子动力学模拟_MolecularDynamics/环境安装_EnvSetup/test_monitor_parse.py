"""Replay ADA 2 ns monitor xvg through the new column rules. Exit 0 if healthy."""
import re
import sys
from pathlib import Path

src = Path.home() / "md_runs/ADA_Adenosine_7RTG/monitor/energy_TP.xvg"
log = Path.home() / "md_runs/ADA_Adenosine_7RTG/md.log"
if not src.is_file():
    sys.exit("missing energy_TP.xvg")

leg = {}
rows = []
for line in src.read_text().splitlines():
    m = re.match(r'@\s*s(\d+)\s+legend\s+"([^"]+)"', line)
    if m:
        leg[m.group(2).lower()] = int(m.group(1)) + 1
        continue
    if not line or line[0] in "#@":
        continue
    parts = line.split()
    rows.append([float(x) for x in parts])

ti, pi = leg["temperature"], leg["potential"]
temps = [r[ti] for r in rows]
pots = [r[pi] for r in rows]
t_recent = sum(temps[-20:]) / 20
p_recent = sum(pots[-20:]) / 20
t_med = sorted(temps)[len(temps) // 2]
p_med = sorted(pots)[len(pots) // 2]
print(f"legend {leg}")
print(f"temp_recent={t_recent:.2f} median={t_med:.2f}")
print(f"pot_recent={p_recent:.3g} median={p_med:.3g}")
assert 250 <= t_recent <= 350, t_recent
assert p_med < -1e5
# old bug: column 1 mean was potential
old = sum(r[1] for r in rows[-20:]) / 20
assert old < -1e5, old
print("old_bug_col1", old)

# md.log: warnangle present, but no NaN after Started mdrun
text = log.read_text(errors="replace").split("Started mdrun", 1)
assert "warnangle" in log.read_text(errors="replace").lower()
body = text[1] if len(text) > 1 else ""
assert not re.search(r"(^|[^A-Za-z])nan([^A-Za-z]|$)", body, re.I)
print("log_after_start_clean")
print("PARSE_OK")
