import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchProducts, getDemoProduct, type ProductCard } from "../lib/shopify";

export function Product() {
  const { handle } = useParams();
  const [product, setProduct] = useState<ProductCard | null>(null);

  useEffect(() => {
    if (!handle) return;
    const demo = getDemoProduct(handle);
    if (demo) {
      setProduct(demo);
      return;
    }
    fetchProducts(50).then((list) => setProduct(list.find((p) => p.handle === handle) || null));
  }, [handle]);

  if (!product) {
    return (
      <p>
        Product not found. <Link to="/">Back</Link>
      </p>
    );
  }

  return (
    <article className="pdp">
      <Link to="/" className="muted">
        ← Shop
      </Link>
      <h1>{product.title}</h1>
      <p className="price">
        {product.currency} {product.price}
      </p>
      <p>{product.description}</p>
      <button
        className="cta"
        type="button"
        onClick={() => alert("Checkout wires to Shopify Cart AJAX / Hydrogen cart once Storefront API is live.")}
      >
        Add to cart (scaffold)
      </button>
    </article>
  );
}
