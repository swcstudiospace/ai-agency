import React from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import Heading from "@theme/Heading";

const features = [
  {
    title: "Discover",
    body: "Parallel Search + Task ultra/pro ranks niches into GO / TEST / NO-GO with unit economics.",
  },
  {
    title: "Locate",
    body: "Supplier locate finds Alibaba/CJ/wholesale leads, MOQ, landed cost — automated after rank.",
  },
  {
    title: "Build",
    body: "Brand, PromptWise/Fal UGC, Shopify drafts, listings — L2 autonomy with HITL for money.",
  },
  {
    title: "Operate",
    body: "30 agents across CX, fraud, logistics, tax, experiments. Linear SWC dual-write + GitHub.",
  },
];

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <header className="hero hero--agency">
        <div className="container text--center">
          <Heading as="h1" className="hero__title">
            AI Dropshipping Agency
          </Heading>
          <p className="hero__subtitle">
            Enterprise multi-agent control plane: Hermes orchestrates Agno AgentOS,
            Parallel research, SuperGrok brains, Shopify drafts, and HITL ads.
          </p>
          <div className="hero-pills">
            <span className="hero-pill">30 agents</span>
            <span className="hero-pill">12 teams</span>
            <span className="hero-pill">11 workflows</span>
            <span className="hero-pill">Linear SWC</span>
            <span className="hero-pill">Shopify · PromptWise</span>
          </div>
          <div>
            <Link className="button button--lg button--agency" to="/docs/getting-started/quickstart">
              Quick start
            </Link>
            <Link
              className="button button--lg button--outline button--secondary margin-left--sm"
              style={{ color: "#e2e5f5", borderColor: "rgba(255,255,255,0.25)" }}
              to="/docs/guides/product-locate"
            >
              Product locate
            </Link>
          </div>
        </div>
      </header>
      <main className="container">
        <div className="feature-grid">
          {features.map((f) => (
            <div key={f.title} className={clsx("feature-card")}>
              <Heading as="h3">{f.title}</Heading>
              <p>{f.body}</p>
            </div>
          ))}
        </div>
      </main>
    </Layout>
  );
}
