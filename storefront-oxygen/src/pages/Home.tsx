import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProducts, type ProductCard } from "../lib/shopify";

export function Home() {
  const [products, setProducts] = useState<ProductCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <div className="hero">
        <p className="eyebrow">ego.engineer · headless commerce</p>
        <h1>Engineered goods for high-output humans</h1>
        <p className="lede">
          Shopify Hydrogen/Oxygen-ready storefront scaffold. Wired for the AI Dropshipping Agency
          catalog — demo products until Storefront API token is set.
        </p>
      </div>
      {loading ? (
        <p className="muted">Loading catalog…</p>
      ) : (
        <div className="grid">
          {products.map((p) => (
            <article key={p.id} className="card">
              <div className="card-body">
                <div className="tags">
                  {(p.tags || []).slice(0, 3).map((t) => (
                    <span key={t}>{t}</span>
                  ))}
                </div>
                <h2>{p.title}</h2>
                <p>{p.description.slice(0, 140)}{p.description.length > 140 ? "…" : ""}</p>
                <div className="row">
                  <strong>
                    {p.currency} {p.price}
                  </strong>
                  <Link to={`/products/${p.handle}`}>View</Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
