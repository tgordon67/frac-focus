# FracFocus Dashboard - Complete Beginner's Guide for Windows

## 🎯 What This Tool Does (In Plain English)

This tool shows you **proppant and water usage** in oil & gas drilling, with focus on the **Permian Basin** in Texas/New Mexico. Think of it like a dashboard for your car, but instead it shows data about fracking operations.

**You get:**
- Charts showing trends over time
- Data from 2001 to 2026 (25 years!)
- 211,347 wells analyzed
- Interactive graphs you can click and explore

---

## 🚀 Step 1: Open Your Dashboard (RIGHT NOW!)

### What I Just Did For You:
✅ I started the dashboard application (it's running on your computer)
✅ All the data is ready (411 MB of FracFocus data analyzed)
✅ Everything is working

### What YOU Need To Do:

**1. Open your web browser** (Chrome, Firefox, Edge - any browser works)

**2. Copy and paste this into the address bar:**
```
http://127.0.0.1:8050
```

**3. Press Enter**

You'll see a colorful dashboard with charts and dropdowns!

---

## 📊 What You'll See (Step-by-Step)

### When the Dashboard Opens:

```
┌─────────────────────────────────────────────────────┐
│  FracFocus Proppant & Water Analysis Dashboard      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [Controls Panel]        │  [Main Charts Area]      │
│  - View Level            │                          │
│  - Metric                │    📈 Big Graph Here    │
│  - Select Regions        │                          │
│  - Download Button       │                          │
│                          │                          │
│  [Summary Stats]         │   📊 Bar Chart Here     │
│  - Total Proppant        │                          │
│  - Total Water           │                          │
│  - Total Wells           │                          │
└─────────────────────────────────────────────────────┘
```

### The Controls Panel (Left Side):

**"View Level" Dropdown:**
- Basin View (RECOMMENDED - start here!)
- State View
- Permian Basin (County)

**"Metric" Dropdown:**
- Proppant (Million lbs) - how much sand/proppant used
- Water (Million gallons) - how much water used
- Well Count - number of wells
- Avg Proppant per Well
- Avg Water per Well

**"Select Regions" Dropdown:**
- Click to choose which basins to see
- For Permian Basin focus, select "Permian Basin"

---

## 🎮 How to Use the Dashboard (Easy!)

### Task 1: View Permian Basin Data

**Step 1:** In "View Level" dropdown → Select **"Basin View"**

**Step 2:** In "Select Regions" dropdown → Click and select **"Permian Basin"**

**Step 3:** In "Metric" dropdown → Select **"Proppant (Million lbs)"**

**What you'll see:**
- A line chart showing proppant usage from 2001 to 2026
- The line goes up or down showing trends
- Hover your mouse over the line to see exact numbers!

### Task 2: Compare Multiple Basins

**Step 1:** In "Select Regions" → Select multiple basins:
- Permian Basin
- Eagle Ford
- Haynesville

**What you'll see:**
- 3 different colored lines
- Each represents a different basin
- You can compare which basin uses more proppant!

### Task 3: Look at Specific Counties in Permian

**Step 1:** In "View Level" → Select **"Permian Basin (County)"**

**Step 2:** Scroll down to see county-level details

**What you'll see:**
- Martin County, Midland County, Ector County, etc.
- Which counties use the most proppant
- Trends for each county over time

### Task 4: Export Data to Excel

**Step 1:** Click the **"Download Data"** button (left panel, bottom)

**Step 2:** A CSV file downloads automatically

**Step 3:** Open it in Excel to do your own analysis!

---

## 💡 Understanding the Charts

### The Main Line Chart (Top):
- **X-axis (horizontal):** Time (quarters like "2023Q1" = January-March 2023)
- **Y-axis (vertical):** The metric you selected (proppant, water, etc.)
- **Lines:** Each colored line is a different region
- **Hover:** Put your mouse on any point to see the exact number

### The Bar Chart (Bottom):
- Shows **Top 10** regions by total amount
- Horizontal bars = easier to read long names
- Longer bar = more proppant/water used

### Summary Stats (Bottom):
- **Big numbers** showing totals
- Updates when you change filters
- Good for quick overview

---

## 🔄 Getting Updates (Simple Options)

Since you're new to this, here are your options from **easiest to most advanced:**

### Option 1: Just Ask Me! (EASIEST) ⭐
**What:** You simply say: *"Claude, please update my FracFocus data"*

**How it works:**
1. You send me a message here
2. I download the latest data
3. I run the analysis
4. I tell you when it's ready
5. You refresh your browser to see updated dashboard

**When to do this:** Once a week or whenever you need fresh data

**Pros:** Zero technical knowledge needed
**Cons:** You have to remember to ask me

---

### Option 2: Windows Task Scheduler (Medium) 📅
**What:** Your computer automatically updates data every Monday morning

**How to set it up:**
1. Press **Windows Key + R**
2. Type: `taskschd.msc` and press Enter
3. Click "Create Basic Task" (right side)
4. Name it: "FracFocus Update"
5. Trigger: Weekly, Monday, 8:00 AM
6. Action: Start a program
7. Program: Browse to `C:\path\to\frac-focus\automate_analysis.bat`
   - (Replace `C:\path\to` with where your files are)
8. Click Finish

**When it runs:** Every Monday at 8 AM automatically

**Pros:** Hands-off, always current
**Cons:** Requires 15-20 minutes of setup

---

### Option 3: Run It Yourself When Needed (Advanced) 💻
**What:** You run a file when you want updates

**How:**
1. Open File Explorer
2. Go to your frac-focus folder
3. Double-click: `automate_analysis.bat`
4. Wait 30-60 minutes
5. Refresh your dashboard

**When to do this:** When you want to control exactly when updates happen

**Pros:** Full control
**Cons:** Most technical option

---

## 🛑 How to Stop the Dashboard

### When You're Done Looking at Data:

**Method 1: Just close your browser tab**
- Dashboard keeps running in background
- Next time you want to use it, just go to http://127.0.0.1:8050 again
- Data will still be there!

**Method 2: Actually stop it** (if you want to free up resources)
- In Claude Code, tell me: *"Please stop the dashboard"*
- I'll shut it down for you
- To start again later, just ask me!

---

## 📖 Understanding the Data

### What is "Proppant"?
Small particles (usually sand) pumped into oil/gas wells to keep fractures open. More proppant = more production capability.

### What is a "Basin"?
A large geographic area where oil/gas is found. Examples:
- **Permian Basin:** West Texas & SE New Mexico (HUGE!)
- **Eagle Ford:** South Texas
- **Haynesville:** East Texas & NW Louisiana

### What is a "Quarter"?
3-month periods:
- **Q1:** January-March
- **Q2:** April-June
- **Q3:** July-September
- **Q4:** October-December

So "2023Q2" means April-June 2023.

### What is "Disclosure"?
A report filed by oil/gas companies showing what they used in a fracking job. Your dataset has 211,347 of these reports!

---

## 🎯 Common Questions

### Q: Why does my chart look different than expected?
**A:** Check your filters! Make sure you selected the right:
- View Level (Basin/State/County)
- Regions (which basins you want to see)
- Metric (what you're measuring)

### Q: Can I zoom in on the chart?
**A:** Yes! Scroll down to see the chart, then hover over it. You'll see zoom controls in the top-right corner of the chart.

### Q: How do I see data for just one year?
**A:** Currently you see all years. To focus on specific years, download the CSV and filter in Excel.

### Q: What if I want to analyze a specific well?
**A:** Use the "quarterly_detail.csv" file in the `output` folder. Open it in Excel and search by well name or API number.

### Q: How often is FracFocus data updated?
**A:** FracFocus updates their database 5 days a week (Monday-Friday). Most new data comes in every few days.

### Q: How do I know if I have the latest data?
**A:** Look at the date range shown in the dashboard. If it says "2026Q1" at the end, you have data up to January-March 2026 (the latest!).

---

## 🚨 Troubleshooting

### Problem: "This site can't be reached" when opening 127.0.0.1:8050
**Solution:**
1. The dashboard isn't running yet. Tell me: *"Please start the dashboard"*
2. Wait 10 seconds
3. Refresh your browser

### Problem: Dashboard is very slow
**Solution:**
1. Close other browser tabs
2. Select fewer regions (not all basins at once)
3. Pick a simpler metric (Well Count loads faster than Details)

### Problem: I closed my browser, now what?
**Solution:**
1. Open your browser again
2. Go to http://127.0.0.1:8050
3. Dashboard should still be there!
4. If not, ask me to restart it

### Problem: I want to see data from a specific well
**Solution:**
1. Don't use the dashboard for this
2. Open the file: `output/quarterly_detail.csv`
3. Open it in Excel
4. Use Excel's search/filter to find your well

### Problem: Where did my downloaded CSV go?
**Solution:**
1. Check your Downloads folder (usually `C:\Users\YourName\Downloads`)
2. Look for a file named `fracfocus_basin_data.csv` or similar
3. It downloads wherever your browser normally saves files

---

## 📁 Where Everything Is Saved

```
C:\Users\YourName\frac-focus\    (wherever you put it)
│
├── dashboard.py                  ← The dashboard program
├── output\
│   ├── quarterly_by_basin.csv   ← Basin data (open in Excel)
│   ├── quarterly_by_state.csv   ← State data
│   ├── permian_by_county.csv    ← Permian detail ⭐
│   └── quarterly_detail.csv     ← All wells (BIG file)
│
├── data\
│   └── fracfocus_data.zip       ← Original download (411 MB)
│
└── logs\
    └── automation_*.log         ← Technical logs (ignore unless troubleshooting)
```

**Important files for you:**
- `permian_by_county.csv` - Your Permian Basin focus
- `quarterly_by_basin.csv` - Basin comparisons
- `validation_report.txt` - Data quality notes

---

## 🎓 Next Steps

### You've Already Done:
✅ Dashboard is running
✅ Data is analyzed (7.3 million records!)
✅ Ready to explore

### What To Do Now:
1. **Open the dashboard** → http://127.0.0.1:8050
2. **Play around** with the dropdowns and charts
3. **Focus on Permian Basin** → That's your main interest
4. **Export data** if you want to analyze in Excel
5. **Ask me questions** if anything is confusing!

### Regular Use:
- **Weekly:** Ask me to update data OR set up Task Scheduler
- **Anytime:** Open http://127.0.0.1:8050 to view dashboard
- **Analysis:** Download CSVs and analyze in Excel
- **Questions:** Just ask me! I'm here to help

---

## 💬 How to Talk to Me

You can say things like:

**For Updates:**
- "Claude, please update my FracFocus data"
- "Can you download the latest data and run the analysis?"
- "I need fresh data for this week"

**For Help:**
- "The dashboard won't open, can you help?"
- "How do I see just Martin County data?"
- "Can you export Permian Basin data for me?"

**For Stopping:**
- "Please stop the dashboard, I'm done for today"
- "Shut down the dashboard please"

**I'll handle all the technical stuff - you just ask!** 🚀

---

## 🎉 You're All Set!

**Remember:**
- Dashboard URL: **http://127.0.0.1:8050**
- Focus on: **Permian Basin** data
- Ask me: Anytime you need help or updates
- Files: In the `output` folder for Excel analysis

**Have fun exploring your data!** 📊✨

---

## 📞 Quick Reference Card

| What You Want | What To Do |
|---------------|------------|
| Open dashboard | Go to: http://127.0.0.1:8050 in browser |
| Update data | Ask me: "Update FracFocus data" |
| Stop dashboard | Ask me: "Stop the dashboard" |
| See Permian data | Dashboard → View Level: Basin → Select: Permian Basin |
| Export to Excel | Click "Download Data" button |
| Get help | Ask me questions anytime! |

---

**That's everything! You don't need to know any technical stuff - just enjoy using your data dashboard!** 🎊
