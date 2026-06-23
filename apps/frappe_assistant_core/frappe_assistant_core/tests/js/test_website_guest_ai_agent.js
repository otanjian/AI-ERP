const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const SCRIPT_PATH = path.resolve(
	__dirname,
	"../../public/js/website_guest_ai_agent.js"
);
const SCRIPT = fs.readFileSync(SCRIPT_PATH, "utf8");
const EXPECTED_AGENT_URL =
	"https://ai.bosofts.com/agents/3a6420a3-8bbe-40a1-8da2-4c6aad83b487/6d752020a22b48ad4a5b5b651cd48fa5181fee135776e9f2b20d4e0645f93d72";

function createElement(tagName) {
	const element = {
		tagName: tagName.toUpperCase(),
		children: [],
		attributes: {},
		className: "",
		id: "",
		style: {},
		_textContent: "",
		appendChild(child) {
			this.children.push(child);
			if (child.id) {
				this.ownerDocument.elementsById[child.id] = child;
			}
			return child;
		},
		addEventListener(type, handler) {
			this.listeners = this.listeners || {};
			this.listeners[type] = handler;
		},
		setAttribute(name, value) {
			this.attributes[name] = value;
		},
		getAttribute(name) {
			return this.attributes[name];
		},
		querySelector(selector) {
			return this.queryMap && this.queryMap[selector];
		},
		classList: {
			toggle() {},
			contains() {
				return false;
			},
		},
	};
	Object.defineProperty(element, "textContent", {
		get() {
			return this._textContent;
		},
		set(value) {
			this._textContent = value;
		},
	});
	Object.defineProperty(element, "innerHTML", {
		set() {
			const panel = createElement("div");
			const launcher = createElement("button");
			const close = createElement("button");
			const iframe = createElement("iframe");
			[panel, launcher, close, iframe].forEach((child) => {
				child.ownerDocument = element.ownerDocument;
			});
			element.queryMap = {
				".bosofts-ai-agent__panel": panel,
				".bosofts-ai-agent__launcher": launcher,
				".bosofts-ai-agent__close": close,
				".bosofts-ai-agent__frame": iframe,
			};
			element.children.push(panel, launcher);
		},
	});
	return element;
}

function runForPath(pathname) {
	const elementsById = {};
	const document = {
		readyState: "complete",
		elementsById,
		head: null,
		body: null,
		createElement(tagName) {
			const element = createElement(tagName);
			element.ownerDocument = document;
			return element;
		},
		getElementById(id) {
			return elementsById[id] || null;
		},
		addEventListener() {},
	};
	document.head = document.createElement("head");
	document.body = document.createElement("body");

	const context = {
		document,
		window: {
			location: { pathname },
		},
		frappe: {
			session: { user: "Guest" },
		},
	};
	vm.runInNewContext(SCRIPT, context);

	return document.getElementById("bosofts-ai-agent");
}

function iframeFor(root) {
	return root.querySelector(".bosofts-ai-agent__frame");
}

function launcherFor(root) {
	return root.querySelector(".bosofts-ai-agent__launcher");
}

const homeRoot = runForPath("/");
assert.strictEqual(homeRoot, null, "home page must not mount guest AI agent");

const loginRoot = runForPath("/login");
assert.strictEqual(loginRoot, null, "ERPNext login must not mount guest AI agent");

const erpRoot = runForPath("/erp");
assert.ok(erpRoot, "non-home website pages should mount guest AI agent");
launcherFor(erpRoot).listeners.click();
assert.strictEqual(
	iframeFor(erpRoot).src,
	EXPECTED_AGENT_URL,
	"guest AI agent should use the requested previous-version agent URL"
);
