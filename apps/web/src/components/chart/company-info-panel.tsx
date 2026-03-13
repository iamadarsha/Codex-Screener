"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, ExternalLink, Building2, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchCompanyInfo } from "@/lib/api";
import { cn } from "@/lib/cn";

// Fallback company descriptions for major stocks when API is unavailable
const FALLBACK_INFO: Record<string, { title: string; description: string; extract: string }> = {
  RELIANCE: {
    title: "Reliance Industries",
    description: "Indian multinational conglomerate",
    extract: "Reliance Industries Limited is an Indian multinational conglomerate headquartered in Mumbai. It has diverse businesses including energy, petrochemicals, natural gas, retail, telecommunications, mass media, and textiles. Reliance is one of the most profitable companies in India and the largest publicly traded company in India by market capitalization.",
  },
  TCS: {
    title: "Tata Consultancy Services",
    description: "Indian multinational IT services and consulting company",
    extract: "Tata Consultancy Services Limited is an Indian multinational information technology services and consulting company with its headquarters in Mumbai. It is a part of the Tata Group and operates in 150 locations across 46 countries. TCS is the second-largest Indian company by market capitalization and is among the most valuable IT services brands worldwide.",
  },
  HDFCBANK: {
    title: "HDFC Bank",
    description: "Indian banking and financial services company",
    extract: "HDFC Bank Limited is an Indian banking and financial services company headquartered in Mumbai. It is India's largest private sector bank by assets and the world's tenth largest bank by market capitalisation. HDFC Bank provides a wide range of banking products and financial services including wholesale banking, retail banking, treasury operations, and digital banking.",
  },
  INFY: {
    title: "Infosys",
    description: "Indian multinational IT company",
    extract: "Infosys Limited is an Indian multinational information technology company that provides business consulting, information technology and outsourcing services. The company was founded in Pune and is headquartered in Bangalore. Infosys is the second-largest Indian IT company by revenue and one of the largest employers of H-1B visa holders in the United States.",
  },
  ICICIBANK: {
    title: "ICICI Bank",
    description: "Indian multinational bank",
    extract: "ICICI Bank Limited is an Indian multinational bank and financial services company headquartered in Mumbai with its registered office in Vadodara. It offers a wide range of banking products and financial services for corporate and retail customers through various delivery channels and specialised subsidiaries in areas of investment banking, life, non-life insurance, venture capital and asset management.",
  },
  SBIN: {
    title: "State Bank of India",
    description: "Indian multinational public sector bank",
    extract: "State Bank of India is an Indian multinational public sector bank and financial services statutory body headquartered in Mumbai. SBI is the 43rd largest bank in the world and ranked 221st in the Fortune Global 500 list of the world's biggest corporations of 2020. It is the largest bank in India with a 23% market share by assets and a 25% share of the total loan and deposits market.",
  },
  TATAMOTORS: {
    title: "Tata Motors",
    description: "Indian multinational automotive company",
    extract: "Tata Motors Limited is an Indian multinational automotive manufacturing company, headquartered in Mumbai. It is a part of the Tata Group. Its products include passenger cars, trucks, vans, coaches, buses, luxury cars, sports cars, and military vehicles. Tata Motors owns Jaguar Land Rover, the British premium automaker.",
  },
  BHARTIARTL: {
    title: "Bharti Airtel",
    description: "Indian multinational telecommunications company",
    extract: "Bharti Airtel Limited, also known as Airtel, is an Indian multinational telecommunications services company headquartered in New Delhi. It operates in 18 countries across South Asia and Africa. Airtel provides 4G/5G wireless services, fixed line broadband, DTH television and enterprise solutions. It is the second largest mobile network operator in India and the third largest in the world.",
  },
};

interface CompanyInfoPanelProps {
  symbol: string;
}

export function CompanyInfoPanel({ symbol }: CompanyInfoPanelProps) {
  const [expanded, setExpanded] = useState(true);

  const { data: info, isLoading } = useQuery({
    queryKey: ["companyInfo", symbol],
    queryFn: () => fetchCompanyInfo(symbol),
    staleTime: 60_000 * 60, // 1 hour
    retry: 1,
  });

  // Use API data, fallback to local data, or show placeholder
  const fallback = FALLBACK_INFO[symbol];
  const title = info?.title || fallback?.title || symbol;
  const description = info?.description || fallback?.description || "";
  const extract = info?.extract || fallback?.extract || "";
  const thumbnail = info?.thumbnail;
  const wikiUrl = info?.url || "";
  const hasContent = extract && extract !== "Company information not available at the moment.";

  return (
    <div className="rounded-panel border border-border bg-card overflow-hidden">
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-5 py-3.5 text-left transition hover:bg-elevated/50"
      >
        <div className="flex items-center gap-2.5">
          <Building2 className="h-4 w-4 text-accent" />
          <span className="text-sm font-semibold text-text-primary">About {title}</span>
          {description && (
            <span className="hidden sm:inline text-xs text-text-muted">
              — {description}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin text-text-muted" />}
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-text-muted" />
          ) : (
            <ChevronDown className="h-4 w-4 text-text-muted" />
          )}
        </div>
      </button>

      {/* Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="border-t border-border px-5 py-4">
              {hasContent ? (
                <div className="flex gap-4">
                  {/* Thumbnail */}
                  {thumbnail && (
                    <div className="hidden sm:block shrink-0">
                      <img
                        src={thumbnail}
                        alt={title}
                        className="h-16 w-16 rounded-lg object-contain bg-elevated p-1"
                      />
                    </div>
                  )}
                  {/* Text */}
                  <div className="min-w-0 flex-1 space-y-2.5">
                    <p className="text-xs leading-relaxed text-text-secondary line-clamp-4 sm:line-clamp-none">
                      {extract}
                    </p>
                    {wikiUrl && (
                      <a
                        href={wikiUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[11px] text-accent hover:underline"
                      >
                        Read more on Wikipedia
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-xs text-text-muted">
                  {isLoading ? "Loading company information..." : "Company information not available."}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
