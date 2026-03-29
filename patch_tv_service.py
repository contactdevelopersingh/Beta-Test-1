import re

with open("backend/tv_service/index.js", "r") as f:
    content = f.read()

# Modify getTA
search_block = """app.get('/ta/:assetId', async (req, res) => {
  const { assetId } = req.params;
  const tvSymbol = SYMBOL_MAP[assetId];
  if (!tvSymbol) return res.json({ error: 'Unknown asset', data: null });"""

replace_block = """app.get('/ta/:assetId', async (req, res) => {
  const { assetId } = req.params;
  let tvSymbol = SYMBOL_MAP[assetId];
  if (!tvSymbol) {
    if (assetId.startsWith('NSE:') || assetId.startsWith('BSE:')) {
      tvSymbol = assetId;
    } else {
      return res.json({ error: 'Unknown asset', data: null });
    }
  }"""

content = content.replace(search_block, replace_block)

# Modify batchTA
search_block2 = """    const tvSymbol = SYMBOL_MAP[id];
    if (!tvSymbol) return;"""

replace_block2 = """    let tvSymbol = SYMBOL_MAP[id];
    if (!tvSymbol && (id.startsWith('NSE:') || id.startsWith('BSE:'))) {
      tvSymbol = id;
    }
    if (!tvSymbol) return;"""

content = content.replace(search_block2, replace_block2)

with open("backend/tv_service/index.js", "w") as f:
    f.write(content)
