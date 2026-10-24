"use client";
import { useEffect, useRef, useState } from "react";
import { X, ArrowRight } from "lucide-react";
import { Account, api, categories, label, relationTypes } from "@/lib/types";
export function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog ref={ref} onCancel={onClose} aria-label={title}>
      <header>
        <h2>{title}</h2>
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Close dialog"
        >
          <X size={20} />
        </button>
      </header>
      {children}
    </dialog>
  );
}
const empty = {
  service_name: "",
  category: "Email",
  email_or_username: "",
  importance: "Medium",
  has_mfa: false,
  mfa_type: "None",
  has_passkey: false,
  recovery_email: "",
  recovery_phone: "",
  notes: "",
};
export function AccountForm({
  account,
  onDone,
  onClose,
}: {
  account?: Account;
  onDone: () => void;
  onClose: () => void;
}) {
  const [form, setForm] = useState(
    account
      ? (Object.fromEntries(
          Object.keys(empty).map((k) => [k, account[k as keyof Account]]),
        ) as typeof empty)
      : empty,
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k: string, v: string | boolean) =>
    setForm((f) => ({ ...f, [k]: v }));
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(
        account ? `/accounts/${account.id}` : "/accounts",
        account ? "PUT" : "POST",
        form,
      );
      onDone();
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }
  return (
    <Modal
      title={account ? "Edit account" : "Add an account"}
      onClose={onClose}
    >
      <form onSubmit={submit}>
        <p className="form-intro">
          Add the details you know. Never enter passwords or recovery codes.
        </p>
        <div className="form-grid">
          <label className="full">
            Service name
            <input
              autoFocus
              required
              maxLength={100}
              value={form.service_name}
              onChange={(e) => set("service_name", e.target.value)}
              placeholder="e.g. Gmail"
            />
          </label>
          <label>
            Category
            <select
              value={form.category}
              onChange={(e) => set("category", e.target.value)}
            >
              {categories.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label>
            Importance
            <select
              value={form.importance}
              onChange={(e) => set("importance", e.target.value)}
            >
              {["Low", "Medium", "High", "Critical"].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label className="full">
            Email / username
            <input
              maxLength={254}
              value={form.email_or_username}
              onChange={(e) => set("email_or_username", e.target.value)}
              placeholder="Optional"
            />
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={form.has_mfa}
              onChange={(e) => set("has_mfa", e.target.checked)}
            />{" "}
            MFA enabled
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={form.has_passkey}
              onChange={(e) => set("has_passkey", e.target.checked)}
            />{" "}
            Passkey enabled
          </label>
          {form.has_mfa && (
            <label className="full">
              MFA type
              <select
                value={form.mfa_type}
                onChange={(e) => set("mfa_type", e.target.value)}
              >
                {[
                  "None",
                  "Authenticator",
                  "SMS",
                  "Security key",
                  "Email",
                  "Other",
                ].map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            </label>
          )}
          <label>
            Recovery email
            <input
              maxLength={254}
              value={form.recovery_email}
              onChange={(e) => set("recovery_email", e.target.value)}
            />
          </label>
          <label>
            Recovery phone
            <input
              maxLength={40}
              value={form.recovery_phone}
              onChange={(e) => set("recovery_phone", e.target.value)}
            />
          </label>
          <label className="full">
            Notes
            <textarea
              maxLength={2000}
              value={form.notes}
              onChange={(e) => set("notes", e.target.value)}
              placeholder="Relationship metadata only — no secrets"
            />
          </label>
        </div>
        <p className="form-intro">
          After saving, use “Add connection” to map which other accounts this
          one can reach. Recovery contact text alone does not create a graph
          connection.
        </p>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <footer>
          <button type="button" className="secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="primary" disabled={busy}>
            {busy ? "Saving…" : "Save account"}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
export function ConnectionForm({
  accounts,
  selected,
  onClose,
  onDone,
}: {
  accounts: Account[];
  selected: string | null;
  onClose: () => void;
  onDone: () => void;
}) {
  const [source, setSource] = useState(selected || accounts[0]?.id || "");
  const [target, setTarget] = useState(
    accounts.find((a) => a.id !== (selected || accounts[0]?.id))?.id || "",
  );
  const [kind, setKind] = useState("PASSWORD_RESET");
  const [weight, setWeight] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api("/relationships", "POST", {
        source_account_id: source,
        target_account_id: target,
        relationship_type: kind,
        risk_weight: weight ? Number(weight) : null,
        notes,
      });
      onDone();
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }
  return (
    <Modal title="Connect two accounts" onClose={onClose}>
      <form onSubmit={submit}>
        <p className="form-intro">
          If the first account is compromised, an attacker may be able to reach
          the second.
        </p>
        <div className="form-grid">
          <label className="full">
            From — account that grants access
            <select value={source} onChange={(e) => setSource(e.target.value)}>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.service_name}
                </option>
              ))}
            </select>
          </label>
          <div className="direction full">
            <ArrowRight size={18} /> could provide access to
          </div>
          <label className="full">
            To — account potentially affected
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.service_name}
                </option>
              ))}
            </select>
          </label>
          <label className="full">
            How are they connected?
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              {relationTypes.map((t) => (
                <option value={t} key={t}>
                  {label(t)}
                </option>
              ))}
            </select>
          </label>
          <label className="full">
            Risk weight (optional, 1–10)
            <input
              type="number"
              min={1}
              max={10}
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              placeholder="Use the recommended weight"
            />
          </label>
          <label className="full">
            Notes
            <textarea
              maxLength={2000}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>
        </div>
        {source === target && (
          <p className="error">Choose two different accounts.</p>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <footer>
          <button type="button" className="secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="primary"
            disabled={busy || source === target || !target}
          >
            {busy ? "Saving…" : "Save connection"}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
