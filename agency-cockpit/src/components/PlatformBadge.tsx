import { useEffect, useState } from "react";
import { detectShell, getNativePlatformInfo, type AppShell } from "../lib/platform";

/** Small status chip showing web / desktop / mobile shell. */
export function PlatformBadge() {
  const [shell, setShell] = useState<AppShell>("web");
  const [native, setNative] = useState<string>("");

  useEffect(() => {
    setShell(detectShell());
    getNativePlatformInfo().then((info) => {
      if (info?.os) setNative(String(info.os));
    });
  }, []);

  const label =
    shell === "web" ? "Web PWA" :
    shell === "tauri-mobile" ? `Mobile · ${native || "Tauri"}` :
    `Desktop · ${native || "Tauri"}`;

  return (
    <span className="pill" title="Packaging target">
      <strong>{label}</strong>
    </span>
  );
}
