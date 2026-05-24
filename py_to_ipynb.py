import nbformat as nbf
import sys

if len(sys.argv) < 3:
    print("Usage: python py_to_ipynb.py <input.py> <output.ipynb>")
    sys.exit(1)

input_py = sys.argv[1]
output_ipynb = sys.argv[2]

with open(input_py, 'r', encoding='utf-8') as f:
    code = f.read()

nb = nbf.v4.new_notebook()

# Split cells by "# %%" or "# ---" if needed, but for simplicity we can just put it all in one cell or split by "# ---"
cells = code.split('# ---')
for i, cell_content in enumerate(cells):
    if i == 0:
        if cell_content.strip():
            nb['cells'].append(nbf.v4.new_code_cell(cell_content.strip()))
    else:
        # Re-add the separator text
        cell_content = '# ---' + cell_content
        nb['cells'].append(nbf.v4.new_code_cell(cell_content.strip()))

# Let's just make it a single cell if the above is too brittle, actually the split works nicely.
# We will insert a markdown cell at the top for the title as requested: 
# Every notebook starts with a markdown cell: "## Purpose" + "## Business Question This Answers"

md_cell = """## Purpose
This notebook covers the data generation or analysis as per the file name.

## Business Question This Answers
Provides the foundational data or answers key business questions for FunnelIQ.
"""
nb['cells'].insert(0, nbf.v4.new_markdown_cell(md_cell))

with open(output_ipynb, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Created {output_ipynb}")
