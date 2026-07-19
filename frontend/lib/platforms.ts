export interface Platform {
  id: string;
  label: string;
  icon: string;
}

export const ALL_PLATFORMS: Platform[] = [
  { id: "amazon", label: "Amazon BR", icon: "🇧🇷" },
  { id: "amazon_us", label: "Amazon US", icon: "🇺🇸" },
  { id: "amazon_uk", label: "Amazon UK", icon: "🇬🇧" },
  { id: "amazon_de", label: "Amazon DE", icon: "🇩🇪" },
  { id: "mercado_livre", label: "Mercado Livre", icon: "🟡" },
  { id: "magalu", label: "Magazine Luiza", icon: "🟢" },
  { id: "americanas", label: "Americanas", icon: "🔵" },
  { id: "casas_bahia", label: "Casas Bahia", icon: "🔴" },
  { id: "shopee", label: "Shopee", icon: "🛍️" },
  { id: "enjoei", label: "Enjoei", icon: "💛" },
  { id: "locomotiva", label: "Locomotiva Discos", icon: "🚂" },
  { id: "kiwi", label: "Kiwi Discos", icon: "🥝" },
  { id: "regards", label: "Regards", icon: "🎵" },
  { id: "cdpoint", label: "CD Point", icon: "💿" },
  { id: "fonoteca", label: "Fonoteca", icon: "🎶" },
  { id: "supernova", label: "Supernova Discos", icon: "💥" },
  { id: "discol", label: "Discol", icon: "🎯" },
  { id: "music_house", label: "Music House Discos", icon: "🎼" },
  { id: "migranet", label: "Migranet", icon: "🌐" },
  { id: "umusicstore", label: "Universal Music Store", icon: "🎤" },
  { id: "loja_discos", label: "A Loja de Discos", icon: "🏪" },
];

export const PLATFORM_LABELS: Record<string, string> = Object.fromEntries(
  ALL_PLATFORMS.map((p) => [p.id, p.label]),
);

export const PLATFORM_ICONS: Record<string, string> = Object.fromEntries(
  ALL_PLATFORMS.map((p) => [p.id, p.icon]),
);

export const PLATFORM_BADGES: Record<string, string> = {
  amazon: "BR",
  amazon_us: "US",
  amazon_uk: "UK",
  amazon_de: "DE",
  mercado_livre: "ML",
  magalu: "MGL",
  americanas: "AM",
  casas_bahia: "CB",
  shopee: "SP",
  enjoei: "EN",
  locomotiva: "LO",
  kiwi: "KW",
  regards: "RG",
  cdpoint: "CP",
  fonoteca: "FN",
  supernova: "SN",
  discol: "DC",
  music_house: "MH",
  migranet: "MG",
  umusicstore: "UM",
  loja_discos: "LD",
};
