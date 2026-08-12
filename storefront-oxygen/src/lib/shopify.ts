/** Storefront config — Hydrogen/Oxygen compatible env names. */

export type StoreConfig = {
  storeDomain: string;
  storefrontToken: string;
  apiVersion: string;
  primaryDomain: string;
  brandName: string;
  hasLiveApi: boolean;
};

export function getStoreConfig(): StoreConfig {
  const storeDomain =
    import.meta.env.PUBLIC_STORE_DOMAIN ||
    import.meta.env.VITE_PUBLIC_STORE_DOMAIN ||
    "aidropshipping.myshopify.com";
  const storefrontToken =
    import.meta.env.PUBLIC_STOREFRONT_API_TOKEN ||
    import.meta.env.VITE_PUBLIC_STOREFRONT_API_TOKEN ||
    "";
  const apiVersion =
    import.meta.env.PUBLIC_STOREFRONT_API_VERSION ||
    import.meta.env.VITE_PUBLIC_STOREFRONT_API_VERSION ||
    "2024-10";
  const primaryDomain =
    import.meta.env.PUBLIC_PRIMARY_DOMAIN ||
    import.meta.env.VITE_PUBLIC_PRIMARY_DOMAIN ||
    "ego.engineer";
  const brandName =
    import.meta.env.PUBLIC_BRAND_NAME ||
    import.meta.env.VITE_PUBLIC_BRAND_NAME ||
    "ego.engineer";
  return {
    storeDomain,
    storefrontToken,
    apiVersion,
    primaryDomain,
    brandName,
    hasLiveApi: Boolean(storefrontToken),
  };
}

export type ProductCard = {
  id: string;
  handle: string;
  title: string;
  description: string;
  price: string;
  currency: string;
  image?: string;
  tags?: string[];
};

const DEMO: ProductCard[] = [
  {
    id: "demo-laptop-stand",
    handle: "fold-flat-laptop-stand",
    title: "Fold-Flat Adjustable Aluminum Laptop Stand",
    description:
      "Travel-ready aluminum stand for remote workers. Agency GO SKU — connect Storefront API for live inventory.",
    price: "49.99",
    currency: "USD",
    tags: ["GO", "desk", "ergonomics"],
  },
  {
    id: "demo-forearm",
    handle: "clamp-on-forearm-support",
    title: "Clamp-On Rotating Forearm Support",
    description: "Desk-mounted forearm rest. TEST/GO companion SKU from product rank.",
    price: "59.99",
    currency: "USD",
    tags: ["GO", "desk"],
  },
];

const PRODUCTS_QUERY = `#graphql
  query Products($first: Int!) {
    products(first: $first) {
      nodes {
        id
        handle
        title
        description
        tags
        featuredImage { url altText }
        priceRange {
          minVariantPrice { amount currencyCode }
        }
      }
    }
  }
`;

export async function fetchProducts(first = 12): Promise<ProductCard[]> {
  const cfg = getStoreConfig();
  if (!cfg.hasLiveApi) return DEMO;

  const endpoint = `https://${cfg.storeDomain}/api/${cfg.apiVersion}/graphql.json`;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Storefront-Access-Token": cfg.storefrontToken,
    },
    body: JSON.stringify({ query: PRODUCTS_QUERY, variables: { first } }),
  });
  if (!res.ok) {
    console.warn("Storefront API error", res.status);
    return DEMO;
  }
  const json = await res.json();
  const nodes = json?.data?.products?.nodes || [];
  if (!nodes.length) return DEMO;
  return nodes.map((n: any) => ({
    id: n.id,
    handle: n.handle,
    title: n.title,
    description: n.description || "",
    price: n.priceRange?.minVariantPrice?.amount || "0",
    currency: n.priceRange?.minVariantPrice?.currencyCode || "USD",
    image: n.featuredImage?.url,
    tags: n.tags || [],
  }));
}

export function getDemoProduct(handle: string): ProductCard | undefined {
  return DEMO.find((p) => p.handle === handle);
}
