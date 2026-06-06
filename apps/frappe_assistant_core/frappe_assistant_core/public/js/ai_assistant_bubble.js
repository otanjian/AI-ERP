// Floating AI assistant bubble; opens embedded assistant in a side panel.
(function () {
	"use strict";

	var BUBBLE_ID = "fac-ai-assistant-bubble";
	var ROOT_ID = "fac-ai-assistant-root";
	var PANEL_ID = "fac-ai-assistant-panel";
	var WIDTH_STORAGE_KEY = "fac_ai_assistant_panel_width";
	var USER_SET_WIDTH_STORAGE_KEY = "fac_ai_assistant_panel_width_user_set";
	var SIZE_PRESET_STORAGE_KEY = "fac_ai_assistant_panel_size_preset";
	var WIDTH_STORAGE_VERSION_KEY = "fac_ai_assistant_panel_width_version";
	var WIDTH_STORAGE_VERSION = "2";
	var DEFAULT_PANEL_WIDTH = 1080;
	var MIN_PANEL_WIDTH = 520;
	var PANEL_WIDTH_STEP = 64;
	var DEFAULT_PRESET = "l";
	var SIZE_PRESETS = {
		m: 0.5,
		l: 0.66,
		xl: 0.8
	};

	var EMBED_FORM_CONTEXT_MESSAGE = "buildingai-set-form-context";
	var EMBED_READY_MESSAGE = "buildingai-embed-ready";

	function safeJsonStringify(value) {
		try {
			return JSON.stringify(value);
		} catch (e) {
			return "";
		}
	}

	function getFrappeRoute() {
		if (typeof frappe !== "undefined" && typeof frappe.get_route === "function") {
			var route = frappe.get_route();
			if (Array.isArray(route)) {
				return route;
			}
		}
		return [];
	}

	function pickDocSummary(doc) {
		if (!doc) {
			return null;
		}

		var summary = {
			name: doc.name,
			doctype: doc.doctype,
			docstatus: doc.docstatus,
			modified: doc.modified
		};

		if (doc.title) {
			summary.title = doc.title;
		}
		if (doc.status) {
			summary.status = doc.status;
		}
		if (doc.customer) {
			summary.customer = doc.customer;
		}
		if (doc.company) {
			summary.company = doc.company;
		}

		return summary;
	}

	function collectErpHostContext() {
		var pageUrl = window.location.href;
		var route = getFrappeRoute();
		var routeStr = route.length ? route.join("/") : "";
		var doctype = "";
		var docname = "";

		if (typeof cur_frm !== "undefined" && cur_frm && cur_frm.doctype) {
			doctype = cur_frm.doctype;
			docname = cur_frm.docname || "";
		} else if (route[0] === "Form" && route.length >= 3) {
			doctype = route[1];
			docname = route.slice(2).join("/");
		} else if (route[0] === "List" && route.length >= 2) {
			doctype = route[1];
		} else if (
			typeof frappe !== "undefined" &&
			frappe.router &&
			frappe.router.routes &&
			window.location.pathname.indexOf("/desk/") === 0
		) {
			var deskParts = window.location.pathname.replace(/^\/desk\/?/, "").split("/");
			var slug = deskParts[0] || "";
			var slugRoute = frappe.router.routes[slug];
			if (slugRoute && slugRoute.doctype) {
				doctype = slugRoute.doctype;
				if (deskParts[1] && deskParts[1] !== "view") {
					docname = decodeURIComponent(deskParts.slice(1).join("/"));
				}
			}
			if (!routeStr && slug) {
				routeStr = deskParts.join("/");
			}
		}

		var context = {
			href: pageUrl,
			pathname: window.location.pathname,
			route: route,
			page_type: route[0] || "",
			user:
				(typeof frappe !== "undefined" &&
					frappe.session &&
					frappe.session.user) ||
				""
		};

		if (typeof cur_frm !== "undefined" && cur_frm && cur_frm.doc) {
			context.form = pickDocSummary(cur_frm.doc);
			if (!doctype) {
				doctype = cur_frm.doctype;
				docname = cur_frm.docname || "";
			}
		}

		if (typeof cur_list !== "undefined" && cur_list) {
			context.list = {
				doctype: cur_list.doctype
			};
			if (cur_list.filter_area && typeof cur_list.get_filters_for_args === "function") {
				try {
					context.list.filters = cur_list.get_filters_for_args();
				} catch (e) {
					// Ignore filter read issues.
				}
			}
			if (!doctype && cur_list.doctype) {
				doctype = cur_list.doctype;
			}
		}

		if (typeof frappe !== "undefined" && frappe.boot && frappe.boot.sysdefaults) {
			context.company = frappe.boot.sysdefaults.company || "";
		}

		return {
			erp_page_url: pageUrl,
			erp_doctype: doctype,
			erp_docname: docname,
			erp_route: routeStr,
			erp_context_json: safeJsonStringify(context)
		};
	}

	function postEmbedFormContext(iframe, targetOrigin) {
		if (!iframe || !iframe.contentWindow) {
			return;
		}

		iframe.contentWindow.postMessage(
			{
				type: EMBED_FORM_CONTEXT_MESSAGE,
				payload: collectErpHostContext()
			},
			targetOrigin || "*"
		);
	}

	function appendContextQueryParams(baseUrl, context) {
		if (!baseUrl || !context) {
			return baseUrl;
		}

		try {
			var url = new URL(baseUrl, window.location.origin);
			Object.keys(context).forEach(function (key) {
				var value = context[key];
				if (value == null || value === "") {
					return;
				}
				// Keep iframe URL short; full JSON is sent via postMessage.
				if (key === "erp_context_json" && String(value).length > 512) {
					return;
				}
				url.searchParams.set("ctx_" + key, String(value));
			});
			return url.toString();
		} catch (e) {
			return baseUrl;
		}
	}

	function buildEmbedUrlWithContext() {
		return appendContextQueryParams(getEmbedUrl(), collectErpHostContext());
	}

	function getEmbedUrl() {
		if (typeof frappe !== "undefined" && frappe.boot && frappe.boot.ai_assistant_embed_url) {
			return frappe.boot.ai_assistant_embed_url;
		}
		return (
			"https://ai.bosofts.com/agents/3a6420a3-8bbe-40a1-8da2-4c6aad83b487/" +
			"6d752020a22b48ad4a5b5b651cd48fa5181fee135776e9f2b20d4e0645f93d72"
		);
	}

	function getMaxPanelWidth() {
		return Math.max(MIN_PANEL_WIDTH, Math.floor(window.innerWidth - 24));
	}

	function normalizeWidth(width) {
		var maxWidth = getMaxPanelWidth();
		return Math.max(MIN_PANEL_WIDTH, Math.min(maxWidth, width));
	}

	function getPresetWidth(preset) {
		var ratio = SIZE_PRESETS[preset] || SIZE_PRESETS[DEFAULT_PRESET];
		return normalizeWidth(Math.round(window.innerWidth * ratio));
	}

	function getStoredPreset() {
		try {
			var preset = localStorage.getItem(SIZE_PRESET_STORAGE_KEY);
			if (preset && SIZE_PRESETS[preset]) {
				return preset;
			}
		} catch (e) {
			// Ignore storage read issues.
		}
		return null;
	}

	function getStoredWidth() {
		try {
			var currentVersion = localStorage.getItem(WIDTH_STORAGE_VERSION_KEY);
			if (currentVersion !== WIDTH_STORAGE_VERSION) {
				localStorage.removeItem(WIDTH_STORAGE_KEY);
				localStorage.removeItem(USER_SET_WIDTH_STORAGE_KEY);
				localStorage.removeItem(SIZE_PRESET_STORAGE_KEY);
				localStorage.setItem(WIDTH_STORAGE_VERSION_KEY, WIDTH_STORAGE_VERSION);
				return null;
			}

			var storedPreset = getStoredPreset();
			if (storedPreset) {
				return getPresetWidth(storedPreset);
			}

			var stored = localStorage.getItem(WIDTH_STORAGE_KEY);
			if (!stored) {
				return null;
			}
			var parsed = parseInt(stored, 10);
			if (Number.isNaN(parsed)) {
				return null;
			}

			var isUserSet = localStorage.getItem(USER_SET_WIDTH_STORAGE_KEY) === "1";
			if (isUserSet) {
				return normalizeWidth(parsed);
			}

			// If width was not explicitly user-set, keep it at least the new default width.
			var migratedWidth = Math.max(DEFAULT_PANEL_WIDTH, parsed);
			persistWidth(migratedWidth, false);
			return normalizeWidth(migratedWidth);
		} catch (e) {
			return null;
		}
	}

	function persistWidth(width, isUserSet, preset) {
		try {
			localStorage.setItem(WIDTH_STORAGE_KEY, String(width));
			if (isUserSet) {
				localStorage.setItem(USER_SET_WIDTH_STORAGE_KEY, "1");
			} else {
				localStorage.removeItem(USER_SET_WIDTH_STORAGE_KEY);
			}
			if (preset && SIZE_PRESETS[preset]) {
				localStorage.setItem(SIZE_PRESET_STORAGE_KEY, preset);
			} else {
				localStorage.removeItem(SIZE_PRESET_STORAGE_KEY);
			}
			localStorage.setItem(WIDTH_STORAGE_VERSION_KEY, WIDTH_STORAGE_VERSION);
		} catch (e) {
			// Ignore quota/privacy errors and keep current width only.
		}
	}

	function applyPanelWidth(panel, width) {
		panel.style.width = normalizeWidth(width) + "px";
	}

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

	function ensureDom() {
		if (document.getElementById(ROOT_ID)) {
			return;
		}

		var root = document.createElement("div");
		root.id = ROOT_ID;

		var bubble = document.createElement("button");
		bubble.type = "button";
		bubble.id = BUBBLE_ID;
		bubble.setAttribute("aria-label", "Open AI assistant");
		bubble.setAttribute("title", "AI Assistant");
		bubble.innerHTML =
			'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
			'<path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.59-.34-1-.99-1-1.73a2 2 0 0 1 2-2M7.5 13A1.5 1.5 0 0 0 6 14.5 1.5 1.5 0 0 0 7.5 16a1.5 1.5 0 0 0 1.5-1.5A1.5 1.5 0 0 0 7.5 13m9 0a1.5 1.5 0 0 0-1.5 1.5 1.5 1.5 0 0 0 1.5 1.5 1.5 1.5 0 0 0 1.5-1.5 1.5 1.5 0 0 0-1.5-1.5M12 9a3 3 0 0 0-3 3h6a3 3 0 0 0-3-3"/>' +
			"</svg>";

		var overlay = document.createElement("div");
		overlay.id = "fac-ai-assistant-overlay";
		overlay.setAttribute("aria-hidden", "true");

		var panel = document.createElement("div");
		panel.id = PANEL_ID;
		panel.setAttribute("role", "dialog");
		panel.setAttribute("aria-modal", "true");
		panel.setAttribute("aria-label", "AI Assistant");

		var resizeHandle = document.createElement("div");
		resizeHandle.id = "fac-ai-assistant-resize-handle";
		resizeHandle.setAttribute("aria-hidden", "true");

		var iframe = document.createElement("iframe");
		iframe.id = "fac-ai-assistant-iframe";
		iframe.setAttribute("title", "AI Assistant");
		iframe.setAttribute("allow", "clipboard-write; microphone; camera");
		iframe.setAttribute("scrolling", "no");

		var toolbar = document.createElement("div");
		toolbar.id = "fac-ai-assistant-panel-toolbar";
		toolbar.className = "fac-ai-assistant-panel-toolbar";
		toolbar.setAttribute("role", "toolbar");
		toolbar.setAttribute("aria-label", "Panel size and close");

		var btnWider = document.createElement("button");
		btnWider.type = "button";
		btnWider.className = "fac-ai-assistant-toolbar-btn";
		btnWider.setAttribute("aria-label", "Widen panel");
		btnWider.setAttribute("title", "Widen panel");
		btnWider.innerHTML =
			'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">' +
			'<path d="M12 5v14M5 12h14"/>' +
			"</svg>";

		var btnNarrower = document.createElement("button");
		btnNarrower.type = "button";
		btnNarrower.className = "fac-ai-assistant-toolbar-btn";
		btnNarrower.setAttribute("aria-label", "Narrow panel");
		btnNarrower.setAttribute("title", "Narrow panel");
		btnNarrower.innerHTML =
			'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">' +
			'<path d="M5 12h14"/>' +
			"</svg>";

		var btnClose = document.createElement("button");
		btnClose.type = "button";
		btnClose.className = "fac-ai-assistant-toolbar-btn fac-ai-assistant-toolbar-btn-close";
		btnClose.setAttribute("aria-label", "Close AI assistant");
		btnClose.setAttribute("title", "Close");
		btnClose.innerHTML =
			'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">' +
			'<path d="M18 6L6 18M6 6l12 12"/>' +
			"</svg>";

		toolbar.appendChild(btnWider);
		toolbar.appendChild(btnNarrower);
		toolbar.appendChild(btnClose);

		panel.appendChild(resizeHandle);
		panel.appendChild(iframe);
		panel.appendChild(toolbar);

		root.appendChild(bubble);
		document.body.appendChild(overlay);
		document.body.appendChild(panel);
		document.body.appendChild(root);

		var initialWidth = getStoredWidth() || DEFAULT_PANEL_WIDTH;
		applyPanelWidth(panel, initialWidth);
		function onResizeWindow() {
			var storedPreset = getStoredPreset();
			if (storedPreset) {
				applyPanelWidth(panel, getPresetWidth(storedPreset));
				return;
			}
			var currentWidth = parseInt(panel.style.width || String(DEFAULT_PANEL_WIDTH), 10);
			if (Number.isNaN(currentWidth)) {
				currentWidth = DEFAULT_PANEL_WIDTH;
			}
			applyPanelWidth(panel, currentWidth);
		}

		window.addEventListener("resize", onResizeWindow);

		function setupPanelResizing() {
			var isResizing = false;
			var moveHandler;
			var upHandler;

			resizeHandle.addEventListener("mousedown", function (event) {
				event.preventDefault();
				isResizing = true;
				document.body.classList.add("fac-ai-assistant-resizing");

				moveHandler = function (moveEvent) {
					if (!isResizing) {
						return;
					}
					var nextWidth = normalizeWidth(window.innerWidth - moveEvent.clientX);
					applyPanelWidth(panel, nextWidth);
				};

				upHandler = function () {
					if (!isResizing) {
						return;
					}
					isResizing = false;
					document.body.classList.remove("fac-ai-assistant-resizing");
					document.removeEventListener("mousemove", moveHandler);
					document.removeEventListener("mouseup", upHandler);
					var savedWidth = parseInt(panel.style.width, 10);
					if (!Number.isNaN(savedWidth)) {
						persistWidth(savedWidth, true, null);
					}
				};

				document.addEventListener("mousemove", moveHandler);
				document.addEventListener("mouseup", upHandler);
			});

			resizeHandle.addEventListener("dblclick", function (event) {
				event.preventDefault();
				applyPanelWidth(panel, DEFAULT_PANEL_WIDTH);
				persistWidth(DEFAULT_PANEL_WIDTH, false, DEFAULT_PRESET);
			});
		}

		setupPanelResizing();

		function postHostContextToIframe(targetOrigin) {
			postEmbedFormContext(iframe, targetOrigin);
		}

		var contextRetryTimer = null;

		function stopContextRetry() {
			if (contextRetryTimer) {
				clearInterval(contextRetryTimer);
				contextRetryTimer = null;
			}
		}

		function startContextRetry() {
			stopContextRetry();
			var attempts = 0;
			var maxAttempts = 24;
			postHostContextToIframe();
			contextRetryTimer = setInterval(function () {
				if (!panel.classList.contains("fac-ai-visible")) {
					stopContextRetry();
					return;
				}
				postHostContextToIframe();
				attempts += 1;
				if (attempts >= maxAttempts) {
					stopContextRetry();
				}
			}, 500);
		}

		function setupHostContextSync() {
			if (setupHostContextSync._bound) {
				return;
			}
			setupHostContextSync._bound = true;

			window.addEventListener("message", function (event) {
				var data = event.data;
				if (!data || typeof data !== "object") {
					return;
				}
				if (data.type === "buildingai-form-context-ack") {
					stopContextRetry();
					return;
				}
				if (data.type !== EMBED_READY_MESSAGE) {
					return;
				}
				if (!panel.classList.contains("fac-ai-visible")) {
					return;
				}
				postHostContextToIframe(event.origin || "*");
				startContextRetry();
			});

			function bindRouteChangeListener() {
				if (bindRouteChangeListener._bound) {
					return;
				}
				if (
					typeof frappe === "undefined" ||
					!frappe.router ||
					typeof frappe.router.on !== "function"
				) {
					return;
				}
				bindRouteChangeListener._bound = true;
				frappe.router.on("change", function () {
					if (panel.classList.contains("fac-ai-visible")) {
						postHostContextToIframe();
					}
				});
			}

			if (typeof frappe !== "undefined" && typeof frappe.ready === "function") {
				frappe.ready(bindRouteChangeListener);
			} else {
				bindRouteChangeListener();
			}
		}

		setupHostContextSync();

		function openPanel() {
			var url = buildEmbedUrlWithContext();
			iframe.src = url;
			iframe.addEventListener(
				"load",
				function () {
					startContextRetry();
				},
				{ once: true }
			);
			overlay.classList.add("fac-ai-visible");
			panel.classList.add("fac-ai-visible");
			document.body.style.overflow = "hidden";
			startContextRetry();
		}

		function closePanel() {
			stopContextRetry();
			overlay.classList.remove("fac-ai-visible");
			panel.classList.remove("fac-ai-visible");
			document.body.style.overflow = "";
			iframe.removeAttribute("src");
			bubble.focus();
		}

		function getPanelWidthPx() {
			var w = parseInt(panel.style.width, 10);
			if (Number.isNaN(w)) {
				w = DEFAULT_PANEL_WIDTH;
			}
			return w;
		}

		function adjustPanelWidth(delta) {
			var next = normalizeWidth(getPanelWidthPx() + delta);
			applyPanelWidth(panel, next);
			persistWidth(next, true, null);
		}

		btnWider.addEventListener("click", function (e) {
			e.preventDefault();
			e.stopPropagation();
			adjustPanelWidth(PANEL_WIDTH_STEP);
		});

		btnNarrower.addEventListener("click", function (e) {
			e.preventDefault();
			e.stopPropagation();
			adjustPanelWidth(-PANEL_WIDTH_STEP);
		});

		btnClose.addEventListener("click", function (e) {
			e.preventDefault();
			e.stopPropagation();
			closePanel();
		});

		bubble.addEventListener("click", function (e) {
			e.preventDefault();
			openPanel();
		});
		overlay.addEventListener("click", closePanel);

		document.addEventListener("keydown", function (e) {
			if (e.key === "Escape" && panel.classList.contains("fac-ai-visible")) {
				closePanel();
			}
		});
	}

	function init() {
		if (!isLoggedInUser()) {
			return;
		}
		ensureDom();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
})();
