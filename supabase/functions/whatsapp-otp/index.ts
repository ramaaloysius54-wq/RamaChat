import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const WA_API_URL = Deno.env.get("WA_PROVIDER_API_URL")!;
const WA_API_TOKEN = Deno.env.get("WA_PROVIDER_API_TOKEN")!;

const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

async function sha256(text: string): Promise<string> {
  const data = new TextEncoder().encode(text);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

serve(async (req) => {
  try {
    const { action, phone, otp_code } = await req.json();
    if (!phone) {
      return new Response(JSON.stringify({ ok: false, error: "Nomor WhatsApp wajib diisi" }), { status: 400 });
    }

    if (action === "send_otp") {
      // Cek cooldown 60 detik (Rate Limiting)
      const { data: recent } = await supabaseAdmin
        .from("whatsapp_otp_requests")
        .select("*")
        .eq("phone_number", phone)
        .order("created_at", { ascending: false })
        .limit(1)
        .maybeSingle();

      if (recent && new Date(recent.cooldown_until) > new Date()) {
        return new Response(
          JSON.stringify({ ok: false, error: "Harap tunggu 60 detik sebelum meminta OTP baru." }),
          { status: 429 }
        );
      }

      // Generate 6 digit OTP & simpan dalam bentuk SHA-256 hash (bukan plaintext)
      const otp = Math.floor(100000 + Math.random() * 900000).toString();
      const otpHash = await sha256(`${phone}:${otp}`);
      const now = Date.now();

      await supabaseAdmin.from("whatsapp_otp_requests").insert({
        phone_number: phone,
        otp_hash: otpHash,
        attempts: 0,
        expires_at: new Date(now + 5 * 60 * 1000).toISOString(),
        cooldown_until: new Date(now + 60 * 1000).toISOString(),
      });

      // Kirim pesan ke Gateway WhatsApp Resmi / Cloud API
      await fetch(WA_API_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${WA_API_TOKEN}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          to: phone,
          message: `*RamaChat* - Kode verifikasi OTP Anda adalah *${otp}*. Berlaku 5 menit. Jangan berikan kode ini kepada siapa pun.`,
        }),
      });

      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    }

    if (action === "verify_otp") {
      const { data: record } = await supabaseAdmin
        .from("whatsapp_otp_requests")
        .select("*")
        .eq("phone_number", phone)
        .order("created_at", { ascending: false })
        .limit(1)
        .maybeSingle();

      if (!record || new Date(record.expires_at) < new Date()) {
        return new Response(JSON.stringify({ ok: false, error: "OTP sudah kedaluwarsa (5 menit)." }), { status: 400 });
      }
      if (record.attempts >= 5) {
        return new Response(JSON.stringify({ ok: false, error: "Melebihi batas maksimal 5 percobaan." }), { status: 403 });
      }

      const candidateHash = await sha256(`${phone}:${otp_code}`);
      if (candidateHash !== record.otp_hash) {
        await supabaseAdmin
          .from("whatsapp_otp_requests")
          .update({ attempts: record.attempts + 1 })
          .eq("id", record.id);
        return new Response(JSON.stringify({ ok: false, error: "Kode OTP salah." }), { status: 401 });
      }

      return new Response(JSON.stringify({ ok: true, verified: true }), { status: 200 });
    }

    return new Response(JSON.stringify({ ok: false, error: "Action tidak dikenali" }), { status: 400 });
  } catch (err) {
    return new Response(JSON.stringify({ ok: false, error: String(err) }), { status: 500 });
  }
});
