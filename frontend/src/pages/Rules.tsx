import React, { useEffect, useState } from "react";
import { Plus, CheckCircle2, AlertCircle, Edit3, Tag, History, ShieldCheck } from "lucide-react";
import { fetchRules, createRule, publishRule, ConsultationTypeRule } from "../api/rules";
import { DataTable, Column } from "../components/DataTable";
import { useAuth } from "../context/AuthContext";

export default function Rules() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [rules, setRules] = useState<ConsultationTypeRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingRule, setEditingRule] = useState<ConsultationTypeRule | null>(null);

  // Form State
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [approvedTestsInput, setApprovedTestsInput] = useState("");
  const [suggestedTestsInput, setSuggestedTestsInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadRules();
  }, []);

  async function loadRules() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchRules();
      setRules(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load rules.");
    } finally {
      setLoading(false);
    }
  }

  function handleOpenCreate() {
    setName("");
    setDescription("");
    setApprovedTestsInput("Hemoglobin, WBC Count, Platelets");
    setSuggestedTestsInput("Serum Creatinine, Fasting Glucose");
    setEditingRule(null);
    setShowCreateModal(true);
  }

  function handleOpenEdit(rule: ConsultationTypeRule) {
    setEditingRule(rule);
    setName(rule.name);
    setDescription(rule.description || "");
    setApprovedTestsInput(rule.approved_test_names.join(", "));
    setSuggestedTestsInput(rule.suggested_test_names.join(", "));
    setShowCreateModal(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    const approved = approvedTestsInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const suggested = suggestedTestsInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      setIsSubmitting(true);
      if (editingRule) {
        // Publish new version
        await publishRule(editingRule.id, {
          approved_test_names: approved,
          suggested_test_names: suggested,
        });
      } else {
        // Create initial rule
        await createRule({
          name: name.trim(),
          description: description.trim(),
          approved_test_names: approved,
          suggested_test_names: suggested,
        });
      }
      setShowCreateModal(false);
      await loadRules();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to save rule.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const columns: Column<ConsultationTypeRule>[] = [
    {
      header: "Consultation Type",
      accessor: "name",
      render: (rule) => (
        <div>
          <div className="font-semibold text-ink flex items-center gap-2">
            {rule.name}
            <span className="rounded bg-line/80 px-1.5 py-0.5 text-[11px] font-mono font-medium text-ink-2">
              v{rule.version}
            </span>
          </div>
          {rule.description && <div className="text-xs text-ink-3 mt-0.5">{rule.description}</div>}
        </div>
      ),
    },
    {
      header: "Approved Tests (Strict)",
      render: (rule) => (
        <div className="flex flex-wrap gap-1 max-w-xs">
          {rule.approved_test_names.map((test, i) => (
            <span key={i} className="inline-flex items-center gap-1 rounded-md bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-xs font-medium text-emerald-800">
              <CheckCircle2 className="h-3 w-3 text-emerald-600" />
              {test}
            </span>
          ))}
        </div>
      ),
    },
    {
      header: "Suggested Tests (Optional)",
      render: (rule) => (
        <div className="flex flex-wrap gap-1 max-w-xs">
          {rule.suggested_test_names.map((test, i) => (
            <span key={i} className="inline-flex items-center gap-1 rounded-md bg-amber-50 border border-amber-200 px-2 py-0.5 text-xs font-medium text-amber-800">
              <Tag className="h-3 w-3 text-amber-600" />
              {test}
            </span>
          ))}
        </div>
      ),
    },
    {
      header: "Status",
      accessor: "status",
      render: (rule) => {
        const isPub = rule.status === "published";
        return (
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium capitalize ${
              isPub
                ? "bg-brand/10 text-brand border border-brand/20"
                : "bg-surface-3 text-ink-3 border border-line"
            }`}
          >
            {isPub ? <ShieldCheck className="h-3.5 w-3.5" /> : <History className="h-3.5 w-3.5" />}
            {rule.status}
          </span>
        );
      },
    },
    {
      header: "Actions",
      render: (rule) =>
        isAdmin && rule.status === "published" ? (
          <button
            onClick={() => handleOpenEdit(rule)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-surface px-3 py-1.5 text-xs font-medium text-ink transition hover:bg-line/60"
          >
            <Edit3 className="h-3.5 w-3.5" /> Edit & Publish v{rule.version + 1}
          </button>
        ) : null,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Clinical Admin: Rules Engine</h1>
          <p className="text-sm text-ink-2">
            Configure approved and suggested lab test lists per consultation type with audited version publishing.
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={handleOpenCreate}
            className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-brand/90"
          >
            <Plus className="h-4 w-4" /> New Consultation Type
          </button>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <AlertCircle className="h-5 w-5 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="py-12 text-center text-sm text-ink-3">Loading consultation type rules...</div>
      ) : (
        <DataTable
          data={rules}
          columns={columns}
          searchPlaceholder="Search rules..."
          searchFilter={(item, q) => item.name.toLowerCase().includes(q.toLowerCase())}
          categoryFilter={{
            label: "Status",
            key: "status",
            options: [
              { label: "Published", value: "published" },
              { label: "Archived", value: "archived" },
            ],
          }}
          keyExtractor={(item) => item.id}
          emptyText="No consultation type rules found. Create one to get started."
        />
      )}

      {/* Create / Publish Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl border border-line bg-paper p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-line pb-4">
              <h2 className="text-lg font-bold text-ink">
                {editingRule ? `Publish New Version (v${editingRule.version + 1})` : "Create Consultation Type"}
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-ink-3 hover:text-ink text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {!editingRule && (
                <>
                  <div>
                    <label className="block text-xs font-semibold uppercase text-ink-2 mb-1">
                      Consultation Type Name
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Cardiology Panel"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full rounded-lg border border-line bg-surface p-2.5 text-sm text-ink outline-none focus:border-brand"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold uppercase text-ink-2 mb-1">Description</label>
                    <input
                      type="text"
                      placeholder="Optional brief description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full rounded-lg border border-line bg-surface p-2.5 text-sm text-ink outline-none focus:border-brand"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-xs font-semibold uppercase text-ink-2 mb-1">
                  Approved Test Names (Comma-separated)
                </label>
                <textarea
                  rows={3}
                  value={approvedTestsInput}
                  onChange={(e) => setApprovedTestsInput(e.target.value)}
                  placeholder="Hemoglobin, WBC Count, Platelets"
                  className="w-full rounded-lg border border-line bg-surface p-2.5 text-sm font-mono text-ink outline-none focus:border-brand"
                />
                <p className="text-[11px] text-ink-3 mt-1">Tests listed here will be verified for doctor view.</p>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-ink-2 mb-1">
                  Suggested Test Names (Comma-separated)
                </label>
                <textarea
                  rows={2}
                  value={suggestedTestsInput}
                  onChange={(e) => setSuggestedTestsInput(e.target.value)}
                  placeholder="Serum Creatinine, Fasting Glucose"
                  className="w-full rounded-lg border border-line bg-surface p-2.5 text-sm font-mono text-ink outline-none focus:border-brand"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-line">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-line bg-surface px-4 py-2 text-sm font-medium text-ink hover:bg-line/60"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-lg bg-brand px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand/90 disabled:opacity-50"
                >
                  {isSubmitting
                    ? "Saving..."
                    : editingRule
                    ? `Approve & Publish v${editingRule.version + 1}`
                    : "Create & Publish"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
