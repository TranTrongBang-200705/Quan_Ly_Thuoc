import {
  Brain,
  Building2,
  Lock,
  Mail,
  Phone,
  ShieldCheck,
  Sparkles,
  UserRound,
} from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { api } from "../api";
import { Alert, Button, Card, Input } from "../components/ui";
import { normalizeApiError } from "../utils/format";

export function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    phone: "",
    organization: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isLogin = mode === "login";

  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function validate() {
    if (!form.email.trim())
      return isLogin
        ? "Vui lòng nhập email hoặc username."
        : "Vui lòng nhập email.";
    if (!form.password) return "Vui lòng nhập mật khẩu.";
    if (!isLogin && !form.fullName.trim()) return "Vui lòng nhập họ tên.";
    if (!isLogin && form.password.length < 6)
      return "Mật khẩu phải có ít nhất 6 ký tự.";
    if (!isLogin && form.password !== form.confirmPassword)
      return "Mật khẩu nhập lại không khớp.";
    return "";
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    const message = validate();
    if (message) {
      setError(message);
      return;
    }

    setLoading(true);
    try {
      const result = isLogin
        ? await api.login({
            email: form.email.trim(),
            password: form.password,
          })
        : await api.register({
            fullName: form.fullName.trim(),
            email: form.email.trim(),
            phone: form.phone || null,
            organization: form.organization || null,
            password: form.password,
            confirmPassword: form.confirmPassword,
          });
      toast.success(isLogin ? "Đăng nhập thành công!" : "Đăng ký thành công!");
      onAuthenticated(result);
    } catch (err) {
      const msg = normalizeApiError(err.message);
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-5 sm:p-8 bg-gradient-to-br from-[#eaf7ff] via-[#f6fbff] to-[#f0fdf4] relative overflow-hidden">
      {/* Subtle background decorations */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-gradient-to-br from-teal-200/20 to-transparent rounded-full -translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-gradient-to-tl from-cyan-200/15 to-transparent rounded-full translate-x-1/3 translate-y-1/3" />
      </div>

      <div className="relative z-10 w-full max-w-[1080px] grid lg:grid-cols-[1.1fr,1fr] gap-8 lg:gap-12 items-center">
        {/* ── Left: Hero Section ── */}
        <section className="hidden lg:block">
          {/* Brand */}
          <div className="flex items-center gap-3 mb-6">
            <div className="w-14 h-14 rounded-[var(--radius-md)] bg-gradient-to-br from-teal-400 to-cyan-400 flex items-center justify-center text-white font-black text-xl shadow-lg shadow-teal-500/20">
              DD
            </div>
            <div>
              <div className="text-xs font-bold text-teal-600 tracking-widest uppercase">
                Clinical Intelligence Platform
              </div>
            </div>
          </div>

          <h1 className="text-5xl xl:text-6xl font-black text-slate-900 leading-[0.95] m-0 mb-4">
            DrugDiseaseML
          </h1>
          <p className="text-base text-slate-600 leading-relaxed max-w-lg m-0">
            Nền tảng hỗ trợ phân tích liên kết thuốc-bệnh bằng AI cho học tập,
            nghiên cứu và thực hành y dược.
          </p>

          {/* Proof badges */}
          <div className="flex flex-wrap gap-2.5 mt-8">
            {[
              { icon: Brain, text: "AI Medical Intelligence" },
              { icon: ShieldCheck, text: "Clinical safety first" },
              { icon: Sparkles, text: "Data-driven insight" },
            ].map(({ icon: Icon, text }) => (
              <span
                key={text}
                className="inline-flex items-center gap-2 h-9 px-3.5 rounded-full border border-teal-200/60 bg-white/70 text-sm font-bold text-teal-700 backdrop-blur-sm"
              >
                <Icon size={16} />
                {text}
              </span>
            ))}
          </div>
        </section>

        {/* ── Right: Auth Card ── */}
        <Card className="!p-7 sm:!p-8 bg-white/90 backdrop-blur-xl shadow-[0_20px_60px_rgba(15,23,42,0.08)] max-w-[480px] lg:max-w-none mx-auto w-full">
          {/* Mobile brand */}
          <div className="lg:hidden flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-teal-400 to-cyan-400 flex items-center justify-center text-white font-black text-sm">
              DD
            </div>
            <div>
              <div className="text-sm font-extrabold text-slate-900">DrugDiseaseML</div>
              <div className="text-[10px] font-bold text-teal-600 uppercase tracking-wide">
                AI Medical Intelligence
              </div>
            </div>
          </div>

          {/* Header */}
          <div className="mb-6">
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
              {isLogin ? "Đăng nhập hệ thống" : "Tạo tài khoản nghiên cứu"}
            </span>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 m-0">
              {isLogin ? "Chào mừng quay lại" : "Bắt đầu với DrugDiseaseML"}
            </h2>
            <p className="text-sm text-slate-500 mt-1.5 m-0">
              {isLogin
                ? "Sử dụng email hoặc username để truy cập dashboard."
                : "Tạo tài khoản người dùng để gửi yêu cầu dự đoán."}
            </p>
          </div>

          {/* Form */}
          <form className="space-y-4" onSubmit={submit}>
            {!isLogin && (
              <>
                <Input
                  label="Họ tên"
                  icon={UserRound}
                  value={form.fullName}
                  onChange={(e) => update("fullName", e.target.value)}
                  placeholder="Nguyễn Văn A"
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Số điện thoại"
                    icon={Phone}
                    value={form.phone}
                    onChange={(e) => update("phone", e.target.value)}
                    placeholder="0900000000"
                  />
                  <Input
                    label="Tổ chức"
                    icon={Building2}
                    value={form.organization}
                    onChange={(e) => update("organization", e.target.value)}
                    placeholder="Trường / bệnh viện"
                  />
                </div>
              </>
            )}

            <Input
              label={isLogin ? "Email hoặc username" : "Email"}
              icon={Mail}
              type={isLogin ? "text" : "email"}
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              placeholder={
                isLogin ? "admin hoặc user@example.com" : "user@example.com"
              }
            />

            <Input
              label="Mật khẩu"
              icon={Lock}
              type="password"
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              placeholder="Ít nhất 6 ký tự"
            />

            {!isLogin && (
              <Input
                label="Nhập lại mật khẩu"
                icon={Lock}
                type="password"
                value={form.confirmPassword}
                onChange={(e) => update("confirmPassword", e.target.value)}
                placeholder="Nhập lại mật khẩu"
              />
            )}

            {error && <Alert tone="danger">{error}</Alert>}

            <Button loading={loading} disabled={loading} className="w-full !h-12 !text-base">
              {loading
                ? "Đang xử lý..."
                : isLogin
                  ? "Đăng nhập"
                  : "Đăng ký"}
            </Button>
          </form>

          {/* Switch mode */}
          <div className="text-center mt-5">
            <button
              className="text-sm font-bold text-teal-600 hover:text-teal-700 border-0 bg-transparent transition-colors"
              onClick={() => {
                setError("");
                setMode(isLogin ? "register" : "login");
              }}
            >
              {isLogin
                ? "Chưa có tài khoản? Đăng ký"
                : "Đã có tài khoản? Đăng nhập"}
            </button>
          </div>
        </Card>
      </div>
    </main>
  );
}
