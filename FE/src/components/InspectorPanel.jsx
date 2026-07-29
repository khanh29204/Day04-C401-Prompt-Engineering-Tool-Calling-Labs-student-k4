import { useEffect, useState } from "react";
import { api } from "../api.js";

function Json({ value }) {
  return (
    <pre className="max-h-72 overflow-auto rounded-2xl bg-slate-900 px-4 py-3 text-xs leading-5 text-slate-100">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function Field({ label, value }) {
  if (value === undefined || value === null || value === "") return null;
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-violet-700">{label}</dt>
      <dd className="mt-1 break-words text-sm font-semibold text-slate-800">{String(value)}</dd>
    </div>
  );
}

function VersionCard({ version, onRefresh, loading, error }) {
  const av = version?.artifact_version;
  return (
    <section className="rounded-[28px] bg-white p-5 shadow-[0_2px_8px_rgba(31,24,54,0.08)] ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-violet-700">Agent runtime</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">Artifact version</h2>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="rounded-full bg-violet-50 px-3.5 py-2 text-sm font-semibold text-violet-700 outline-none transition hover:bg-violet-100 focus-visible:ring-2 focus-visible:ring-violet-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Đang tải…" : "Làm mới"}
        </button>
      </div>
      {error ? <p role="alert" className="mt-3 text-sm text-rose-700">{error}</p> : null}
      {av ? (
        <dl className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Version" value={av.version} />
          <Field label="Artifact version" value={av.artifact_version} />
          <Field label="Provider" value={version.provider} />
          <Field label="Model" value={version.model} />
          <Field label="Max tool rounds" value={version.max_tool_rounds} />
          <Field label="Prompt hash" value={av.prompt_hash?.slice(0, 16)} />
          <Field label="Tools hash" value={av.tools_hash?.slice(0, 16)} />
        </dl>
      ) : (
        <p className="mt-4 text-sm text-slate-500">{loading ? "Đang tải phiên bản artifact…" : "Chưa có dữ liệu."}</p>
      )}
    </section>
  );
}

function ToolEventsTable({ events }) {
  if (!Array.isArray(events) || events.length === 0) {
    return <p className="text-sm text-slate-500">Không có tool nào được gọi ở lượt này.</p>;
  }
  return (
    <ul className="space-y-2">
      {events.map((event, index) => {
        const isError = Boolean(event?.result?.error);
        return (
          <li key={`${event?.tool}-${index}`} className="rounded-2xl bg-slate-50 p-3">
            <div className="flex items-center justify-between gap-3">
              <span className="font-mono text-sm font-semibold text-slate-800">{event?.tool}</span>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${isError ? "bg-rose-100 text-rose-700" : "bg-emerald-100 text-emerald-700"}`}>
                {isError ? "error" : "ok"}
              </span>
            </div>
            <details className="mt-2">
              <summary className="cursor-pointer text-xs font-medium text-violet-700">args & result</summary>
              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                <div>
                  <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Args</p>
                  <Json value={event?.args} />
                </div>
                <div>
                  <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Result</p>
                  <Json value={event?.result} />
                </div>
              </div>
            </details>
          </li>
        );
      })}
    </ul>
  );
}

function InteractionCard({ interaction }) {
  const { at, request, response, error } = interaction;
  const status = error ? "error" : response?.status || "unknown";
  const statusStyles = {
    answered: "bg-emerald-100 text-emerald-700",
    waiting_for_user: "bg-amber-100 text-amber-700",
    max_tool_rounds: "bg-amber-100 text-amber-700",
    error: "bg-rose-100 text-rose-700",
    unknown: "bg-slate-100 text-slate-600",
  };

  return (
    <li className="rounded-[24px] bg-white p-5 shadow-[0_2px_8px_rgba(31,24,54,0.08)] ring-1 ring-slate-200">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-medium text-slate-500">{at}</span>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusStyles[status] || statusStyles.unknown}`}>{status}</span>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Request</p>
          <Json value={request} />
        </div>
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Response</p>
          {error ? <Json value={{ error }} /> : <Json value={{ status: response?.status, assistant_text: response?.assistant_text }} />}
        </div>
      </div>

      {response?.artifact_version ? (
        <p className="mt-3 text-xs text-slate-500">
          artifact_version: <span className="font-mono text-slate-700">{response.artifact_version.artifact_version}</span>
        </p>
      ) : null}

      <div className="mt-4">
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Tool events</p>
        <ToolEventsTable events={response?.tool_events} />
      </div>

      {Array.isArray(response?.rounds) && response.rounds.length > 0 ? (
        <details className="mt-4">
          <summary className="cursor-pointer text-xs font-medium text-violet-700">raw rounds</summary>
          <div className="mt-2"><Json value={response.rounds} /></div>
        </details>
      ) : null}
    </li>
  );
}

export default function InspectorPanel({ interactions = [] }) {
  const [version, setVersion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadVersion = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await api.agentVersion();
      setVersion(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVersion();
  }, []);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto">
      <VersionCard version={version} onRefresh={loadVersion} loading={loading} error={error} />

      <section aria-label="Lịch sử request/response của agent">
        <h2 className="mb-3 text-lg font-semibold text-slate-900">Request / Response / Tool events</h2>
        {interactions.length === 0 ? (
          <p className="rounded-[24px] bg-white p-5 text-sm leading-6 text-slate-500 shadow-[0_2px_8px_rgba(31,24,54,0.08)] ring-1 ring-slate-200">
            Chưa có lượt chat nào. Gửi tin nhắn ở tab Chat để xem chi tiết tại đây.
          </p>
        ) : (
          <ul className="space-y-4">
            {interactions.map((interaction) => <InteractionCard key={interaction.id} interaction={interaction} />)}
          </ul>
        )}
      </section>
    </div>
  );
}
