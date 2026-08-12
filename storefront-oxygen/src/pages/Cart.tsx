import { Link } from "react-router-dom";

export function Cart() {
  return (
    <section className="pdp">
      <h1>Cart</h1>
      <p className="muted">
        Scaffold only. Production Oxygen/Hydrogen uses Storefront Cart API + Checkout.
      </p>
      <Link to="/">Continue shopping</Link>
    </section>
  );
}
