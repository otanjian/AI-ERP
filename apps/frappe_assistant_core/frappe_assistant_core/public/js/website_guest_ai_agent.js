// Public website AI customer service for Guest users (west.bosofts.com et al.)
(function () {
	"use strict";

	function isLoggedInUser() {
		if (typeof frappe === "undefined") {
			return false;
		}
		if (frappe.session && frappe.session.user) {
			return frappe.session.user !== "Guest";
		}
		if (frappe.boot && frappe.boot.user) {
			if (typeof frappe.boot.user === "string") {
				return frappe.boot.user !== "Guest";
			}
			if (frappe.boot.user.name) {
				return frappe.boot.user.name !== "Guest";
			}
		}
		return false;
	}

	function mountGuestAgent() {
		if (isExcludedPage() || isLoggedInUser() || document.getElementById("bosofts-ai-agent")) {
			return;
		}

		var PUBLIC_AGENT_URL =
			"https://ai.bosofts.com/agents/3a6420a3-8bbe-40a1-8da2-4c6aad83b487/6d752020a22b48ad4a5b5b651cd48fa5181fee135776e9f2b20d4e0645f93d72";
		var ROOT_ID = "bosofts-ai-agent";
		var OPEN_CLASS = "bosofts-ai-agent--open";

		var style = document.createElement("style");
		style.textContent =
			"#" +
			ROOT_ID +
			"{position:fixed;right:22px;bottom:22px;z-index:2147483000;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'PingFang SC','Microsoft YaHei',sans-serif;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__panel{position:absolute;right:0;bottom:78px;width:min(420px,calc(100vw - 32px));max-height:min(720px,calc(100vh - 110px));background:#fff;border-radius:16px;box-shadow:0 20px 50px rgba(15,23,42,.22),0 0 0 1px rgba(22,93,255,.08);overflow:hidden;opacity:0;visibility:hidden;transform:translateY(14px) scale(.97);transition:opacity .24s ease,transform .24s ease,visibility .24s;}" +
			"#" +
			ROOT_ID +
			"." +
			OPEN_CLASS +
			" .bosofts-ai-agent__panel{opacity:1;visibility:visible;transform:translateY(0) scale(1);}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__header{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 14px;background:linear-gradient(120deg,#00c2b8 0%,#165dff 55%,#0e42c2 100%);color:#fff;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__title{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:600;letter-spacing:.02em;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__title svg{width:18px;height:18px;flex-shrink:0;opacity:.95;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__close{width:30px;height:30px;border:0;border-radius:10px;background:rgba(255,255,255,.14);color:#fff;font-size:20px;line-height:1;cursor:pointer;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__frame-wrap{height:min(720px,calc(100vh - 152px));background:#f8fafc;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__frame{display:block;width:100%;height:100%;border:0;background:#fff;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__launcher{position:relative;display:flex;align-items:center;gap:10px;padding:0;border:0;background:transparent;cursor:pointer;color:#fff;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__orb{position:relative;width:62px;height:62px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(145deg,#00d4c8 0%,#165dff 48%,#0b36b8 100%);box-shadow:0 10px 28px rgba(22,93,255,.42),inset 0 1px 0 rgba(255,255,255,.35);}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__orb::before{content:'';position:absolute;inset:-4px;border-radius:50%;background:linear-gradient(145deg,rgba(0,212,200,.55),rgba(22,93,255,.45));filter:blur(8px);opacity:.75;z-index:-1;animation:bosofts-ai-agent-glow 2.8s ease-in-out infinite;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__ring{position:absolute;inset:-7px;border-radius:50%;border:1px solid rgba(22,93,255,.35);opacity:.8;animation:bosofts-ai-agent-ring 2.4s ease-out infinite;pointer-events:none;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__ring--delay{animation-delay:1.2s;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__icon{width:30px;height:30px;display:block;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__badge{position:absolute;top:-2px;right:-2px;min-width:18px;height:18px;padding:0 5px;border-radius:999px;background:linear-gradient(135deg,#22d3ee,#06b6d4);color:#042f3a;font-size:10px;font-weight:800;line-height:18px;text-align:center;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__chip{display:flex;flex-direction:column;align-items:flex-start;padding:10px 14px 10px 12px;border-radius:16px;background:rgba(255,255,255,.92);backdrop-filter:blur(12px);border:1px solid rgba(22,93,255,.12);box-shadow:0 10px 30px rgba(15,23,42,.12);}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__chip strong{font-size:13px;font-weight:700;color:#0f172a;}" +
			"#" +
			ROOT_ID +
			" .bosofts-ai-agent__chip span{font-size:11px;color:#64748b;margin-top:2px;}" +
			"@keyframes bosofts-ai-agent-glow{0%,100%{opacity:.55;transform:scale(.96);}50%{opacity:.95;transform:scale(1.04);}}" +
			"@keyframes bosofts-ai-agent-ring{0%{transform:scale(.92);opacity:.85;}70%{transform:scale(1.22);opacity:0;}100%{transform:scale(1.22);opacity:0;}}" +
			"@media (max-width:640px){#" +
			ROOT_ID +
			" .bosofts-ai-agent__chip{display:none;}}";
		document.head.appendChild(style);

		var aiIconSvg =
			'<svg class="bosofts-ai-agent__icon" viewBox="0 0 32 32" fill="none" aria-hidden="true"><path d="M10 8.5c0-2.2 1.8-4 4-4h4c2.2 0 4 1.8 4 4v1.2c2.2.5 3.8 2.4 3.8 4.8V18c0 2.7-2.2 4.9-4.9 4.9H14.9C12.2 22.9 10 20.7 10 18v-3.5c0-2.4 1.6-4.3 3.8-4.8V8.5Z" fill="rgba(255,255,255,.95)"/><circle cx="13.2" cy="15.2" r="1.35" fill="#165dff"/><circle cx="18.8" cy="15.2" r="1.35" fill="#165dff"/></svg>';

		var root = document.createElement("div");
		root.id = ROOT_ID;
		root.innerHTML =
			'<div class="bosofts-ai-agent__panel" role="dialog" aria-label="AI 智能客服" aria-hidden="true">' +
			'<div class="bosofts-ai-agent__header"><span class="bosofts-ai-agent__title">AI 智能客服</span>' +
			'<button type="button" class="bosofts-ai-agent__close" aria-label="关闭">&times;</button></div>' +
			'<div class="bosofts-ai-agent__frame-wrap">' +
			'<iframe class="bosofts-ai-agent__frame" title="AI 智能客服" allow="clipboard-write; microphone; camera"></iframe>' +
			"</div></div>" +
			'<button type="button" class="bosofts-ai-agent__launcher" aria-expanded="false" aria-label="打开 AI 智能客服">' +
			'<span class="bosofts-ai-agent__chip"><strong>AI 智能客服</strong><span>7×24 在线解答</span></span>' +
			'<span class="bosofts-ai-agent__orb"><span class="bosofts-ai-agent__ring"></span>' +
			'<span class="bosofts-ai-agent__ring bosofts-ai-agent__ring--delay"></span>' +
			aiIconSvg +
			'<span class="bosofts-ai-agent__badge">AI</span></span></button>';

		var panel = root.querySelector(".bosofts-ai-agent__panel");
		var launcher = root.querySelector(".bosofts-ai-agent__launcher");
		var closeBtn = root.querySelector(".bosofts-ai-agent__close");
		var iframe = root.querySelector(".bosofts-ai-agent__frame");
		var loaded = false;

		function loadIframe() {
			if (!loaded) {
				iframe.src = PUBLIC_AGENT_URL;
				loaded = true;
			}
		}

		function setOpen(open) {
			root.classList.toggle(OPEN_CLASS, open);
			launcher.setAttribute("aria-expanded", open ? "true" : "false");
			panel.setAttribute("aria-hidden", open ? "false" : "true");
			if (open) {
				loadIframe();
			}
		}

		launcher.addEventListener("click", function () {
			setOpen(!root.classList.contains(OPEN_CLASS));
		});
		closeBtn.addEventListener("click", function () {
			setOpen(false);
		});
		document.addEventListener("keydown", function (event) {
			if (event.key === "Escape") {
				setOpen(false);
			}
		});

		document.body.appendChild(root);
	}

	function isExcludedPage() {
		var pathname = window.location && window.location.pathname ? window.location.pathname : "/";
		pathname = pathname.replace(/\/+$/, "") || "/";
		return pathname === "/" || pathname === "/login";
	}

	function init() {
		if (!document.body) {
			return;
		}
		mountGuestAgent();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
})();
