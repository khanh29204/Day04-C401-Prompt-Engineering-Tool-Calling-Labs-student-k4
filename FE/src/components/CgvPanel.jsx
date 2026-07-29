import { useEffect, useState } from "react";

const SEAT_STATUS_STYLES = [
  "bg-emerald-100 text-emerald-700",
  "bg-sky-100 text-sky-700",
  "bg-amber-100 text-amber-700",
  "bg-rose-100 text-rose-700",
  "bg-slate-200 text-slate-600",
];

function seatStatusStyle(status, statusOrder) {
  const index = statusOrder.indexOf(status);
  return SEAT_STATUS_STYLES[index % SEAT_STATUS_STYLES.length] ?? SEAT_STATUS_STYLES[SEAT_STATUS_STYLES.length - 1];
}

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

function MoviePreview({ movie }) {
  if (!movie) return null;

  return (
    <div className="flex gap-4">
      {movie.posterUrl ? (
        <img
          src={movie.posterUrl}
          alt={movie.title || "Poster phim"}
          className="h-32 w-24 shrink-0 rounded-xl object-cover ring-1 ring-slate-200"
        />
      ) : (
        <div className="grid h-32 w-24 shrink-0 place-items-center rounded-xl bg-slate-100 text-center text-xs text-slate-400">
          Không có ảnh
        </div>
      )}
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-violet-700">Phim đang xem</p>
        <h3 className="mt-1 truncate text-base font-semibold text-slate-900">{movie.title || "Chưa rõ tên phim"}</h3>
        {movie.rating != null ? <p className="mt-1 text-sm text-slate-500">⭐ {movie.rating}/10</p> : null}
        {movie.meta ? <p className="mt-1 text-sm leading-5 text-slate-500">{movie.meta}</p> : null}
      </div>
    </div>
  );
}

function SeatmapPreview({ seatmap, selectedSeats, onToggleSeat }) {
  if (!seatmap || !Array.isArray(seatmap.rows) || seatmap.rows.length === 0) return null;
  const statusOrder = Object.keys(seatmap.status_counts || {});

  return (
    <div className="flex min-h-0 flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-violet-700">Sơ đồ ghế</p>
          <h3 className="mt-1 text-sm text-slate-500">
            {[seatmap.cinema_id ? `Rạp ${seatmap.cinema_id}` : null, seatmap.date].filter(Boolean).join(" · ") || "Suất chiếu"}
          </h3>
        </div>
        {selectedSeats.size > 0 ? (
          <span className="shrink-0 rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">
            {selectedSeats.size} ghế đang chọn
          </span>
        ) : null}
      </div>

      {statusOrder.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {statusOrder.map((status) => (
            <span key={status} className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${seatStatusStyle(status, statusOrder)}`}>
              mã {status} · {seatmap.status_counts[status]}
            </span>
          ))}
        </div>
      ) : null}

      <div className="max-h-60 min-h-0 overflow-auto rounded-2xl bg-slate-50 p-3">
        <div className="flex flex-col gap-1.5">
          {seatmap.rows.map((row) => (
            <div className="flex items-center gap-1.5" key={row.label}>
              <span className="w-5 shrink-0 text-xs font-semibold text-slate-400">{row.label}</span>
              <div className="flex flex-wrap gap-1">
                {row.seats.map((seat, seatIndex) => {
                  const seatId = seat.id || `${row.label}-${seat.col ?? seatIndex}`;
                  const isSelected = selectedSeats.has(seatId);
                  return (
                    <button
                      key={seatId}
                      type="button"
                      onClick={() => onToggleSeat(seatId)}
                      title={`Ghế ${seatId} · mã trạng thái ${seat.status}${seat.price ? ` · ${Number(seat.price).toLocaleString("vi-VN")}đ` : ""}`}
                      className={`grid h-6 w-6 shrink-0 place-items-center rounded text-[10px] font-medium transition ${
                        isSelected ? "bg-violet-600 text-white" : seatStatusStyle(String(seat.status), statusOrder)
                      }`}
                    >
                      {seat.col ?? "•"}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
      <p className="text-[11px] leading-4 text-slate-400">
        Mã trạng thái ghế do hệ thống CGV trả về. Bấm vào ghế để đánh dấu ghế đang chọn trên giao diện xem trước này.
      </p>
    </div>
  );
}

export default function CgvPanel({
  authState = EMPTY_AUTH_STATE,
  activity = [],
  profile,
  movie,
  seatmap,
  onLogin,
  onLogout,
  onLoadProfile,
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [selectedSeats, setSelectedSeats] = useState(() => new Set());
  const auth = { ...EMPTY_AUTH_STATE, ...authState };

  useEffect(() => {
    setSelectedSeats(new Set());
  }, [seatmap?.cinema_id, seatmap?.session_id, seatmap?.date]);

  function toggleSeat(seatId) {
    setSelectedSeats((current) => {
      const next = new Set(current);
      if (next.has(seatId)) next.delete(seatId);
      else next.add(seatId);
      return next;
    });
  }

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

      <section className="flex min-h-0 shrink-0 flex-col gap-4 rounded-[28px] bg-white p-5 shadow-[0_2px_8px_rgba(31,24,54,0.08)] ring-1 ring-slate-200">
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
        <MoviePreview movie={movie} />
        <SeatmapPreview seatmap={seatmap} selectedSeats={selectedSeats} onToggleSeat={toggleSeat} />
        {!movie && !seatmap ? <ProfilePreview profile={profile} /> : null}
      </section>

      <section className="flex min-h-0 flex-1 flex-col rounded-[28px] bg-white p-5 shadow-[0_2px_8px_rgba(31,24,54,0.08)] ring-1 ring-slate-200">
        <div className="shrink-0">
          <h2 className="text-lg font-semibold text-slate-900">Agent đang làm gì?</h2>
          <p className="mt-0.5 text-sm text-slate-500">Các thao tác CGV gần đây</p>
        </div>
        <div className="mt-3 min-h-0 flex-1 overflow-y-auto">
          {activity.length > 0 ? (
            <ol className="divide-y divide-slate-100">{activity.map((item, index) => <ActivityItem item={item} index={index} key={item?.id || `${item?.title || item?.tool || "activity"}-${index}`} />)}</ol>
          ) : (
            <p className="rounded-2xl bg-slate-50 px-4 py-5 text-sm leading-6 text-slate-500">Khi agent tra cứu CGV, hoạt động sẽ xuất hiện tại đây.</p>
          )}
        </div>
      </section>
    </aside>
  );
}
