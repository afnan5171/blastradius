export type Account = {
  id: string;
  user_id: string;
  service_name: string;
  category: string;
  email_or_username: string;
  importance: string;
  has_mfa: boolean;
  mfa_type: string;
  has_passkey: boolean;
  recovery_email: string;
  recovery_phone: string;
  notes: string;
};
export type Connection = {
  id: string;
  source_account_id: string;
  target_account_id: string;
  relationship_type: string;
  risk_weight: number;
  notes: string;
};
export type Path = {
  target_account_id: string;
  account_ids: string[];
  relationship_ids: string[];
  relationship_types: string[];
  direct: boolean;
};
export type Recommendation = {
  title: string;
  detail: string;
  priority: number;
  account_id: string;
  kind: string;
};
export type Risk = {
  account_id: string;
  score: number;
  level: string;
  dependent_accounts: number;
};
export type Simulation = {
  source_account_id: string;
  directly_reachable: string[];
  indirectly_reachable: string[];
  paths: Path[];
  affected_count: number;
  high_value_count: number;
  score: number;
  level: string;
  recommendations: Recommendation[];
};
export type Choke = {
  account_id: string;
  dependent_accounts: number;
  out_degree: number;
  centrality: number;
};
export const categories = [
  "Email",
  "Financial",
  "Social Media",
  "Cloud Storage",
  "Shopping",
  "Work",
  "School",
  "Gaming",
  "Password Manager",
  "Communication",
  "Other",
];
export const relationTypes = [
  "PASSWORD_RESET",
  "RECOVERY_EMAIL",
  "SIGN_IN_WITH_GOOGLE",
  "SIGN_IN_WITH_APPLE",
  "SIGN_IN_WITH_FACEBOOK",
  "SHARED_PASSWORD",
  "OAUTH_READ_ACCESS",
  "OAUTH_WRITE_ACCESS",
  "PHONE_RECOVERY",
  "PASSWORD_MANAGER_STORES_CREDENTIAL",
  "OTHER",
];
export const label = (v: string) =>
  v
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/^./, (c) => c.toUpperCase());
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method,
    credentials: "same-origin",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const data = await response
      .json()
      .catch(() => ({ detail: "Unable to reach the server." }));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Please check the form fields and try again.",
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
