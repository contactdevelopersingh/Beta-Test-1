import re

with open("frontend/src/pages/MarketsPage.jsx", "r") as f:
    content = f.read()

# Add import for TradingChart if missing
if "import TradingChart" not in content:
    content = content.replace("import { Card, CardContent, CardHeader, CardTitle }", "import TradingChart from '../components/TradingChart';\nimport { Card, CardContent, CardHeader, CardTitle }")

# Update state to track selected asset for graph
if "const [selectedAsset, setSelectedAsset]" not in content:
    content = content.replace("const [tab, setTab] = useState('crypto');", "const [tab, setTab] = useState('crypto');\n  const [selectedAsset, setSelectedAsset] = useState(null);")
    content = content.replace("useEffect(() => {\n    const fetchSparklines", "useEffect(() => {\n    if (tab === 'crypto' && crypto.length > 0 && !selectedAsset) setSelectedAsset(crypto[0]);\n    else if (tab === 'forex' && forex.length > 0 && !selectedAsset) setSelectedAsset(forex[0]);\n    else if (tab === 'indian' && indian.length > 0 && !selectedAsset) setSelectedAsset(indian[0]);\n  }, [crypto, forex, indian, tab]);\n\n  useEffect(() => {\n    const fetchSparklines")
    content = content.replace("onClick={() => navigate(`/chart?asset=${item.id}&type=${item.type || tab}`)}", "onClick={() => setSelectedAsset(item)}")

# Find return statement
search_return = """  return (
    <div className="space-y-6 page-enter" data-testid="markets-page">"""

replace_return = """  return (
    <div className="space-y-6 page-enter" data-testid="markets-page">
      {selectedAsset && (
        <Card className="glass-panel border-white/10 overflow-hidden fade-in relative h-[400px]">
          <div className="absolute top-4 left-4 z-10">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              {selectedAsset.name} <Badge className="text-[10px] bg-white/5">{selectedAsset.symbol}</Badge>
            </h2>
            <div className="flex gap-4 mt-1">
              <span className={`text-lg font-data font-semibold ${priceChanges[selectedAsset.id] === 'up' ? 'text-[#10B981]' : priceChanges[selectedAsset.id] === 'down' ? 'text-[#EF4444]' : 'text-white'}`}>
                ${selectedAsset.price?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 6}) || '0.00'}
              </span>
              <span className={`text-sm flex items-center font-data ${selectedAsset.change_24h >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                {selectedAsset.change_24h >= 0 ? '+' : ''}{selectedAsset.change_24h}%
              </span>
            </div>
          </div>
          <TradingChart assetId={selectedAsset.id} assetType={selectedAsset.type || tab} height={400} />
        </Card>
      )}"""

content = content.replace(search_return, replace_return)

with open("frontend/src/pages/MarketsPage.jsx", "w") as f:
    f.write(content)
