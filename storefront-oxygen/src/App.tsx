import { Link, Route, Routes } from "react-router-dom";
import { Home } from "./pages/Home";
import { Product } from "./pages/Product";
import { Cart } from "./pages/Cart";
import { getStoreConfig } from "./lib/shopify";

export default function App() {
  const cfg = getStoreConfig();
  return (
    <div className="shell">
      <header className="top">
        <Link to="/" className="brand">
          ego<span>.engineer</span>
        </Link>
        <nav>
          <Link to="/">Shop</Link>
          <Link to="/cart">Cart</Link>
          <a href={`https://${cfg.storeDomain}`} target="_blank" rel="noreferrer">
            Shopify
          </a>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products/:handle" element={<Product />} />
          <Route path="/cart" element={<Cart />} />
        </Routes>
      </main>
      <footer className="foot">
        <div>
          Headless storefront scaffold for <strong>Oxygen / Hydrogen</strong> · brand domain{" "}
          <code>{cfg.primaryDomain}</code>
        </div>
        <div className="muted">
          Set PUBLIC_STOREFRONT_API_TOKEN to load live catalog. Until then demo products render.
        </div>
      </footer>
    </div>
  );
}
