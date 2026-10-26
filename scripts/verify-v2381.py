from pathlib import Path
s=Path('src/trends-main.jsx').read_text()
assert ".sort((a,b)=>b.weight-a.weight || Math.abs(b.contribution)-Math.abs(a.contribution))" in s
assert "GDP weight*" in s and "Contribution" in s and "Country contributions" in s
print('V2.38.1 GDP-WEIGHT TABLE ORDER CONTRACT OK')
