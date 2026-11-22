import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { SERVER_WAKING_EVENT } from "../api/client";

/** Shown while API requests are waiting for a sleeping backend to start. */
export function ServerWakeBanner() {
  const [waking, setWaking] = useState(false);

  useEffect(() => {
    const onChange = (e: Event) => setWaking((e as CustomEvent<boolean>).detail);
    window.addEventListener(SERVER_WAKING_EVENT, onChange);
    return () => window.removeEventListener(SERVER_WAKING_EVENT, onChange);
  }, []);

  if (!waking) return null;
  return (
    <div
      role="status"
      className="fixed inset-x-4 top-4 z-50 mx-auto flex max-w-md items-center gap-3 rounded-2xl border border-fix/30 bg-fix-soft px-5 py-3 shadow-lift"
    >
      <Loader2 className="h-4 w-4 shrink-0 animate-spin text-fix" aria-hidden="true" />
      <p className="text-sm text-ink">
        <span className="font-semibold">Starting the server…</span>{" "}
        <span className="text-ink-2">This can take up to a minute. Your request will go through on its own.</span>
      </p>
    </div>
  );
}
