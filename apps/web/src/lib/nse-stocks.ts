/**
 * Comprehensive NSE stock list for instant client-side search.
 * Covers Nifty 50, Nifty Next 50, and popular mid-caps (~200 stocks).
 */

export interface NseStock {
  symbol: string;
  name: string;
  sector: string;
}

export const NSE_STOCKS: NseStock[] = [
  // ── Nifty 50 ──────────────────────────────────────────────────────
  { symbol: "RELIANCE", name: "Reliance Industries Ltd", sector: "Energy" },
  { symbol: "TCS", name: "Tata Consultancy Services Ltd", sector: "IT" },
  { symbol: "HDFCBANK", name: "HDFC Bank Ltd", sector: "Banking" },
  { symbol: "INFY", name: "Infosys Ltd", sector: "IT" },
  { symbol: "ICICIBANK", name: "ICICI Bank Ltd", sector: "Banking" },
  { symbol: "BHARTIARTL", name: "Bharti Airtel Ltd", sector: "Telecom" },
  { symbol: "SBIN", name: "State Bank of India", sector: "Banking" },
  { symbol: "LT", name: "Larsen & Toubro Ltd", sector: "Infrastructure" },
  { symbol: "ITC", name: "ITC Ltd", sector: "FMCG" },
  { symbol: "HCLTECH", name: "HCL Technologies Ltd", sector: "IT" },
  { symbol: "BAJFINANCE", name: "Bajaj Finance Ltd", sector: "NBFC" },
  { symbol: "MARUTI", name: "Maruti Suzuki India Ltd", sector: "Automobile" },
  { symbol: "TATAMOTORS", name: "Tata Motors Ltd", sector: "Automobile" },
  { symbol: "SUNPHARMA", name: "Sun Pharmaceutical Industries Ltd", sector: "Pharma" },
  { symbol: "KOTAKBANK", name: "Kotak Mahindra Bank Ltd", sector: "Banking" },
  { symbol: "TITAN", name: "Titan Company Ltd", sector: "Consumer" },
  { symbol: "AXISBANK", name: "Axis Bank Ltd", sector: "Banking" },
  { symbol: "ADANIENT", name: "Adani Enterprises Ltd", sector: "Conglomerate" },
  { symbol: "NTPC", name: "NTPC Ltd", sector: "Power" },
  { symbol: "ASIANPAINT", name: "Asian Paints Ltd", sector: "Paints" },
  { symbol: "ONGC", name: "Oil & Natural Gas Corporation Ltd", sector: "Energy" },
  { symbol: "TATASTEEL", name: "Tata Steel Ltd", sector: "Metals" },
  { symbol: "POWERGRID", name: "Power Grid Corporation of India Ltd", sector: "Power" },
  { symbol: "M&M", name: "Mahindra & Mahindra Ltd", sector: "Automobile" },
  { symbol: "WIPRO", name: "Wipro Ltd", sector: "IT" },
  { symbol: "ULTRACEMCO", name: "UltraTech Cement Ltd", sector: "Cement" },
  { symbol: "JSWSTEEL", name: "JSW Steel Ltd", sector: "Metals" },
  { symbol: "BAJAJFINSV", name: "Bajaj Finserv Ltd", sector: "NBFC" },
  { symbol: "NESTLEIND", name: "Nestle India Ltd", sector: "FMCG" },
  { symbol: "HINDUNILVR", name: "Hindustan Unilever Ltd", sector: "FMCG" },
  { symbol: "COALINDIA", name: "Coal India Ltd", sector: "Mining" },
  { symbol: "TECHM", name: "Tech Mahindra Ltd", sector: "IT" },
  { symbol: "GRASIM", name: "Grasim Industries Ltd", sector: "Cement" },
  { symbol: "INDUSINDBK", name: "IndusInd Bank Ltd", sector: "Banking" },
  { symbol: "DRREDDY", name: "Dr Reddy's Laboratories Ltd", sector: "Pharma" },
  { symbol: "CIPLA", name: "Cipla Ltd", sector: "Pharma" },
  { symbol: "ADANIPORTS", name: "Adani Ports & Special Economic Zone Ltd", sector: "Infrastructure" },
  { symbol: "DIVISLAB", name: "Divi's Laboratories Ltd", sector: "Pharma" },
  { symbol: "BPCL", name: "Bharat Petroleum Corporation Ltd", sector: "Energy" },
  { symbol: "BRITANNIA", name: "Britannia Industries Ltd", sector: "FMCG" },
  { symbol: "EICHERMOT", name: "Eicher Motors Ltd", sector: "Automobile" },
  { symbol: "APOLLOHOSP", name: "Apollo Hospitals Enterprise Ltd", sector: "Healthcare" },
  { symbol: "HEROMOTOCO", name: "Hero MotoCorp Ltd", sector: "Automobile" },
  { symbol: "SBILIFE", name: "SBI Life Insurance Company Ltd", sector: "Insurance" },
  { symbol: "HDFCLIFE", name: "HDFC Life Insurance Company Ltd", sector: "Insurance" },
  { symbol: "TRENT", name: "Trent Ltd", sector: "Retail" },
  { symbol: "BAJAJ-AUTO", name: "Bajaj Auto Ltd", sector: "Automobile" },
  { symbol: "HINDALCO", name: "Hindalco Industries Ltd", sector: "Metals" },
  { symbol: "SHRIRAMFIN", name: "Shriram Finance Ltd", sector: "NBFC" },
  { symbol: "BEL", name: "Bharat Electronics Ltd", sector: "Defence" },

  // ── Nifty Next 50 / Popular Large-caps ────────────────────────────
  { symbol: "ADANIGREEN", name: "Adani Green Energy Ltd", sector: "Power" },
  { symbol: "ADANIPOWER", name: "Adani Power Ltd", sector: "Power" },
  { symbol: "AMBUJACEM", name: "Ambuja Cements Ltd", sector: "Cement" },
  { symbol: "ATGL", name: "Adani Total Gas Ltd", sector: "Gas" },
  { symbol: "AWL", name: "Adani Wilmar Ltd", sector: "FMCG" },
  { symbol: "BANKBARODA", name: "Bank of Baroda", sector: "Banking" },
  { symbol: "BERGEPAINT", name: "Berger Paints India Ltd", sector: "Paints" },
  { symbol: "BOSCHLTD", name: "Bosch Ltd", sector: "Automobile" },
  { symbol: "CANBK", name: "Canara Bank", sector: "Banking" },
  { symbol: "CHOLAFIN", name: "Cholamandalam Investment & Finance Co Ltd", sector: "NBFC" },
  { symbol: "COLPAL", name: "Colgate-Palmolive India Ltd", sector: "FMCG" },
  { symbol: "DABUR", name: "Dabur India Ltd", sector: "FMCG" },
  { symbol: "DLF", name: "DLF Ltd", sector: "Real Estate" },
  { symbol: "GAIL", name: "GAIL (India) Ltd", sector: "Gas" },
  { symbol: "GODREJCP", name: "Godrej Consumer Products Ltd", sector: "FMCG" },
  { symbol: "HAL", name: "Hindustan Aeronautics Ltd", sector: "Defence" },
  { symbol: "HAVELLS", name: "Havells India Ltd", sector: "Electricals" },
  { symbol: "ICICIPRULI", name: "ICICI Prudential Life Insurance Co Ltd", sector: "Insurance" },
  { symbol: "ICICIGI", name: "ICICI Lombard General Insurance Co Ltd", sector: "Insurance" },
  { symbol: "INDIGO", name: "InterGlobe Aviation Ltd", sector: "Aviation" },
  { symbol: "IOC", name: "Indian Oil Corporation Ltd", sector: "Energy" },
  { symbol: "IRCTC", name: "Indian Railway Catering & Tourism Corp Ltd", sector: "Tourism" },
  { symbol: "JINDALSTEL", name: "Jindal Steel & Power Ltd", sector: "Metals" },
  { symbol: "LICI", name: "Life Insurance Corporation of India", sector: "Insurance" },
  { symbol: "LTIM", name: "LTIMindtree Ltd", sector: "IT" },
  { symbol: "LUPIN", name: "Lupin Ltd", sector: "Pharma" },
  { symbol: "MARICO", name: "Marico Ltd", sector: "FMCG" },
  { symbol: "MCDOWELL-N", name: "United Spirits Ltd", sector: "Beverages" },
  { symbol: "MUTHOOTFIN", name: "Muthoot Finance Ltd", sector: "NBFC" },
  { symbol: "NAUKRI", name: "Info Edge (India) Ltd", sector: "Internet" },
  { symbol: "NHPC", name: "NHPC Ltd", sector: "Power" },
  { symbol: "NMDC", name: "NMDC Ltd", sector: "Mining" },
  { symbol: "OBEROIRLTY", name: "Oberoi Realty Ltd", sector: "Real Estate" },
  { symbol: "OFSS", name: "Oracle Financial Services Software Ltd", sector: "IT" },
  { symbol: "PAGEIND", name: "Page Industries Ltd", sector: "Textiles" },
  { symbol: "PEL", name: "Piramal Enterprises Ltd", sector: "Diversified" },
  { symbol: "PERSISTENT", name: "Persistent Systems Ltd", sector: "IT" },
  { symbol: "PIDILITIND", name: "Pidilite Industries Ltd", sector: "Chemicals" },
  { symbol: "PNB", name: "Punjab National Bank", sector: "Banking" },
  { symbol: "POLYCAB", name: "Polycab India Ltd", sector: "Electricals" },
  { symbol: "RECLTD", name: "REC Ltd", sector: "NBFC" },
  { symbol: "SAIL", name: "Steel Authority of India Ltd", sector: "Metals" },
  { symbol: "SIEMENS", name: "Siemens Ltd", sector: "Engineering" },
  { symbol: "SRF", name: "SRF Ltd", sector: "Chemicals" },
  { symbol: "TATACONSUM", name: "Tata Consumer Products Ltd", sector: "FMCG" },
  { symbol: "TATAPOWER", name: "Tata Power Company Ltd", sector: "Power" },
  { symbol: "TORNTPHARM", name: "Torrent Pharmaceuticals Ltd", sector: "Pharma" },
  { symbol: "TVSMOTOR", name: "TVS Motor Company Ltd", sector: "Automobile" },
  { symbol: "UPL", name: "UPL Ltd", sector: "Chemicals" },
  { symbol: "VEDL", name: "Vedanta Ltd", sector: "Metals" },
  { symbol: "VOLTAS", name: "Voltas Ltd", sector: "Consumer Durables" },
  { symbol: "ZOMATO", name: "Zomato Ltd", sector: "Internet" },
  { symbol: "PAYTM", name: "One 97 Communications Ltd", sector: "Fintech" },

  // ── Popular Mid-caps ──────────────────────────────────────────────
  { symbol: "ABB", name: "ABB India Ltd", sector: "Engineering" },
  { symbol: "ABCAPITAL", name: "Aditya Birla Capital Ltd", sector: "NBFC" },
  { symbol: "ACC", name: "ACC Ltd", sector: "Cement" },
  { symbol: "ALKEM", name: "Alkem Laboratories Ltd", sector: "Pharma" },
  { symbol: "AUROPHARMA", name: "Aurobindo Pharma Ltd", sector: "Pharma" },
  { symbol: "ASHOKLEY", name: "Ashok Leyland Ltd", sector: "Automobile" },
  { symbol: "ASTRAL", name: "Astral Ltd", sector: "Pipes" },
  { symbol: "ATUL", name: "Atul Ltd", sector: "Chemicals" },
  { symbol: "BALKRISIND", name: "Balkrishna Industries Ltd", sector: "Tyres" },
  { symbol: "BANDHANBNK", name: "Bandhan Bank Ltd", sector: "Banking" },
  { symbol: "BATAINDIA", name: "Bata India Ltd", sector: "Footwear" },
  { symbol: "BHEL", name: "Bharat Heavy Electricals Ltd", sector: "Engineering" },
  { symbol: "BIOCON", name: "Biocon Ltd", sector: "Pharma" },
  { symbol: "CANFINHOME", name: "Can Fin Homes Ltd", sector: "Housing Finance" },
  { symbol: "CONCOR", name: "Container Corporation of India Ltd", sector: "Logistics" },
  { symbol: "COFORGE", name: "Coforge Ltd", sector: "IT" },
  { symbol: "CROMPTON", name: "Crompton Greaves Consumer Electricals Ltd", sector: "Electricals" },
  { symbol: "CUB", name: "City Union Bank Ltd", sector: "Banking" },
  { symbol: "CUMMINSIND", name: "Cummins India Ltd", sector: "Engineering" },
  { symbol: "DEEPAKNTR", name: "Deepak Nitrite Ltd", sector: "Chemicals" },
  { symbol: "DELHIVERY", name: "Delhivery Ltd", sector: "Logistics" },
  { symbol: "DIXON", name: "Dixon Technologies India Ltd", sector: "Electronics" },
  { symbol: "EMAMILTD", name: "Emami Ltd", sector: "FMCG" },
  { symbol: "ESCORTS", name: "Escorts Kubota Ltd", sector: "Automobile" },
  { symbol: "EXIDEIND", name: "Exide Industries Ltd", sector: "Batteries" },
  { symbol: "FEDERALBNK", name: "Federal Bank Ltd", sector: "Banking" },
  { symbol: "FORTIS", name: "Fortis Healthcare Ltd", sector: "Healthcare" },
  { symbol: "GLENMARK", name: "Glenmark Pharmaceuticals Ltd", sector: "Pharma" },
  { symbol: "GMRINFRA", name: "GMR Airports Infrastructure Ltd", sector: "Infrastructure" },
  { symbol: "GODREJPROP", name: "Godrej Properties Ltd", sector: "Real Estate" },
  { symbol: "GRANULES", name: "Granules India Ltd", sector: "Pharma" },
  { symbol: "GSPL", name: "Gujarat State Petronet Ltd", sector: "Gas" },
  { symbol: "GUJGASLTD", name: "Gujarat Gas Ltd", sector: "Gas" },
  { symbol: "HDFCAMC", name: "HDFC Asset Management Company Ltd", sector: "AMC" },
  { symbol: "HINDPETRO", name: "Hindustan Petroleum Corporation Ltd", sector: "Energy" },
  { symbol: "IDFCFIRSTB", name: "IDFC First Bank Ltd", sector: "Banking" },
  { symbol: "IEX", name: "Indian Energy Exchange Ltd", sector: "Exchange" },
  { symbol: "INDIANB", name: "Indian Bank", sector: "Banking" },
  { symbol: "INDUSTOWER", name: "Indus Towers Ltd", sector: "Telecom" },
  { symbol: "IRFC", name: "Indian Railway Finance Corporation Ltd", sector: "NBFC" },
  { symbol: "IPCALAB", name: "IPCA Laboratories Ltd", sector: "Pharma" },
  { symbol: "JUBLFOOD", name: "Jubilant FoodWorks Ltd", sector: "QSR" },
  { symbol: "LAURUSLABS", name: "Laurus Labs Ltd", sector: "Pharma" },
  { symbol: "L&TFH", name: "L&T Finance Ltd", sector: "NBFC" },
  { symbol: "LICHSGFIN", name: "LIC Housing Finance Ltd", sector: "Housing Finance" },
  { symbol: "MANAPPURAM", name: "Manappuram Finance Ltd", sector: "NBFC" },
  { symbol: "MFSL", name: "Max Financial Services Ltd", sector: "Insurance" },
  { symbol: "MGL", name: "Mahanagar Gas Ltd", sector: "Gas" },
  { symbol: "METROPOLIS", name: "Metropolis Healthcare Ltd", sector: "Healthcare" },
  { symbol: "MPHASIS", name: "MphasiS Ltd", sector: "IT" },
  { symbol: "MRF", name: "MRF Ltd", sector: "Tyres" },
  { symbol: "NAM-INDIA", name: "Nippon Life India Asset Management Ltd", sector: "AMC" },
  { symbol: "NATIONALUM", name: "National Aluminium Company Ltd", sector: "Metals" },
  { symbol: "NIACL", name: "New India Assurance Company Ltd", sector: "Insurance" },
  { symbol: "PETRONET", name: "Petronet LNG Ltd", sector: "Gas" },
  { symbol: "PFC", name: "Power Finance Corporation Ltd", sector: "NBFC" },
  { symbol: "PIIND", name: "PI Industries Ltd", sector: "Chemicals" },
  { symbol: "PRESTIGE", name: "Prestige Estates Projects Ltd", sector: "Real Estate" },
  { symbol: "PVRINOX", name: "PVR INOX Ltd", sector: "Entertainment" },
  { symbol: "RAMCOCEM", name: "The Ramco Cements Ltd", sector: "Cement" },
  { symbol: "RBLBANK", name: "RBL Bank Ltd", sector: "Banking" },
  { symbol: "SBICARD", name: "SBI Cards & Payment Services Ltd", sector: "NBFC" },
  { symbol: "SHREECEM", name: "Shree Cement Ltd", sector: "Cement" },
  { symbol: "STARHEALTH", name: "Star Health & Allied Insurance Co Ltd", sector: "Insurance" },
  { symbol: "SUNTV", name: "Sun TV Network Ltd", sector: "Media" },
  { symbol: "SUPREMEIND", name: "Supreme Industries Ltd", sector: "Plastics" },
  { symbol: "SYNGENE", name: "Syngene International Ltd", sector: "Pharma" },
  { symbol: "TATACHEM", name: "Tata Chemicals Ltd", sector: "Chemicals" },
  { symbol: "TATACOMM", name: "Tata Communications Ltd", sector: "Telecom" },
  { symbol: "TATAELXSI", name: "Tata Elxsi Ltd", sector: "IT" },
  { symbol: "THERMAX", name: "Thermax Ltd", sector: "Engineering" },
  { symbol: "TORNTPOWER", name: "Torrent Power Ltd", sector: "Power" },
  { symbol: "TTML", name: "Tata Teleservices Maharashtra Ltd", sector: "Telecom" },
  { symbol: "UNIONBANK", name: "Union Bank of India", sector: "Banking" },
  { symbol: "UBL", name: "United Breweries Ltd", sector: "Beverages" },
  { symbol: "WHIRLPOOL", name: "Whirlpool of India Ltd", sector: "Consumer Durables" },
  { symbol: "ZEEL", name: "Zee Entertainment Enterprises Ltd", sector: "Media" },
  { symbol: "ZYDUSLIFE", name: "Zydus Lifesciences Ltd", sector: "Pharma" },
  { symbol: "IDEA", name: "Vodafone Idea Ltd", sector: "Telecom" },
  { symbol: "YESBANK", name: "Yes Bank Ltd", sector: "Banking" },
  { symbol: "MOTHERSON", name: "Samvardhana Motherson International Ltd", sector: "Auto Ancillary" },
  { symbol: "MAXHEALTH", name: "Max Healthcare Institute Ltd", sector: "Healthcare" },
  { symbol: "PHOENIXLTD", name: "The Phoenix Mills Ltd", sector: "Real Estate" },
  { symbol: "SOLARINDS", name: "Solar Industries India Ltd", sector: "Chemicals" },
  { symbol: "SONACOMS", name: "Sona BLW Precision Forgings Ltd", sector: "Auto Ancillary" },
  { symbol: "SUPREMEIND", name: "Supreme Industries Ltd", sector: "Plastics" },
  { symbol: "KALYANKJIL", name: "Kalyan Jewellers India Ltd", sector: "Jewellery" },
  { symbol: "DMART", name: "Avenue Supermarts Ltd", sector: "Retail" },
  { symbol: "NYKAA", name: "FSN E-Commerce Ventures Ltd", sector: "E-Commerce" },
  { symbol: "POLICYBZR", name: "PB Fintech Ltd", sector: "Fintech" },
  { symbol: "JIOFIN", name: "Jio Financial Services Ltd", sector: "NBFC" },
  { symbol: "MANKIND", name: "Mankind Pharma Ltd", sector: "Pharma" },
  { symbol: "LTTS", name: "L&T Technology Services Ltd", sector: "IT" },
  { symbol: "LODHA", name: "Macrotech Developers Ltd", sector: "Real Estate" },
  { symbol: "MAZDOCK", name: "Mazagon Dock Shipbuilders Ltd", sector: "Defence" },
  { symbol: "COCHINSHIP", name: "Cochin Shipyard Ltd", sector: "Defence" },
  { symbol: "RVNL", name: "Rail Vikas Nigam Ltd", sector: "Infrastructure" },
  { symbol: "IREDA", name: "Indian Renewable Energy Development Agency Ltd", sector: "NBFC" },
  { symbol: "SUZLON", name: "Suzlon Energy Ltd", sector: "Power" },
  { symbol: "CAMS", name: "Computer Age Management Services Ltd", sector: "AMC" },
  { symbol: "CDSL", name: "Central Depository Services Ltd", sector: "Exchange" },
  { symbol: "BSE", name: "BSE Ltd", sector: "Exchange" },
  { symbol: "MCX", name: "Multi Commodity Exchange of India Ltd", sector: "Exchange" },
];

/**
 * Search stocks locally by matching symbol or name against query.
 * Returns up to `limit` results. Matching is case-insensitive.
 * Symbol-prefix matches rank higher than name-contains matches.
 */
export function searchLocalStocks(query: string, limit = 10): NseStock[] {
  if (!query || query.length < 1) return [];
  const q = query.toUpperCase().trim();

  // Score: symbol starts with query → 3, symbol contains → 2, name contains → 1
  const scored: { stock: NseStock; score: number }[] = [];

  for (const stock of NSE_STOCKS) {
    const sym = stock.symbol.toUpperCase();
    const name = stock.name.toUpperCase();
    if (sym.startsWith(q)) {
      scored.push({ stock, score: 3 });
    } else if (sym.includes(q)) {
      scored.push({ stock, score: 2 });
    } else if (name.includes(q)) {
      scored.push({ stock, score: 1 });
    }
  }

  // Sort by score desc, then alphabetically by symbol
  scored.sort((a, b) => b.score - a.score || a.stock.symbol.localeCompare(b.stock.symbol));

  // Dedupe by symbol
  const seen = new Set<string>();
  const results: NseStock[] = [];
  for (const { stock } of scored) {
    if (seen.has(stock.symbol)) continue;
    seen.add(stock.symbol);
    results.push(stock);
    if (results.length >= limit) break;
  }

  return results;
}
