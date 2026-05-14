/**
 * edge-api -- Cloudflare Worker for DevOps Lab 17
 *
 * A simple HTTP API deployed on Cloudflare's edge network.
 * Routes: /, /health, /edge, /counter, /settings
 * Version: v2 (rollback test)
 */

export interface Env {
	APP_NAME: string;
	COURSE_NAME: string;
	API_TOKEN: string;
	ADMIN_EMAIL: string;
	SETTINGS: KVNamespace;
}

export default {
	async fetch(request, env, ctx): Promise<Response> {
		const url = new URL(request.url);
		const path = url.pathname;

		// Log every request for observability
		console.log("request", {
			path,
			method: request.method,
			colo: request.cf?.colo,
			country: request.cf?.country,
		});

		// GET / -- general app information
		if (path === "/" && request.method === "GET") {
			return Response.json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				version: "v2",
				message: "Hello from Cloudflare Workers!",
				timestamp: new Date().toISOString(),
			});
		}

		// GET /health -- health check endpoint
		if (path === "/health" && request.method === "GET") {
			return Response.json({
				status: "ok",
				uptime: "all good here",
				timestamp: new Date().toISOString(),
			});
		}

		// GET /edge -- edge metadata from request context
		if (path === "/edge" && request.method === "GET") {
			return Response.json({
				colo: request.cf?.colo ?? "unknown",
				country: request.cf?.country ?? "unknown",
				city: request.cf?.city ?? "unknown",
				asn: request.cf?.asn ?? "unknown",
				httpProtocol: request.cf?.httpProtocol ?? "unknown",
				tlsVersion: request.cf?.tlsVersion ?? "unknown",
				timezone: request.cf?.timezone ?? "unknown",
				latitude: request.cf?.latitude ?? "unknown",
				longitude: request.cf?.longitude ?? "unknown",
				timestamp: new Date().toISOString(),
			});
		}

		// GET /counter -- KV-backed persistent counter
		if (path === "/counter") {
			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));
			return Response.json({
				visits,
				message: "This counter persists across deploys via KV",
			});
		}

		// GET /settings -- show configured vars (but NOT secrets!)
		if (path === "/settings" && request.method === "GET") {
			return Response.json({
				app_name: env.APP_NAME,
				course_name: env.COURSE_NAME,
				// secrets are never exposed in responses
				secrets_configured: ["API_TOKEN", "ADMIN_EMAIL"],
				note: "Secret values are never shown -- they stay encrypted",
			});
		}

		// 404 for everything else
		return new Response(JSON.stringify({ error: "Not Found", path }), {
			status: 404,
			headers: { "Content-Type": "application/json" },
		});
	},
} satisfies ExportedHandler<Env>;
