# ATLAS REVENUE MODEL - CRITICAL ANALYSIS

## THE BASIC ASSUMPTION: Volume × Price = Revenue

```
Atlas Revenue = (Proppant Volume in lbs) × (Price per lb)
```

**This seems obvious, but there are MAJOR problems.**

---

## 🚨 CRITICAL ISSUE #1: TIMING MISMATCH

### The Problem: When Does Revenue Happen vs When Do We Measure Volume?

**What Atlas reports as "Q1 Revenue":**
- Revenue recognized when sand is **SHIPPED** from Atlas to the customer
- Typically: Customer orders in December → Atlas ships in January → Revenue recorded in Q1

**What FracFocus measures:**
- Proppant **CONSUMED** (used in frac job)
- Typical flow: Customer orders sand → Receives delivery → **Stores on-site for 1-3 months** → Uses in frac job → Reports to FracFocus 30 days later

**The Lag:**
```
Atlas ships sand:        January 15, 2024 (Q1 revenue)
Customer stores on-site: January 15 - March 1, 2024
Customer uses in frac:   March 1, 2024
FracFocus reporting:     April 1, 2024 (Q1 disclosure)

BUT: Sometimes storage is longer!
- Order in Q4 2023 → Ship in Q4 → Store all winter → Frac in Q2 2024
- Atlas gets Q4 revenue, but FracFocus shows Q2 volume
```

**What this means:**
- ❌ FracFocus Q1 volume ≠ Atlas Q1 shipments
- ❌ Could be 1-6 month lag between shipment and consumption
- ⚠️ **Your model assumes zero lag** (WRONG!)

### How to Test This:
```python
# Compare Atlas's reported volumes to FracFocus volumes with different lags
for lag_months in [0, 1, 2, 3, 6]:
    # Shift FracFocus data forward by lag
    fracfocus_q1_2024 = data from (Jan 2024 - lag) to (Mar 2024 - lag)

    correlation = corr(fracfocus_q1_2024, atlas_reported_q1_2024)

    print(f"Lag of {lag_months} months: R² = {correlation}")
```

**Expected result:** Best correlation will be at 1-3 month lag, NOT zero lag.

---

## 🚨 CRITICAL ISSUE #2: SUPPLIER FIELD ATTRIBUTION

### The Problem: What Does "Supplier" Actually Mean in FracFocus?

**Assumptions we're making:**
1. "Supplier = ATLAS SAND" means Atlas sold the sand
2. All proppant records have Supplier filled in
3. Supplier field is accurate

**Reality check:**

**Test 1: Data Completeness**
```python
# What % of proppant records have Supplier data?
proppant_records = df[df['Purpose'].contains('Proppant')]
with_supplier = proppant_records['Supplier'].notna().sum()
completeness = with_supplier / len(proppant_records)

print(f"Completeness: {completeness:.1%}")

# If < 80%: You're missing 20%+ of Atlas's volume!
```

**Test 2: Atlas Name Variations**
```python
# How many different ways is Atlas listed?
atlas_variations = df[df['Supplier'].str.contains('ATLAS', case=False)]['Supplier'].unique()

print(f"Found {len(atlas_variations)} variations:")
for name in atlas_variations:
    count = len(df[df['Supplier'] == name])
    print(f"  {name}: {count:,} records")

# Example issues:
# - "Atlas Sand Company" vs "Atlas Energy Solutions"
# - "ATLAS" vs "Atlas Sand" vs "Atlas Sand Co."
# - What if they acquired another company and old name still appears?
```

**Test 3: Does Supplier = Who Sold The Sand?**

This is philosophical but important:
- FracFocus asks: "Who supplied this ingredient?"
- Does operator interpret this as:
  - Who sold us the sand? (Atlas)
  - Who delivered it? (trucking company)
  - Who we bought it from? (Could be a distributor, not Atlas directly)

**We have no way to validate this assumption!**

---

## 🚨 CRITICAL ISSUE #3: PRICING IS NOT FLAT

### The Problem: You're Assuming $60/ton for Everything

**Reality of proppant pricing:**

**1. Product Mix:**
```
Atlas's product portfolio (example):
- 100 mesh regional sand: $45/ton (low-end)
- 40/70 Northern White:  $65/ton (mid-range)
- 30/50 Resin-coated:    $95/ton (premium)

If Atlas's Q1 sales are:
- 60% regional ($45) = $27/ton contribution
- 30% white sand ($65) = $19.50/ton contribution
- 10% resin ($95) = $9.50/ton contribution
Average: $56/ton

But you assumed $60/ton → 7% revenue overestimate!
```

**2. Geographic Price Variation:**
```
Permian Basin: $50-55/ton (local sand, low transport)
Eagle Ford:    $60-65/ton (further from mines)
Haynesville:   $65-70/ton (longer haul)

If Atlas sells:
- 70% in Permian at $52/ton
- 30% in Eagle Ford at $63/ton
Weighted avg: $55.30/ton

But you assumed $60/ton → 8.5% overestimate!
```

**3. Contract vs Spot Pricing:**
```
You assumed: 80% contract at $60, 20% spot at $60

Reality might be:
- Contracts locked in Q4 2023 at $55/ton (when oil was $70)
- Spot market in Q1 2024 at $48/ton (oil crashed to $62)
- Weighted: (0.80 × $55) + (0.20 × $48) = $53.60/ton

Your estimate: $60/ton → 12% OVERESTIMATE!
```

**4. Price Changes Quarter-to-Quarter:**
```
Q1 2023: $58/ton (high oil prices, tight supply)
Q2 2023: $62/ton (summer drilling season)
Q3 2023: $55/ton (oil price decline)
Q4 2023: $48/ton (oversupply, weak demand)

If you use $60/ton for all quarters:
- Q1: 3% overestimate
- Q2: 3% underestimate
- Q3: 9% overestimate
- Q4: 25% OVERESTIMATE!
```

### How to Fix This:

**Option 1: Backsolve Historical Pricing (BEST)**
```python
# From Atlas's 10-K/10-Q filings:
for quarter in historical_quarters:
    atlas_revenue = get_reported_revenue(quarter)  # e.g., $425M
    atlas_volume = get_reported_volume(quarter)     # e.g., 7.5M tons

    implied_price = atlas_revenue / atlas_volume

    print(f"{quarter}: ${implied_price:.2f}/ton")

# Use this implied price for future projections
# Assumption: Price changes slowly (valid if 80% contracted)
```

**Option 2: Track Public Spot Indices**
```python
# Bloomberg PPSM (Permian Proppant Spot Market) index
# Or: Scrape from industry reports

# But remember: Spot ≠ Atlas's blended realization
# Spot might be $50/ton, but Atlas's contracts are $60/ton
```

**Option 3: Use Oil Price as Proxy**
```python
# Proppant pricing correlates with oil prices
# Simple model:
proppant_price = 30 + (0.40 × (wti_oil_price - 50))

# Example:
# WTI at $70: Proppant = 30 + 0.40 × 20 = $38/ton... wait that's way off
# This needs calibration!
```

---

## 🚨 CRITICAL ISSUE #4: ATLAS HAS MULTIPLE REVENUE STREAMS

### The Problem: Sand Sales ≠ Total Revenue

**What's in Atlas's 10-K revenue:**
```
Total Revenue: $1.8B

Breakdown (example - need to verify):
- Proppant sales:         $1.5B (83%)
- Transportation/logistics: $200M (11%)
- Terminal services:       $80M (4%)
- Equipment rental:        $20M (1%)
```

**Your model only captures proppant sales!**

If you calculate $1.5B from volume × price, but Atlas reports $1.8B, you'll think you're wrong by 20% when actually you're missing non-proppant revenue.

### How to Fix:
```python
# From 10-K: Find revenue breakdown
# Adjust your model:

proppant_revenue = volume × price
total_revenue = proppant_revenue × 1.2  # Add 20% for other services

# OR: Model only proppant revenue, compare to that segment
```

---

## 🚨 CRITICAL ISSUE #5: MARKET SHARE CHANGES

### The Problem: Atlas's Share Isn't Constant

**Your calculation:**
```python
atlas_volume = fracfocus_data[supplier == 'ATLAS'].sum()
atlas_revenue = atlas_volume × $60/ton
```

**But what if:**
```
2023 Q1: Atlas has 18% market share
2023 Q2: Atlas has 19% market share (won new contract)
2023 Q3: Atlas has 17% market share (lost customer to competitor)
2023 Q4: Atlas has 20% market share (acquired smaller competitor)
```

If you use constant assumptions, you'll miss these dynamics.

### How to Test:
```python
# Track Atlas's market share over time
for quarter in quarters:
    atlas_vol = fracfocus[fracfocus['Supplier'].contains('ATLAS')]['Proppant_lbs'].sum()
    total_vol = fracfocus['Proppant_lbs'].sum()

    market_share = atlas_vol / total_vol

    print(f"{quarter}: {market_share:.1%}")

# Is market share stable or trending?
# Stable: Good for forecasting
# Trending: Need to model the trend
```

---

## 🚨 CRITICAL ISSUE #6: INVENTORY & WORKING CAPITAL

### The Problem: Customers Pre-Buy Sand

**Real-world scenario:**
```
Q4 2023: Major customer pre-orders 50M lbs for Q1 2024
         Atlas ships in December, gets paid, recognizes revenue
         Revenue: Q4 2023

Q1 2024: Customer fracs wells using that sand
         FracFocus disclosure shows Q1 2024 volume

Your model: Attributes revenue to Q1 2024 (WRONG!)
Atlas reported: Q4 2023 revenue
```

**This creates quarter-to-quarter noise.**

### How to Handle:
```python
# Use rolling averages instead of quarterly
atlas_revenue_4q_avg = (Q1 + Q2 + Q3 + Q4) / 4

# Reduces noise from inventory timing
```

---

## 🧪 VALIDATION FRAMEWORK

### Test 1: Volume Correlation Test
```python
# Do our calculated volumes match Atlas's reported volumes?
our_volumes = [...]  # From FracFocus
atlas_reported = [...]  # From 10-K

correlation = np.corrcoef(our_volumes, atlas_reported)[0,1]
rmse = sqrt(mean((our_volumes - atlas_reported)²))

print(f"Correlation: {correlation:.3f}")
print(f"RMSE: {rmse:,.0f} lbs")

# Success criteria:
# Correlation > 0.85 ✅
# Correlation < 0.70 ❌ Model doesn't work
```

### Test 2: Revenue Backtesting
```python
# For last 8 quarters, predict revenue and compare to actual
errors = []

for quarter in historical_quarters:
    # Your model
    predicted_revenue = volume(quarter) × price_assumption

    # Actual
    actual_revenue = atlas_10k_data[quarter]

    error_pct = abs(predicted_revenue - actual_revenue) / actual_revenue
    errors.append(error_pct)

avg_error = mean(errors)

print(f"Average prediction error: {avg_error:.1%}")

# Success criteria:
# <10% error ✅ Model is useful
# >25% error ❌ Model is broken
```

### Test 3: Direction Accuracy
```python
# Even if magnitude is wrong, can you predict UP vs DOWN?
for i in range(1, len(quarters)):
    actual_change = atlas_revenue[i] - atlas_revenue[i-1]
    predicted_change = predicted_revenue[i] - predicted_revenue[i-1]

    if sign(actual_change) == sign(predicted_change):
        correct += 1

directional_accuracy = correct / total

print(f"Directional accuracy: {directional_accuracy:.1%}")

# Success criteria:
# >75% ✅ Can predict direction (tradeable!)
# <60% ❌ No better than coin flip
```

### Test 4: Beat/Miss Predictions
```python
# Can you predict earnings beats vs misses?
for quarter in quarters:
    wall_street_consensus = get_consensus(quarter)
    your_prediction = volume × price
    actual = atlas_reported[quarter]

    # Did you correctly predict beat vs miss?
    you_predicted_beat = (your_prediction > wall_street_consensus)
    actual_beat = (actual > wall_street_consensus)

    if you_predicted_beat == actual_beat:
        correct_calls += 1

accuracy = correct_calls / total_quarters

print(f"Beat/Miss accuracy: {accuracy:.1%}")

# Success criteria:
# >70% ✅ You have an edge over Wall Street
# <55% ❌ No edge, don't trade this
```

---

## 💡 WHAT ACTUALLY MATTERS FOR TRADING

### You DON'T Need Perfect Revenue Prediction

**What you need:**
1. **Direction**: Will Q1 be up or down vs Q4?
2. **Magnitude**: Will Q1 be up 5% or 25%?
3. **Surprise**: Will Q1 beat or miss Wall Street expectations?

**Example:**
```
Wall Street consensus: $450M
Your model predicts:   $485M (+7.8% vs consensus)
Actual result:         $478M (+6.2% vs consensus)

Your prediction was OFF by $7M (1.5%)
But you correctly predicted a BEAT (+7.8% vs +6.2%)
→ Stock went up 8% after earnings
→ You made money ✅
```

**What kills the trade:**
```
Wall Street consensus: $450M
Your model predicts:   $485M (+7.8% beat)
Actual result:         $440M (-2.2% miss)

You were wrong about direction
→ Stock crashed 12%
→ You lost money ❌
```

---

## 🎯 RECOMMENDED APPROACH

### Phase 1: Validate Volume Tracking (DO THIS FIRST)
1. Get Atlas's last 8 quarters of reported volumes (from 10-Ks)
2. Calculate volumes from FracFocus
3. Test correlation
4. **If correlation < 0.70: STOP. Model doesn't work.**
5. **If correlation > 0.85: Proceed to Phase 2.**

### Phase 2: Backsolve Pricing
1. Get Atlas's last 8 quarters of revenue AND volume
2. Calculate implied price = revenue / volume
3. Check if price is stable (std dev < 15%)
4. **If stable: Use average for predictions**
5. **If volatile: Need real-time pricing data**

### Phase 3: Test Predictive Power
1. Can 2-month data predict full quarter? (Test lag)
2. Backtest: Would your model have worked in 2022-2023?
3. Calculate average error
4. **If error < 15%: Tradeable**
5. **If error > 25%: Not tradeable**

### Phase 4: Refinements
1. Adjust for timing lag (1-3 months)
2. Weight by geography (Permian vs Eagle Ford pricing)
3. Track market share trends
4. Model contract pricing separately from spot

---

## 🚨 RED FLAGS THAT MODEL IS BROKEN

### If You See These, STOP TRADING:

1. **Your predicted volumes are 30%+ higher than Atlas reports**
   - Supplier data completeness issue
   - You're counting non-Atlas volume

2. **Correlation between your volumes and Atlas's volumes < 0.70**
   - FracFocus data doesn't match Atlas's shipments
   - Timing lag is too large

3. **Your revenue predictions are consistently off by >20%**
   - Pricing assumptions are wrong
   - Missing revenue streams

4. **You predict 6 quarters correctly, then 4 quarters wrong**
   - Market structure changed
   - Contract terms changed
   - Need to recalibrate

5. **Directional accuracy < 60%**
   - No better than random
   - Don't trade this

---

## 💰 WHAT COULD MAKE THIS WORK

### Positive Signals:

1. **Volume correlation > 0.85**
   - FracFocus is good proxy for Atlas shipments

2. **Pricing is stable (std dev < 10%)**
   - 80% contracted volume dampens price swings
   - Simple price assumption works

3. **Early-quarter data is predictive**
   - Jan-Feb volumes correlate with Q1 total
   - Gives you 6-week trading window

4. **Data completeness > 90%**
   - Most records have Supplier field
   - You're capturing full Atlas volume

5. **Timing lag is consistent**
   - Always 2 months between shipment and consumption
   - Can adjust predictions reliably

---

## 🔧 HOW TO BUILD CONFIDENCE

### Checklist Before Trading Real Money:

- [ ] Validated volume correlation > 0.80 over 8+ quarters
- [ ] Backtested revenue predictions with <15% average error
- [ ] Tested directional accuracy > 70%
- [ ] Verified data completeness > 85%
- [ ] Identified and adjusted for timing lag
- [ ] Calculated realistic pricing (backsolved from Atlas data)
- [ ] Tested on out-of-sample quarters (2022-2023)
- [ ] Compared predictions to Wall Street consensus
- [ ] Paper-traded for 2 quarters before going live

**If all checkboxes = ✅: Model might work**
**If any checkbox = ❌: Fix before trading**

---

## THE HONEST ASSESSMENT

Your core insight is RIGHT:
> "More volume → More revenue"

But the execution has 6+ points of failure:
1. Timing mismatch (shipment vs consumption)
2. Pricing assumptions (flat $60/ton is naive)
3. Data completeness (missing supplier records)
4. Attribution accuracy (does Supplier mean sold-by?)
5. Non-proppant revenue (logistics, services)
6. Market share changes (dynamic, not static)

**This CAN work, but only if:**
- You validate each assumption with historical data
- You backtest thoroughly (8+ quarters)
- You're willing to accept 10-15% prediction error
- You focus on direction (beat/miss) not exact magnitude

**Bottom line:**
- This is NOT "plug and play"
- This COULD be a 20-30% annual return strategy IF validated
- This WILL lose money if you skip validation

**Next step:** Run Phase 1 validation. If correlation > 0.85, keep going. If < 0.70, abandon or pivot.
