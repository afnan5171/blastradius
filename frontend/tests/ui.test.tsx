import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Page from "@/app/page";
import { AccountForm, ConnectionForm } from "@/components/Forms";
import { api, Account } from "@/lib/types";
vi.mock("@/components/IdentityMap", () => ({
  default: () => <div aria-label="Interactive account map" />,
}));
vi.mock("@/lib/types", async (original) => ({
  ...(await original<typeof import("@/lib/types")>()),
  api: vi.fn(),
}));
const gmail: Account = {
  id: "a",
  user_id: "u",
  service_name: "Gmail",
  category: "Email",
  email_or_username: "test@example.com",
  importance: "Critical",
  has_mfa: false,
  mfa_type: "None",
  has_passkey: false,
  recovery_email: "",
  recovery_phone: "",
  notes: "",
};
const bank = { ...gmail, id: "b", service_name: "Bank", category: "Financial" };
beforeEach(() => {
  vi.mocked(api).mockReset();
  vi.mocked(api).mockImplementation(async (path) => {
    const responses: Record<string, unknown> = {
      "/auth/me": { id: "u" },
      "/accounts": [gmail, bank],
      "/relationships": [],
      "/risk-scores": [
        {
          account_id: "a",
          score: 60,
          level: "Elevated",
          dependent_accounts: 1,
        },
      ],
      "/security-chokepoints": [],
      "/circular-dependencies": [],
      "/recommendations/a": [],
      "/simulate/a": {
        source_account_id: "a",
        affected_count: 1,
        high_value_count: 1,
        directly_reachable: ["b"],
        indirectly_reachable: [],
        score: 60,
        level: "Elevated",
        paths: [
          {
            target_account_id: "b",
            account_ids: ["a", "b"],
            relationship_ids: ["r"],
            relationship_types: ["PASSWORD_RESET"],
            direct: true,
          },
        ],
        recommendations: [
          {
            kind: "passkey",
            account_id: "a",
            title: "Enable a passkey on Gmail",
            detail: "Protect your email",
            priority: 80,
          },
        ],
      },
    };
    return responses[path] as never;
  });
});
describe("critical UI behavior", () => {
  it("runs a selected-account simulation and clears the result", async () => {
    render(<Page />);
    await screen.findByRole("button", { name: "Simulate Compromise" });
    fireEvent.click(
      screen.getByRole("button", { name: "Simulate Compromise" }),
    );
    await screen.findByRole("heading", { name: "If Gmail is compromised" });
    expect(api).toHaveBeenCalledWith("/simulate/a", "POST");
    expect(screen.getByText("Password reset")).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "Enable a passkey on Gmail" }),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Reset view" }));
    expect(
      screen.queryByRole("heading", { name: "If Gmail is compromised" }),
    ).toBeNull();
  });
  it("submits account metadata and MFA settings without password fields", async () => {
    const done = vi.fn();
    render(<AccountForm onDone={done} onClose={() => {}} />);
    fireEvent.change(screen.getByLabelText("Service name"), {
      target: { value: "New account" },
    });
    fireEvent.click(screen.getByLabelText("MFA enabled"));
    fireEvent.change(screen.getByLabelText("MFA type"), {
      target: { value: "Authenticator" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save account" }));
    await waitFor(() => expect(done).toHaveBeenCalled());
    expect(api).toHaveBeenCalledWith(
      "/accounts",
      "POST",
      expect.objectContaining({
        service_name: "New account",
        has_mfa: true,
        mfa_type: "Authenticator",
      }),
    );
    expect(screen.queryByLabelText(/^Password$/)).toBeNull();
  });
  it("preserves connection direction and rejects self connections in the UI", async () => {
    const done = vi.fn();
    render(
      <ConnectionForm
        accounts={[gmail, bank]}
        selected="a"
        onDone={done}
        onClose={() => {}}
      />,
    );
    fireEvent.change(
      screen.getByLabelText("To — account potentially affected"),
      { target: { value: "a" } },
    );
    expect(
      (
        screen.getByRole("button", {
          name: "Save connection",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    fireEvent.change(
      screen.getByLabelText("To — account potentially affected"),
      { target: { value: "b" } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Save connection" }));
    await waitFor(() => expect(done).toHaveBeenCalled());
    expect(api).toHaveBeenCalledWith(
      "/relationships",
      "POST",
      expect.objectContaining({
        source_account_id: "a",
        target_account_id: "b",
      }),
    );
  });
  it("shows API failures without claiming a successful save", async () => {
    vi.mocked(api).mockRejectedValue(new Error("Connection failed"));
    const done = vi.fn();
    render(<AccountForm onDone={done} onClose={() => {}} />);
    fireEvent.change(screen.getByLabelText("Service name"), {
      target: { value: "Example" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save account" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(done).not.toHaveBeenCalled();
  });
});
