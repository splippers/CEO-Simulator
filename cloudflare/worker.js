/**
 * CEO-Simulator Email Ingest Worker.
 *
 * Receives forwarded email from Cloudflare Email Routing and POSTs it to
 * the home game server via the /api/ingest/email endpoint.
 *
 * Deploy:
 *   npm install -g wrangler
 *   wrangler deploy
 */

export default {
  async email(message, env, ctx) {
    const from = message.from;
    const to = Array.isArray(message.to) ? message.to[0] : message.to;
    const subject = message.headers.get("subject") || "(no subject)";

    // Read raw email content
    let raw = "";
    try {
      raw = await message.raw.text();
    } catch {
      raw = "(could not read body)";
    }

    const role = extractRole(to);

    console.log(
      `ingest: role=${role} from=${from} to=${to} subject=${subject}`
    );

    const payload = {
      role,
      context: raw,
      secret: env.INGEST_SECRET,
    };

    const homeHost = env.HOME_HOST || "localhost:8080";
    const scheme = env.HOME_SCHEME || "http";
    const url = `${scheme}://${homeHost}/api/ingest/email`;

    try {
      const resp = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const text = await resp.text();
      console.log(`forwarded: ${resp.status} ${text.slice(0, 200)}`);
    } catch (err) {
      console.error(`forward failed: ${err}`);
    }
  },
};

/** Extract staff role from recipient email address. */
function extractRole(to) {
  if (!to) return "inbound";
  const local = to.split("@")[0].toLowerCase();
  const roles = { ceo: "ceo", cto: "cto", dev: "dev", ops: "ops", support: "support" };
  return roles[local] || "inbound";
}
