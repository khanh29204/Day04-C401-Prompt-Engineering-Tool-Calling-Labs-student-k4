import { useState } from "react";

const EMPTY_AUTH_STATE = {
  authenticated: false,
  fullname: "",
  member_level: "",
  loading: false,
  error: "",
};

function StatusDot({ active }) {
  return (
    <span
      aria-hidden="true"
      className={`h-2.5 w-2.5 rounded-full ${active ? "bg-emerald-500" : "bg-slate-400"}`}
    />
  );
}

function ActivityItem({ item, index }) {
  const title = item?.title || item?.tool || "CGV activity";
  const detail = item?.detail || item?.message || item?.status || "Đang chờ cập nhật";
  const state = item?.state || item?.status;
  const isWorking = state === "loading" || state === "running";
  const isError = state === "error" || item?.error;

  return (
    <li className="flex gap-3 py-3" key={item?.id || `${title}-${index}`}>
      <span
        aria-hidden="true"
        className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${
          isError ? "bg-rose-500" : isWorking ? "animate-pulse bg-amber-500" : "bg-violet-500"
        }`}
      />
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-slate-800">{title}</p>
        <p className="mt-0.5 text-sm leading-5 text-slate-500">{detail}</p>
      </div>
    </li>
  );
}

function ProfilePreview({ profile }) {
  if (!profile) {
    return (
      <p className="rounded-2xl bg-slate-50 px-4 py-5 text-sm leading-6 text-slate-500">
        Đăng nhập để xem thông tin thành viên CGV và các thao tác agent đang thực hiện.
      </p>
    );
  }

  const details = [
    ["Tên", profile.fullname || profile.name || profile.full_name],
    ["Hạng", profile.member_level || profile.memberLevel || profile.level],
    ["Điểm", profile.point ?? profile.points ?? profile.available_points],
  ].filter(([, value]) => value !== undefined && value !== null && value !== "");

  return (
    <dl className="grid gap-3 rounded-2xl bg-violet-50 p-4 sm:grid-cols-2">
      {details.length > 0 ? (
        details.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs font-medium uppercase tracking-wide text-violet-700">{label}</dt>
            <dd className="mt-1 break-words text-sm font-semibold text-slate-800">{String(value)}</dd>
          </div>
        ))
      ) : (
        <p className="text-sm text-slate-600">Đã đăng nhập. Thông tin hồ sơ đang được cập nhật.</p>
      )}
    </dl>
  );
}

export default function CgvPanel({
  authState = EMPTY_AUTH_STATE,
  activity = [],
  profile,
  onLogin,
  onLogout,
  onLoadProfile,
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const auth = { ...EMPTY_AUTH_STATE, ...authState };

  async function handleSubmit(event) {
    event.preventDefault();
    if (!onLogin || auth.loading) return;

    try {
      await onLogin({ email: email.trim(), password });
      setPassword("");
    } catch {
      // The parent owns the error state so API details are not duplicated here.
    }
  }

  return (
    <aside aria-label="CGV activity and account" className="flex h-full min-h-0 flex-col gap-5">
      <section className="rounded-[28px] bg-white p-5 shadow-[0_2px_8px_rgba(31,24,54,0.08)] ring-1 ring-slate-200">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-violet-700">CGV companion</p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">Tài khoản CGV</h2>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600">
            <StatusDot active={auth.authenticated} />
            {auth.authenticated ? "Đã kết nối" : "Chưa đăng nhập"}
          </div>
        </div>

        {auth.authenticated ? (
          <div className="mt-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="font-semibold text-slate-800">{auth.fullname || "Thành viên CGV"}</p>
                {auth.member_level ? <p className="mt-0.5 text-sm text-slate-500">{auth.member_level}</p> : null}
              </div>
              <button
                type="button"
                onClick={onLogout}
                disabled={auth.loading}
                className="rounded-full px-4 py-2 text-sm font-semibold text-violet-700 outline-none transition hover:bg-violet-50 focus-visible:ring-2 focus-visible:ring-violet-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Đăng xuất
              </button>
            </div>
            {auth.error ? <p role="alert" className="mt-3 text-sm text-rose-700">{auth.error}</p> : null}
          </div>
        ) : (
          <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
            <p className="text-sm leading-5 text-slate-600">Đăng nhập để agent có thể xem hồ sơ và sơ đồ ghế của bạn.</p>
            <label className="block text-sm font-medium text-slate-700">
              Email CGV
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                disabled={auth.loading}
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-violet-600 focus:ring-2 focus:ring-violet-200 disabled:cursor-not-allowed disabled:bg-slate-100"
                placeholder="name@example.com"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Mật khẩu CGV
              <input
                type="password"
                autoComplete="current-password"
                required
                minLength="1"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={auth.loading}
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 text-slate-900 outline-none transition focus:border-violet-600 focus:ring-2 focus:ring-violet-200 disabled:cursor-not-allowed disabled:bg-slate-100"
              />
            </label>
            {auth.error ? <p role="alert" className="text-sm text-rose-700">{auth.error}</p> : null}
            <button
              type="submit"
              disabled={auth.loading}
              className="w-full rounded-full bg-violet-700 px-5 py-3 text-sm font-semibold text-white shadow-sm outline-none transition hover:bg-violet-800 focus-visible:ring-2 focus-visible:ring-violet-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {auth.loading ? "Đang đăng nhập…" : "Đăng nhập CGV"}
            </button>
            <p className="text-xs leading-5 text-slate-500">Thông tin đăng nhập chỉ được gửi đến backend an toàn của ứng dụng.</p>
          </form>
        )}
      </section>

      <section className="rounded-[28px] bg-white p-5 shadow-[0_2px_8px_rgba(31,24,54,0.08)] ring-1 ring-slate-200">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Xem trước</h2>
            <p className="mt-0.5 text-sm text-slate-500">Thông tin an toàn từ CGV</p>
          </div>
          {auth.authenticated ? (
            <button
              type="button"
              onClick={onLoadProfile}
              disabled={auth.loading}
              className="rounded-full bg-violet-50 px-3.5 py-2 text-sm font-semibold text-violet-700 outline-none transition hover:bg-violet-100 focus-visible:ring-2 focus-visible:ring-violet-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Làm mới
            </button>
          ) : null}
        </div>
        <div className="mt-4"><ProfilePreview profile={profile} /></div>
      </section>

      <section className="min-h-0 flex-1 rounded-[28px] bg-white p-5 shadow-[0_2px_8px_rgba(31,24,54,0.08)] ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold text-slate-900">Agent đang làm gì?</h2>
        <p className="mt-0.5 text-sm text-slate-500">Các thao tác CGV gần đây</p>
        {activity.length > 0 ? (
          <ol className="mt-3 divide-y divide-slate-100">{activity.map((item, index) => <ActivityItem item={item} index={index} key={item?.id || `${item?.title || item?.tool || "activity"}-${index}`} />)}</ol>
        ) : (
          <p className="mt-4 rounded-2xl bg-slate-50 px-4 py-5 text-sm leading-6 text-slate-500">Khi agent tra cứu CGV, hoạt động sẽ xuất hiện tại đây.</p>
        )}
      </section>
    </aside>
  );
}
