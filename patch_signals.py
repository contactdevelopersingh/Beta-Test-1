import re

with open("frontend/src/pages/SignalsPage.js", "r") as f:
    content = f.read()

# 1. Update the Search Input logic for Indian assets
search_input = """              {assetType === 'indian' ? (
                <div className="relative">
                  <Input
                    placeholder="Search stock..."
                    value={assetId ? assets.find(a => a.id === assetId)?.name || assetId : ''}
                    onChange={e => {
                      const q = e.target.value.toLowerCase();
                      const match = assets.find(a => a.name.toLowerCase().includes(q) || a.id.includes(q));
                      if (match) setAssetId(match.id);
                    }}
                    className="w-[200px] bg-black/50 border-white/10 text-white text-sm"
                    data-testid="asset-search-input"
                    list="indian-assets-list"
                  />
                  <datalist id="indian-assets-list">
                    {assets.map(a => <option key={a.id} value={a.name} />)}
                  </datalist>
                </div>
              ) : ("""

replace_input = """              {assetType === 'indian' ? (
                <div className="relative">
                  <Input
                    placeholder="e.g. NSE:RELIANCE or search..."
                    value={assetId}
                    onChange={e => {
                      const val = e.target.value;
                      setAssetId(val);
                    }}
                    className="w-[200px] bg-black/50 border-white/10 text-white text-sm"
                    data-testid="asset-search-input"
                    list="indian-assets-list"
                  />
                  <datalist id="indian-assets-list">
                    {assets.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                  </datalist>
                </div>
              ) : ("""

content = content.replace(search_input, replace_input)

# 2. Update generate signal button payload for Indian custom assets
search_generate = """      const payload = {
        asset_id: assetId,
        asset_name: asset.name,
        asset_type: assetType,"""

replace_generate = """      let actualAssetName = asset ? asset.name : assetId;
      let actualAssetId = assetId;
      if (assetType === 'indian' && !asset) {
        if (!assetId.startsWith('NSE:') && !assetId.startsWith('BSE:')) {
          actualAssetId = 'NSE:' + assetId.toUpperCase();
        }
      }
      const payload = {
        asset_id: actualAssetId,
        asset_name: actualAssetName,
        asset_type: assetType,"""

content = content.replace(search_generate, replace_generate)

# Update generate signal to remove dependency on asset being found
search_generate_return = """  const generateSignal = async () => {
    const asset = assets.find(a => a.id === assetId);
    if (!asset) return;
    if (selectedTimeframes.length < 1) {"""

replace_generate_return = """  const generateSignal = async () => {
    const asset = assets.find(a => a.id === assetId);
    if (!asset && assetType !== 'indian') return;
    if (assetType === 'indian' && !assetId) return;
    if (selectedTimeframes.length < 1) {"""

content = content.replace(search_generate_return, replace_generate_return)

# 3. Add slide-up-fade and stagger-* classes to signal cards
search_card = """              <Card key={sig.signal_id || i}
                className={`glass-panel border-white/10 card-hover overflow-hidden ${sig.direction === 'BUY' ? 'signal-card-buy' : 'signal-card-sell'}`}"""

replace_card = """              <Card key={sig.signal_id || i}
                className={`glass-panel border-white/10 card-hover overflow-hidden slide-up-fade stagger-${(i % 4) + 1} ${sig.direction === 'BUY' ? 'signal-card-buy' : 'signal-card-sell'}`}"""

content = content.replace(search_card, replace_card)

# 4. Add pulse-glow to Generate button
search_btn = """          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95 uppercase tracking-wide font-semibold px-8 py-2.5 btn-glow btn-ripple\""""

replace_btn = """          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95 uppercase tracking-wide font-semibold px-8 py-2.5 btn-glow btn-ripple pulse-glow btn-hover-effect\""""

content = content.replace(search_btn, replace_btn)

# Write back
with open("frontend/src/pages/SignalsPage.js", "w") as f:
    f.write(content)
